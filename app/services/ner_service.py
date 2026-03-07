"""
NER Service using GLiNER for entity recognition
"""

from pathlib import Path
from typing import Any, Literal

import simplemma
import stanza
from gliner import GLiNER
from langdetect import LangDetectException, detect

from app.core.config import settings
from app.core.constants import RELATION_BETWEEN_DOCUMENT_AND_ENTITY
from app.core.logger import logger
from app.repositories.category_repository import CategoryRepository
from app.repositories.entity_repository import EntityRepository
from app.repositories.text_repository import TextRepository


class NERService:
    """Service for Named Entity Recognition using GLiNER"""

    def __init__(self):
        self.model: GLiNER | None = None
        self.nlp_en = None
        self.nlp_ru = None
        self._load_ner_model()
        self._load_stanza()

    def _load_ner_model(self):
        """Load GLiNER model from mounted volume"""
        try:
            model_path = Path(settings.gliner_model_path)
            logger.info(f"Loading GLiNER model from: {model_path}")

            if not model_path.exists():
                raise RuntimeError(
                    f"GLiNER model not found at {model_path}. "
                    f"Please run ./scripts/download_models.sh to download models."
                )

            self.model = GLiNER.from_pretrained(str(model_path))
            logger.info("GLiNER model loaded successfully")
        except Exception as e:
            logger.exception(f"Failed to load GLiNER model: {e}")
            raise

    def _load_stanza(self):
        """Load Stanza models from mounted volume"""
        try:
            stanza_dir = Path(settings.stanza_models_dir)
            logger.info(f"Loading Stanza models from: {stanza_dir}")

            en_model_path = stanza_dir / "en"
            ru_model_path = stanza_dir / "ru"

            if not en_model_path.exists():
                raise RuntimeError(
                    f"Stanza EN model not found at {en_model_path}. "
                    f"Please run ./scripts/download_models.sh to download models."
                )
            if not ru_model_path.exists():
                raise RuntimeError(
                    f"Stanza RU model not found at {ru_model_path}. "
                    f"Please run ./scripts/download_models.sh to download models."
                )

            self.nlp_en = stanza.Pipeline(
                "en", dir=str(stanza_dir), use_gpu=False, processors="tokenize,pos,mwt,lemma"
            )
            self.nlp_ru = stanza.Pipeline(
                "ru", dir=str(stanza_dir), use_gpu=False, processors="tokenize,pos,lemma"
            )
            logger.info("Stanza models loaded successfully")
        except Exception as e:
            logger.exception(f"Failed to load Stanza models: {e}")
            raise

    def get_nlp_pipeline(self, language: Literal["en", "ru"] = "en") -> stanza.Pipeline:
        if language == "en":
            return self.nlp_en
        elif language == "ru":
            return self.nlp_ru
        else:
            raise RuntimeError(f"Unsupported language: {language}")

    def predict_entities(
        self, text: str, labels: list[str] | None = None, threshold: float = 0.5
    ) -> list[dict[str, Any]]:
        """Predict entities in text using GLiNER"""
        if not self.model:
            raise RuntimeError("GLiNER model not loaded")

        if labels is None:
            from app.services.category_service import category_service

            labels = [category["c"]["name"] for category in category_service.list_categories()]

        if not labels:
            return []

        try:
            # Predict entities
            entities = self.model.predict_entities(text, labels, threshold=threshold)

            # Format results
            formatted_entities = []
            try:
                text_language = detect(text)
            except LangDetectException:
                # We couldn't determine language. Maybe text consists of just symbols
                text_language = "en"

            logger.info(f"> Language: {text_language}")
            for entity in entities:
                if text_language in ["en", "ru"]:
                    # Stanza lemmatization
                    nlp = self.get_nlp_pipeline(text_language)
                    doc = nlp(entity["text"])
                    lemmas = [word.lemma for sentence in doc.sentences for word in sentence.words]
                else:
                    # simplemma lemmatization for other languages
                    try:
                        lemmas = simplemma.text_lemmatizer(
                            entity["text"], lang=text_language, greedy=True
                        )
                    except ValueError:
                        # Fallback if language is not supported
                        lemmas = simplemma.text_lemmatizer(entity["text"], lang="en", greedy=True)

                normalized_text = " ".join(lemmas)

                formatted_entities.append(
                    {
                        "text": normalized_text,
                        "original_text": entity["text"],
                        "label": entity["label"],
                        "start": entity["start"],
                        "end": entity["end"],
                        "confidence": entity.get("score", 0.0),
                    }
                )

            logger.info(f"Detected {len(formatted_entities)} entities in text")
            return formatted_entities

        except Exception as e:
            logger.exception(f"Entity prediction failed: {e}")
            raise

    def parse_text(
        self,
        content: str,
        labels: list[str] | None = None,
        auto_create_entities: bool = True,
    ) -> dict[str, Any]:
        """Parse text and extract entities"""
        text_id = TextRepository.create(content)

        detected_entities = self.predict_entities(content, labels)

        processed_entities = []
        for entity_data in detected_entities:
            entity_name = entity_data["text"]
            entity_label = entity_data["label"]
            category = CategoryRepository.get_by_name(entity_label)
            if not category:
                # Category should exist - log warning and skip this entity
                logger.warning(
                    f"Category '{entity_label}' not found in graph. Skipping entity '{entity_name}'"
                )
                continue

            entity = EntityRepository.get_by_name(entity_name)
            if not entity and auto_create_entities:
                entity_id = EntityRepository.create(entity_name, category["c"]["id"])
                entity = EntityRepository.get_by_id(entity_id)

            # Add entity mention to text
            role = RELATION_BETWEEN_DOCUMENT_AND_ENTITY
            if entity:
                TextRepository.add_entity_mention(text_id, entity["e"]["id"], role)
                processed_entities.append(
                    {
                        "text": entity_name,
                        "label": entity_label,
                        "entity_id": entity["e"]["id"],
                        "role": role,
                        "confidence": entity_data["confidence"],
                    }
                )
            else:
                processed_entities.append(
                    {
                        "text": entity_name,
                        "label": entity_label,
                        "entity_id": None,
                        "role": role,
                        "confidence": entity_data["confidence"],
                    }
                )

        logger.info(f"Parsed text {text_id}: found {len(detected_entities)} entities")

        return {
            "text_id": text_id,
            "content": content,
            "entities": processed_entities,
        }


ner_service = NERService()
