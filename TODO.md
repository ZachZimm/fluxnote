- [x] Ensure that other model providers work (openai, deepseek)
    - I may want to abstract out the model from the langchain_interface
        - I am thinking of a Model object that takes a config obj and returns a model

- [x] Some kind of monitoring so that the client can tell if the server is busy
    - Should also start testing with multiple users
        - User string needs to be configurable first

- [x] Refactor api_server.py

- [x] Write a function to read existing documents into the chat history
    - similarly, the ability to read existing summaries, or ideas
        - perhaps those ideas could be fetched from the vector db an n would represent the breadth of the search
            - although for consistency we would want some way of finding the density of information on that topic stored in the summary - because it may not be uniform across topics.
            - So n shoud be `n = n * information_density`

- [x] Implement a vector embedding manager
    - This is so that we can use different LLM providers and have a compatible vector database

- [x] Save idea vectors to mongodb

- [x] Save wiki articles to mongodb
    - title, summary, full text, and retrieval date

- [x] Fully deprecate the usage of text files in the sample-data directory
    - What remains to be changed:
        - Where the string for creating summaries is read from
        - Save behaviour on wikipedia download 
    - Implement a new way to read text documents into the database using the existing method

- [x] Implement a routine to verify the quality of a summary
  - Not sure whether this run upon summary creation, or only when requested

- [x] Write a routine to check / rewrite individual ideas
    - This should give the LLM both the original document, as well as the idea
    - The LLM will be instructed to evaluate the idea without the context of the others and re-write the idea if it is not individually meaningful.
        - This may be a 2 step process where the first checks whether a re-write is nessecary and the second performs the rewrite
    - This seems like a very heavy compute task (lots of input processing of full documents)
        - This will ideally run in the background

- [ ] Add a reworked version of the "document-parser" character called "note-parser" or something
    - this system prompt will specify that the notes are created by a user and will be treated slightly differently
    - The associated routine should allow for some options (or just metadata somehow specified, possibly just as text in the note file). Most of this should be added to the doc parsing routine too.
        - These options will be used to guide the summary generation
        - not sure about the types for these options yet
        - opt: completeness
            - whether information should be filled in / added
        - opt: reliability
            - should the llm doubt the claims in the document or treat them in a particular way?
        - opt: context
            - additional context that should be taken into account when generating a summary of this note

- [x] Add a server-side command history
    - Clients should grab this on login and update it independently
    - Hopefully it will be simple enough to implement up-arrow behaviour

- [ ] Integrate a vector database and tagging system
    - This will mostly be used so for semantic search so that the user can dynamically create idea-spaces
        - This will allow for a system of choosing ideas based on 'tags'
            - these tags will need to be added to the Summary and Idea models
            - in the long term, these tags will be something that an LLM can determine (if that is the preference)
            - maintain a list of all of a user's tags
            - Not sure how this will mesh with other ideas of notes / news
                - Those may be tags in themselves but for news at least I feel that I need more than just a tag
                    - I feel like news in particular will need a date system, so a date range can easily be specified, or potentially even weighed into the importance of the ideas when they are eventually used
                - Things would likely have multiple tags anyways, so this might be fine
                    - tags could be like: "news, technology, hardware, GPU, NVIDIA"
                        - This would catch queries at many levels of specificity 
                            - would be a pain to do that manually, no doubt we will need an LLM routine for this, along with a model most likely

- [ ] FEATURE GOAL: Have a conversation with the LLM with user-specified context.
    - Everything above should be checked off before this is complete
    - Not sure how this context will be defined
        - It may just be a list of tags/categories at first

- [ ] Implement a graph database (if I need to!)
    - There will be at least 2 databases
        - Summary database
            - Nodes are summaries / condensations
            - Edges are the strengh of their connection
                - Not sure if embeddings will be sufficient here due to the potential length
        - Idea database
            - Nodes are ideas
            - Edges are the similarity of their embeddings
                - While implementing this seems pretty reasonable, I wonder how much compute it will involve to find all of those embedding similarities. The number of ideas in a knowledge base could grow rather large and this involves computing vector similarities for every single combination of ideas.
                - This may be more feasable on a per-document level, and new graphs could be created upon instruction, but not automatically.
                - Or, I may be overestimating the amount of compute involved in say 30,000 similarity computations (wild guess of a number). We're currently using 768 dimension embeddings. 758 x 30,000 = 23 M. Multiply that by the number of ideas in the summary (15-40) and that doesn't look so terrible. I am not sure if `embedding_size x num_embeddings` represents the computation time very well though.
                - Maybe this would be a good time to learn about using C / C++ in python. Very likely though, the most obvious way of doing it (numpy) will already drop into C / C++.

- [ ] Sync front-end user command history with back-end user command history
    - Implement up-arrow behaviour

- [ ] Use the LLM to 'highlight' important ideas in source documents
    - I'm not sure how this will be done
    - One option would be to simply use markdown or some similar approach.
    - We could also instruct the llm to use an HTML-like tag. `<hilite> </hilite>` or something

- [ ] Usefully render that highlighted information in a GUI front end.
    - This seems like a novel feature to me, but I haven't looked for it either.
        - Could be legitimately useful too, for someone with too many low-priority documents
            - or someone with a lot of faith in their LLM choice

- [ ] Look into using to LLM to generate second-order ideas
  - This would be a very interesting feature if it pans out
  - The LLM would be given a list of ideas and would be asked a list of new ideas using those as a starting point

- [ ] Given a working knowledge base, use the LLM to suggest areas where information density seems to be low / lacking
    - This seems like it will be a real test of the smaller models
    - Hopefully it isn't out of reach of the larger models

