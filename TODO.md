- [ ] Ensure that other model providers work (openai, deepseek)
    - I may want to abstract out the model from the langchain_interface
        - I am thinking of a Model object that takes a config obj and returns a model

- [ ] Some kind of monitoring so that the client can tell if the server is busy
    - Should also start testing with multiple users
        - User string needs to be configurable first
- [ ] Refactor api_server.py
- [ ] Save idea vectors to mongodb
- [ ] Write a routine to check / rewrite individual ideas
    - This should give the LLM both the original document, as well as the idea
    - The LLM will be instructed to evaluate the idea without the context of the others and re-write the idea if it is not individually meaningful.
        - This may be a 2 step process where the first checks whether a re-write is nessecary and the second performs the rewrite
    - This seems like a very heavy compute task (lots of input processing of full documents)
        - This will ideally run in the background

- [ ] Implement a smart model / cheap model dichotomy which allows the user to specify a model for a task

- [ ] Implement a vector database
