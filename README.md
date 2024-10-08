# `fluxnote`
### A new, idea-centric approach to a note taking application backend.

## Overview
`fluxnote` is an LLM-enhanced notes backend which aims to improve the usefulness of notes or other text-based knowledge in a variety of ways. The novelty of `fluxnote` lies in using the LLM to break written knowledge into its component ideas which are used to build a knowledge base. `fluxnote` also aims to provide novel ways of promoting deep understanding of the ideas in the knowledge base by using the LLM to generate questions, contradictions, alternatives to existing ideas and routes for further exploration.

## Development Plan

### AI Integration
- **LLM Integration**
  - Selection and integration of a configurable LLM (e.g., GPT-3)
  - Development of API endpoints for idea extreaction and summarization of source text 

- **API Development**
  - Creation of semi-stateless Websocket API for note management and AI interactions
  - Implementation of authentication and user configuration endpoints
  

### Backend Development
##### Likely to be deveoped alongside the 'basic features'
- **Database Setup**
  - Configuration of MongoDB (if that is what I decide to use)
  - Design of database schemas for notes, metadata, and knowledge graphs

  **(progress is currently about here)**

- **AI-Native Knowledge Base**
  - Setup and configuration of Langchain for dynamic knowledge graph creation
  - Implementation of an embedding store for efficient idea representation and linking

### Basic Features
- **Note Management**
  - Advanced CRUD operations with AI-enhanced note structuring and linking
  - Implementation of a semantic search functionality for deep note exploration

- **Socratic Functions**
  - Integration of LLM-driven Socratic questioning and contradiction generation
  - Features for identifying and suggesting alternatives to existing note content

### AI Assistant Features
- **Custom Training Data Preparation**
  - Automated collection and preprocessing of user note data for model training
    - precicely what training data might be used, I am not sure
    - post-training may not be nessecary
  - Dynamic dataset creation based on user-defined importance and relevance
      - mixed category 'sort by' and more

### User Feedback and Testing
- **Internal Testing**
  - Development of comprehensive test cases covering core and AI functionalities
  - Rigorous manual testing of AI-driven features for accuracy and relevance

- **External Testing**
  - Find other people who want to use this and gather their feedback

## Important notes:
- This repository has further `README.md` files under the subdirectories `server/` `frontend/` and `frontend/python-cli/`
- This project is pretty far from what it sets out to do, the current implementation is rather bare bones
- The default configuration expects an openai compatible server (something like lm_studio or oobabooga/text-generation-webui. There are many options.) to be running on `http://localhost:5000/v1`
  - There will be more LLM provider options in the future
- To simply use the OpenAI API instead, put your OpenAI API key in `secret_config.json` and set `use_openai` to `true` in `config.json` under `server/`.

## Philosophy
When trying to use and gain advantage from note taking in the past, I have always struggled with the disconnect of the rigid separation and hierarchy of ideas on the page from the ultimate goal of an intricate and deep understanding of the interrelation of ideas. As such I have often opted not to take any notes at all as I have become accustomed to learning by listening.

While that has not been an issue in itself, I feel that there is great benefit to be derrived by writing. The goal of `fluxnote` then, is to remove the friction from the note taking process by improving the individual and combined usability of user-written notes. Further, `fluxnote` aims to ensure that every note has meaning, and will allow users to use new tools to get more out of their notes than they put in.

`fluxnote` generates signal in the note knowledge base in three main ways. The first is with innovative and deep LLM integration. The LLM integration is multi-layered and configurable at every level. The LLM integration will aim to expand on well-understood topics in real time, as well as suggest questions for a reliable source (whether for web research or an event the user is attending, such as a lecture or meeting). The LLM is also used to make inferences and draw connections which are not already made clear in the exiting contents of the notes. 

The goal is not to use the LLM to generate (/hallucinate) information about a topic (although that is an optional feature). Instead it is used to enhance 'resolution' of the ideas that the user's notes are meant to represent. 

Circling back to the friction I have encountered with my own notes in the past, I found that I would rarely gain much by reading my notes. This was often because my notes were a low-resolution representation of what they were meant to tell me. 

The second way that `fluxnote` improves the note taking process is by drawing connections between notes themselves, and shifting the mental model away from notes as such and towards one of ideas. `fluxnote` aims to create a modern alternative to the notebook model. Notes themselves are a fairly outdated concept and it's clear that an alternative is ripe to be developed. Instead of thinking of notes as documents which can be referenced as a whole (as in sheets of paper, or document files), we should be thinking of the ideas those documents relay. Ideas, unlike documents, are flexible. Ideas can be linked 

The third way `fluxnote` improves the resolution of existing ideas is by 'playing Socrates'. When used, these functions use the LLM to generate ideas that serve as contradiction, look for flaws/contradictions in existing notes, and suggest alternatives.

Additionally, the LLM can be used to chat with an AI that understands your notes. Users can simply select the tags/categories they want the LLM to be informed about and chat.

Every feature in `fluxnote` is user configurable and is either optional or easily disabled.

Additionally, the LLM used as well as the database can easily be switched to a user-provided configuration. In the case of the LLM that can be a production api (such as openai) or local service (ollama).

Philosophical inspirations:
Heraclitus, Socrates, Plato, Aristotle



