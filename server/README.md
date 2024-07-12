## Fluxnote reference server implementation
The `fluxnote` server does not directly interact with LLM models, instead that is offloaded to another provider of the user's choice. 

## TODO
- get embeddings and implement a vector store
- implement database storage for text files
    - decide how to relate that with the vector store
    - some kind of graph/vector native db could be interesting
- write some tests
- switch websocket inputs to json format
    - account for users
        - implement some sort of auth (API keys at least)
    - a better function calling system
        - {"function": "summarize", {"args": "path/to.txt"}}
        - flag for REPL mode vs attempt to fully execute instruction
    
- consider rewriting the string processing util in a faster language
    - may not be 100% nessecary as these strings aren't supposed to be huge
    - call out to C/C++?
    - go?
- start to save the generated summaries
- generate summaries of different resolutions by giving the small idea + full article
    - possibly use extra context too
- test a knowledgebase generation function
    - have LLM come up with a list of specific topics based on a prompt
    - use the wiki integration to get info on those specific topics
    - create a multi-layered knowledge base which can be used for RAG
        - 'high detail', 'summary', 'broad idea'    
        - try to draw connections between ideas (and possibly topics)
            - would be nice to use a multi-dimensional graph for this

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