- [ ] Design an interesting way of displaying data in a GUI
  - Some way of meaningfully represetning the potentially representing the many ideas and summaries without overwhelming the user
  - This will likely involve some kind of graph
  - Should allow the user some kind of discoverability too

- [ ] Implement a way for users to choose which model to use for which task
  - OpenAI / Deepseek can summarize while the local model can chat
  - one option:
  - Essentaily each task should have a priority level, which is associated with a model
    - based on user configuration
    - Scores of 1-10
      - If there is only one model specified, it will be used for all tasks
      - If there are multiple models, they will be distributed across the score range according to how the user ranks them
        - If there are 2 models, anything 1-5 will use the first model, and 6-10 will use the second model
        - If there are 3 models, 1-3 will use the first, 4-6 will use the second, and 7-10 will use the third
        - etc..
  - Another option, as there are only 2 tasks and wer'e only looking at adding a couple more
    - The user can specify which model to use for each task
    - If user doesn't specify, the cheapest model will be used

- [ ] Listen to the male voice options and determine which are good

- [ ] PDF parsing routine
    - Just an extension of the document / note parsing routines that is PDF compatible
    - OCR may be nessecary for some PDFs, and when it is recognition will probably be bad. At the very least the user should be warned.

- [ ] Implement a server-side routine to fetch news from specified feeds
    - this should be easily disabled / enabled with a bool in the config file
    - Server-side because multiple users may want the same news sources and this is likely to take the most disk space already as will work automatically in the background.
    - The list of feeds can be updated by authorized users
    - Each feed will have its own critera for what is relevant (as I noticed there can be a lot of junk in some news RSS feeds, or financial feeds will anncounce earnings for EVERY company they can, which we may not be interested in)
    - The news database should probably not be replicated for each user, but should be treated very similarly to notes or other documents.
    - Automatically determine whether this particular piece of news is valuable / satisfies criteria that has been configured,
        - This will most likely be with the LLM. Feed it the critera, as well as the news item and let it decide.
    - If the news item is relevant, then automatically summarize it, categorize it in the database, and create vector relationships
    - News items may need their own model, as a timestamp is important so that the LLM can easily be told X happened before Y.

- [ ] Implement a server-side audio-to-text component
    - This enables using source materials like online lectures, youtube videos, and podcasts
    - This will involve implementing a good mechanisim for loading the audio, whether from a file, url, RSS (?), or otherwise.
    - This should be optional, as it would likely involve running Whisper, which can use a few GB of vram when undistilled and using the large variant.
        - The model / provider will be configurable though. This may be a seperate server / microservice
    - This could also be used as a TTS provider for clients, assuming it is enabled on the server
    - Not yet sure about whether to add streaming capability.

- [ ] Implement a historical record, both going forward and backward.
    - This seems like a hugely ambitious idea in concept, but somewhat less so in terms of implementation
        - MongoDB may prove to be an issue for this, as a 'historical record' could get pretty big.
            - Consider trying to build a comprehensive knowledge base of events worldwide in the single year of 1848. The list of facts would be immense, as there are books upon books of recorded information about that single year.
        - A complete implementation should somehow take account of indivdual years' events, people and their doings, as well as a less date-dependant notion of events to provide further context to recorded facts.
            - This introduces a serious and undeniable element of subjectivity
                - Not nessicarily an issue but it must be adknowledged
            - The purpose of this is to prevent the LLM from having to infer at inference time more than is nessecary.
                - This should help us avoid hallucinations and some anachronisims.

- [ ] Implement document creation based on web research.
    - This will most likely involve the use of an API for good results.
        - There are API providers that offer search results catered for LLMs, as well as some more generic-use ones.
    - We could probably build a simple version that does not use any external services too

- [ ] Implement an alternative TTS option
    - the `edge_tts` package makes an API request to a Bing url. Their TTS processing is really good, fast, and free. Those 3 things don't usually go together so once they realize people have reverse engineered their API and they also start caring about how much that compute costs they might restrict it.
    - There are a number of other TTS options, both paid and locally hostable
        -Paid
            - OpenAI
            - ElevenLabs
            - Coqi XTTS
            - probably many more
        - Hostable
            - OS Native solutions
                - maybe the next macOS will change this but based on my testing the accessible macOS speech API produced pretty terribe (outdated) TTS. The OS does have good TTS though if you do it as an end user. There may be a newer API / command for macOS TTS
            - Coqi XTTS
                - Liscence forbids commercial use, although as a fully self hosted option it's pretty good
            - MARS TTS
                - The promo video was impressive but the huggingface spaces demo I tried was not. It may still be worth looking into though.

- [ ] Implement an Image to Text routine
    - Like the other ML routines, this will have multiple providers
        - OpenAI package already supports this
        - Self hosting could be a challenge, I have not really tried local Image2text
    - So that images (charts and otherwise) can be used as information for our knowledge base
    - Save some metadata as well, at least a title. This can be LLM-suggested
    - Option for user-specified context while parsing
        - this would help with ambiguity, and would

- [ ] Powerpoint to text
    - This may be a combination of parsing visible text from the slides, as well as using Image2Text
    - Powerpoints are often designed such that there only small, incremental changes between slides (one new bullet point at a time) and this is not ideal for parsing. That will have to be addressed somehow.
        - diffs?

- [ ] Server-side text to speech
    - this is pretty low priority but it would be useful for the creation of clients.
    - this would dramatically raise bandwith usage
        - possibly storage as well
    - this could enable the use of the siri voice everywhere, provided a mac is running the server, or a serverlet for this purpose
        - could possibly be done in a macOS VM as well.
