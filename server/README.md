## Fluxnote reference server implementation
The `fluxnote` server does not directly interact with LLM models, instead that is offloaded to another provider of the user's choice. 

## Setup
Make sure you have access to a supported LLM provider (see below under requirements)

`python -m venv venv`
`pip install -r requirements.txt`
`chmod +x start_python_server.sh`
`./start_python_server.sh`

## Requirements
    - Some supported LLM provider
        - OpenAI api key
        - Claude api key
        - Grok api key
        - Deepseek api key
        - Ollama server
        - Self hosted OpenAI api compatible server
    - MongoDB database connection string
        - Other databases will be supported in the future