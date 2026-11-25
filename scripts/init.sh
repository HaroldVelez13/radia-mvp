#!/bin/bash
echo "RADIA init"
cp .env.example .env
docker compose up -d ollama
echo "Esperando Ollama..."
sleep 5
docker exec radia-ollama ollama pull qwen3:8b || echo "Ollama no listo, corre manualmente: docker exec radia-ollama ollama pull qwen3:8b"
docker compose up --build
