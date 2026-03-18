# Project Foundations

## Project name
social-chatbot-core

## Initial stack
- Python
- venv
- requirements.txt
- Git + GitHub
- terminal interface
- .env configuration
- mock response provider

## Not included yet
- FastAPI
- SQLite
- Instagram integration
- real LLM provider
- Docker
- deployment

## Minimal architecture
- LocalChannel: handles local input/output
- ChatOrchestrator: coordinates message flow
- ResponseEngine: generates responses

## Minimal flow
User -> LocalChannel -> ChatOrchestrator -> ResponseEngine -> response