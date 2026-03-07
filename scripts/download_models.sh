#!/bin/bash

# *********************************************************************
# ATTENTION (is all you need): this file is (almost) fully AI-generated
# *********************************************************************

# Model Download Script for NER System
# This script downloads all required models (GLiNER, Stanza, and LLM) to the ./models directory

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color


# Print colored message
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

if [ -f .env ]; then
    # shellcheck source=/dev/null
    source .env
else
    print_error ".env file not found! Please, run \`cp .env.example .env\`"
    exit 1
fi

# Default values
GLINER_MODEL="${GLINER_MODEL:-urchade/gliner_medium-v2.1}"
LLM_MODEL="${LLM_MODEL:-Qwen/Qwen3-1.7B-Instruct-GGUF}"
LLM_FILE="${LLM_FILE:-Qwen3-1.7B-Instruct-Q8_0.gguf}"
MODELS_DIR="./models"
LLM_MODEL_DOWNLOAD_PATH="${MODELS_DIR}/${LLM_MODEL}"
GLINER_DIR="${MODELS_DIR}/gliner"
STANZA_DIR="${MODELS_DIR}/stanza"

# Check if hf is installed
check_hf_cli() {
    if ! command -v hf &> /dev/null; then
        print_error "hf CLI is not installed"
        echo "Please install it with: pip install huggingface-hub"
        exit 1
    fi
    print_info "hf CLI found"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_info "Python 3 found"
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."
    mkdir -p "${GLINER_DIR}"
    mkdir -p "${STANZA_DIR}/en"
    mkdir -p "${STANZA_DIR}/ru"
    mkdir -p "${LLM_MODEL_DOWNLOAD_PATH}"
    print_info "Directory structure created"
}

# Download GLiNER model
download_gliner_model() {
    print_info "Downloading GLiNER model: ${GLINER_MODEL}"

    # Check if model already exists
    if [ -f "${GLINER_DIR}/pytorch_model.bin" ] || [ -f "${GLINER_DIR}/model.safetensors" ]; then
        print_warning "GLiNER model already exists in ${GLINER_DIR}"
        read -p "Do you want to re-download? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping GLiNER model download"
            return
        fi
        print_info "Re-downloading GLiNER model..."
    fi

    # Download using hf CLI
    hf download "${GLINER_MODEL}" --local-dir "${GLINER_DIR}"

    # Verify download
    if [ -d "${GLINER_DIR}" ] && [ "$(ls -A ${GLINER_DIR})" ]; then
        print_info "GLiNER model downloaded successfully to ${GLINER_DIR}"
    else
        print_error "GLiNER model download failed"
        exit 1
    fi
}

# Download Stanza models
download_stanza_models() {
    print_info "Downloading Stanza models..."

    # Create a temporary Python script to download Stanza models
    cat > /tmp/download_stanza.py << 'EOF'
import stanza
import os
from pathlib import Path

def download_stanza_model(lang, models_dir):
    """Download Stanza model for a specific language"""
    print(f"Downloading Stanza model for language: {lang}")

    # Set STANZA_RESOURCES_DIR to our custom directory
    os.environ['STANZA_RESOURCES_DIR'] = models_dir

    # Download the model
    stanza.download(lang, model_dir=models_dir)

    # Verify download
    lang_dir = Path(models_dir) / lang
    if lang_dir.exists() and any(lang_dir.iterdir()):
        print(f"Stanza {lang} model downloaded successfully to {lang_dir}")
    else:
        raise Exception(f"Stanza {lang} model download failed")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python download_stanza.py <lang> <models_dir>")
        sys.exit(1)

    lang = sys.argv[1]
    models_dir = sys.argv[2]

    try:
        download_stanza_model(lang, models_dir)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
EOF

    # Download English model
    print_info "Downloading Stanza English model..."
    python3 /tmp/download_stanza.py "en" "${STANZA_DIR}"

    # Download Russian model
    print_info "Downloading Stanza Russian model..."
    python3 /tmp/download_stanza.py "ru" "${STANZA_DIR}"

    # Clean up temporary script
    rm -f /tmp/download_stanza.py

    print_info "Stanza models downloaded successfully"
}

# Download LLM model
download_llm_model() {
    print_info "Downloading LLM model: ${LLM_MODEL}"
    print_info "File: ${LLM_FILE}"

    # Check if model already exists
    if [ -f "${LLM_MODEL_DOWNLOAD_PATH}/${LLM_FILE}" ]; then
        print_warning "LLM model already exists in ${LLM_MODEL_DOWNLOAD_PATH}"
        read -p "Do you want to re-download? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping LLM model download"
            return
        fi
        print_info "Re-downloading LLM model..."
    fi

    # Download using hf CLI
    hf download "${LLM_MODEL}" "${LLM_FILE}" --local-dir "${LLM_MODEL_DOWNLOAD_PATH}"

    # Verify download
    if [ -f "${LLM_MODEL_DOWNLOAD_PATH}/${LLM_FILE}" ]; then
        print_info "LLM model downloaded successfully to ${LLM_MODEL_DOWNLOAD_PATH}"
    else
        print_error "LLM model download failed"
        exit 1
    fi
}

# Verify all downloads
verify_downloads() {
    print_info "Verifying downloads..."

    local all_good=true

    # Check GLiNER model
    if [ -d "${GLINER_DIR}" ] && [ "$(ls -A ${GLINER_DIR})" ]; then
        print_info "✓ GLiNER model verified"
    else
        print_error "✗ GLiNER model not found"
        all_good=false
    fi

    # Check Stanza English model
    if [ -d "${STANZA_DIR}/en" ] && [ "$(ls -A ${STANZA_DIR}/en)" ]; then
        print_info "✓ Stanza English model verified"
    else
        print_error "✗ Stanza English model not found"
        all_good=false
    fi

    # Check Stanza Russian model
    if [ -d "${STANZA_DIR}/ru" ] && [ "$(ls -A ${STANZA_DIR}/ru)" ]; then
        print_info "✓ Stanza Russian model verified"
    else
        print_error "✗ Stanza Russian model not found"
        all_good=false
    fi

    # Check LLM model
    if [ -f "${LLM_MODEL_DOWNLOAD_PATH}/${LLM_FILE}" ]; then
        print_info "✓ LLM model verified"
    else
        print_error "✗ LLM model not found"
        all_good=false
    fi

    if [ "$all_good" = true ]; then
        print_info "All models verified successfully!"
        return 0
    else
        print_error "Some models are missing or incomplete"
        return 1
    fi
}

# Main execution
main() {
    print_info "Starting model download process..."
    print_info "Models directory: ${MODELS_DIR}"
    print_info "GLiNER model: ${GLINER_MODEL}"
    print_info "LLM model: ${LLM_MODEL}"
    print_info "LLM file: ${LLM_FILE}"
    echo ""

    # Check prerequisites
    check_python
    check_hf_cli
    echo ""

    # Create directories
    create_directories
    echo ""

    # Download models
    download_gliner_model
    echo ""
    download_stanza_models
    echo ""
    download_llm_model
    echo ""

    # Verify downloads
    if verify_downloads; then
        echo ""
        print_info "=========================================="
        print_info "Model download completed successfully!"
        print_info "=========================================="
        echo ""
        print_info "You can now start the application with:"
        print_info "  docker compose up --build -d --wait"
        echo ""
    else
        print_error "Model download verification failed"
        exit 1
    fi
}

# Run main function
main
