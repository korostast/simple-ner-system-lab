# NER System - Named Entity Recognition and Management System

A simple Named Entity Recognition (NER) system built with GLiNER, Neo4j graph database, and LLM API integration deployed via llama.cpp for intelligent entity management and knowledge extraction.

## Pre-requisites

* Python 3.10+
* Docker and docker compose

## Quick Start

1. Configure environment variables:
    ```bash
    cp .env.example .env
    # If you like, you can edit .env with your configuration. But you can just use defaults
    # There is also password for Neo4j database if you are interested in Neo4j browser tool
    ```

2. Pre-download all the necessary models (may take several gigabytes of memory):
    ```bash
    docker compose --profile downloader run --build --rm model-downloader
    # Creates ./models directory automatically
    ```
3. Start the system:
    ```bash
    docker compose up --build -d --wait
    # May take some time to build from sources and deploy until healthcheck if success
    ```

    3.1. To view logs:
      ```bash
      docker compose logs -f ner-app
      ```

    3.2. To stop system and remove volumes (Neo4j data):
      ```bash
      docker compose down -v
      ```

Services:
* Web can be accessed on http://localhost:8011 (by default);
* llama.cpp web - http://localhost:8075 (by default). You can chat with LLM here;
* Neo4j - http://localhost:8474/browser (by default). Use credentials from `.env` file to pass authentication:
  * URL: `neo4j://localhost:8687`
  * Database field empty
  * Username/password in `.env`

Application implement OpenAPI interface. You can access documentation on http://localhost:8011/docs

## License

This project is provided as-is for educational and research purposes.
