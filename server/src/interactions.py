# This file is a collection of functions that can be called by the websocket server to interact with the backend
# Each function should take in a websocket, a languagechain interface, and any arguments passed in by the user
# The function should return a tuple containing a message to be sent to the user and a status string
# The functions should be added to the available_request_functions dictionary at the bottom of the file to be accessible by the server

import os
import json
# from langchain_interface import langchain_interface
import server_info
from fastapi import WebSocket
from models.WikiData import WikiData



async def send_ws_message(websocket: WebSocket, message: str, mode: str = "default") -> None:
    await websocket.send_json({"message": message, "mode": mode})
async def chat(websocket, lc_interface, message, help=False, max_tokens = 600, temperature = 0.7) -> tuple[str, str]:
    if help == True:
        return "Chat with the LLM, using your configured character. Information from summaries can be loaded into history for the LLM's reference but the way of doing that is in development. Currently it involves creating a summary then initiating a chat session. Chat history is currently deleted on disconnection, though that is likely to change.", "help"
    user_message = message.strip()
    history = lc_interface.get_history()
    history = lc_interface.append_history(user_message, history, is_human = True)
    generator = await lc_interface.stream_langchain_chat_loop_async_generator(history, max_tokens, temperature)
    assistant_message = ""
    async for chunk in generator:
        assistant_message += chunk
        await send_ws_message(websocket, chunk, mode="chat streaming")

    history = lc_interface.append_history(assistant_message, history, is_human = False)
    return "<stream_finished>", "chat streaming finished"

def get_chat_history(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the chat history.", "help"
    history = lc_interface.get_history_str()
    return history, "status"

def clear_chat_history(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Clear the chat history.", "help"
    lc_interface.clear_history()
    return "Chat history cleared.", "status"

def add_chat_chatacter(websocket, lc_interface, character_name, character_prompt, help=False) -> tuple[str, str]:
    if help == True:
        return "Add a chat character to the configuration. Accepts `character_name` and `character_bio` strings", "help"
    lc_interface.add_chat_character(character_name, character_prompt)
    return f"Chat character added: {character_name}", "status"

def update_chat_character(websocket, lc_interface, character_name, character_prompt, help=False) -> tuple[str, str]:
    if help == True:
        return "Update a chat character in the configuration. Accepts `character_name` and `character_bio` strings", "help"
    lc_interface.update_chat_character(character_name, character_prompt)
    return f"Chat character updated: {character_name}", "status"

def get_chat_characters(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get a list of available chat characters.", "help"
    chat_characters: str = lc_interface.get_chat_characters_str()
    return chat_characters, "characters"

def remove_chat_character(websocket, lc_interface, character_name, help=False) -> tuple[str, str]:
    if help == True:
        return "Remove a chat character from the configuration.", "help"
    removed: bool = lc_interface.remove_chat_character(character_name)
    if removed:
        return f"Chat character removed: {character_name}", "status"
    else:
        return f"Chat character not removed: {character_name}", "status"

def get_configuration(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the configuration options.", "help"
    config_str = lc_interface.get_config_str()
    return config_str, "status"

def get_secret_configuration(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the secret configuration options.", "help"
    secret_config_str = lc_interface.get_secret_config_str()
    return secret_config_str, "status"

def set_secret_configuration(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Set the secret configuration options based on arguments passed in.", "help"
    # This function will be used to set secret config options that are passed in
    return f"Secret configuration set"

def get_configuration_options(websocket, lc_interface, field, help=False) -> tuple[str, str]:
    if help == True:
        return "Get all possible configuration fields.", "help"
    # Implement your get_configuration_options logic here
    return f"Configuration options for field: {field}"

def set_configuration(websocket, lc_interface, configuration_field=None, configuration_value=None, help=False) -> tuple[str, str]:
    if help == True:
        return "Set the configuration options based on arguments passed in. Use get_configuration_options to see the availible configuration fields.", "help"
    # This function is used to set config options that are passed in
    if configuration_field is not None and configuration_value is not None:
        _value = None
        if configuration_value.lower() == "true": # Change strings to bools
            _value = True
        # I may want to do something similar with ints and floats
        elif configuration_value.lower() == "false":
            _value = False
        else: _value = configuration_value

        lc_interface.update_config(configuration_field, _value)
        return f"Configured {configuration_field}: {str(_value)}", "status"
    return f"Configuration:\n{lc_interface.get_confg_str()}", "status"

# This function will soon be removed
async def summarize_file(websocket, lc_interface, file_path: str="sample_data/", file_index:str=None, help:bool=False) -> tuple[str, str]:
    if help == True:
        return "Summarize text from a specified file. Either a directory with an index or a full file path can be passed in. Relative paths are not allowed.", "help"
    available_files = []
    file_path = file_path.strip().replace("..", "")
    path_is_file: bool = os.path.isfile(file_path)

    # Build a file path for the file to be summarized
    if path_is_file:
        file_index = None
    elif file_index is not None and file_index.isdigit():
        available_files, _ = get_available_files(websocket, lc_interface, file_path)
        file_path = available_files[int(file_index) - 1]
        print(f"Available files: {available_files}")
    if file_index and not file_index.isdigit():
        return "File index must be a digit.", "summary error"

    # if not os.path.exists(file_path):
        # return "File not found.", "summary error"
    print(f"File path: {file_path}")
    text = ""
    try :
        with open(file_path, "r") as file:
            text = file.read()
    except:
        return "Error reading file.", "summary error"

    await send_ws_message(websocket, "Summarizing text from " + file_path.split('\\')[-1], mode="status")

    history = lc_interface.get_history()
    history, summary = await lc_interface.langchain_summarize_text_async(text, history)
    summary_string = ""
    try:
        summary_object = json.dumps(summary.model_dump()) # Verify that data conforms to expected format
        lc_interface.append_summary(summary) # Save to database
    except Exception as e:
        # Try again
        print("Error summarizing text, trying again.")
        print(e)
        history, summary = await lc_interface.langchain_summarize_text_async(text, history)
        try:
            summary_object = json.dumps(summary.model_dump()) # Verify that data conforms to expected format
            lc_interface.append_summary(summary) # Save to database
        except Exception as e:
            print("Failed to summarize text.")
            print(e)
            return str(e), "summary error"
    for idea in summary.summary:
        summary_string += idea.idea + " \n"
    history = lc_interface.append_history(summary_string, history, is_human = False)
    print("Summary added to history.")
    if summary_string != "":
        return summary_string, "summary"
    else:
        return f"Error summarizing text. Summary: {summary_string}", "summary error"

async def summarize(websocket, lc_interface, text, title="", help=False) -> tuple[str, str]:
    if help == True:
        return "Summarize text from a specified file. Either a directory with an index or a full file path can be passed in. Relative paths are not allowed.", "help"
    history = lc_interface.get_history()
    history, summary = await lc_interface.langchain_summarize_text_async(text, history, title=title)
    summary_string = ""
    try:
        summary_object = json.dumps(summary.model_dump()) # Verify that data conforms to expected format
        lc_interface.append_summary(summary) # Save to database
    except Exception as e:
        # Try again
        print("Error summarizing text, trying again.")
        print(e)
        history, summary = await lc_interface.langchain_summarize_text_async(text, history, title=title)
        try:
            summary_object = json.dumps(summary.model_dump()) # Verify that data conforms to expected format
            lc_interface.append_summary(summary) # Save to database
        except Exception as e:
            print("Failed to summarize text.")
            print(e)
            return str(e), "summary error"
    for idea in summary.summary:
        summary_string += idea.idea + " \n"
    history = lc_interface.append_history(summary_string, history, is_human = False)
    print("Summary added to history.")
    if summary_string != "":
        return summary_string, "summary"
    else:
        return f"Error summarizing text. Summary: {summary_string}", "summary error"

async def summarize_article(websocket, lc_interface, title, help=False) -> tuple[str,str]:
    if help == True:
        return "Summarize an article from the configured wiki.", "help"

    available_articles = lc_interface.get_list_of_articles()
    if title not in available_articles:
        return "Article not found.", "summary error"

    article: WikiData = lc_interface.get_article(title)
    summary_string, status = await summarize(websocket, lc_interface, text=article.content, title=title)
    return summary_string, status

def read_summary(websocket, lc_interface, title, help=False) -> tuple[str, str]:
    if help == True:
        return "Read a summary into chat history.", "help"
    summary = lc_interface.get_summary(title)

    summary_string = f"summary of document named {title}: \n"
    summary_json = summary.model_dump()
    i = 0
    for idea in summary_json["summary"]:
        i += 1
        summary_string += f"{str(i)}: {idea['idea']} \n"

    lc_interface.append_history(summary_string) # Save to history

    return f"Summary of {summary.title} added to history", "status"

def get_summary(websocket, lc_interface, title, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the last summary.", "help"
    summary = lc_interface.get_summary_str(title)
    return summary, "summary"

def get_summaries(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get all summaries.", "help"
    summaries = lc_interface.get_list_of_summaries_str()
    return summaries, "status"

def get_articles(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the list of articles.", "help"
    articles = lc_interface.get_list_of_articles_str()
    return articles, "status"

def get_article(websocket, lc_interface, title, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the article with the specified name.", "help"
    article = lc_interface.get_article_str(title)
    return article, "article"

def read_article(websocket, lc_interface, title, include_content=True, include_summary=False, help=False) -> tuple[str, str]:
    if help == True:
        return "Read an article's content into chat history. include_content and include_summary flags nidify behaviour", "help"

    article = lc_interface.get_article(title)
    new_content = ""
    if include_content:
        new_content += article.content
    if include_summary:
        new_content += article.summary
    lc_interface.append_history(new_content) # Save to history
    return f"Article {title} added to history", "status"

async def wiki_search(websocket, lc_interface, wiki, query, help=False) -> tuple[str, str]:
    if help == True:
        return "Search the configured wiki for a query.", "help"
    query_results = wiki.search(query)
    max_results = 10
    wiki.wiki_results = []
    for i, result in enumerate(query_results):
        if i >= max_results:
            break
        wiki.wiki_results.append(result)
    return json.dumps(wiki.wiki_results), "wiki search results"

async def get_wiki_results(websocket, lc_interface, wiki, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the results of the last wiki search.", "help"
    try:
        _wiki_results = json.dumps(wiki.wiki_results)
        return _wiki_results, "wiki search results"
    except KeyError:
        return "No search results. Enter 'wiki search' to search for a topic.", "wiki error"

# This is the function which actually retrieves the wiki data
async def wiki(websocket, lc_interface, wiki, query, should_save=False, return_full=False, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the content of a wiki page.", "help"
    if len(wiki.wiki_results) == 0:
        return "No search results. Enter 'wiki search' to search for a topic.", "wiki error"
    if not query.isdigit():
        return "Invalid input. Enter a number corresponding to a search result.", "wiki error"
    data: WikiData = wiki.get_data(wiki.wiki_results[int(query) - 1])
    return_object = {
        "title": data.title,
        "summary": data.summary,
    }
    if return_full:
        return_object["content"] = data.content
    return_object["message"] = f"Keys are {', '.join(return_object.keys())}"

    if should_save: # This should probably also save the summary in a separate file
        lc_interface.append_article(data) # Save to database

        # filepath = f"sample_data/{data.title.replace(' ', '_')}_wikidownload.txt"
        # with open(filepath, "w") as file:
        #     file.write(data.content)
    return json.dumps(return_object), "wiki"

def get_available_files_str(websocket, lc_interface, help=False) -> tuple[str, str]:
    available_files, status = get_available_files(websocket, lc_interface, help)
    if help == True:
        return available_files[0], status
    return json.dumps(available_files), "status"

def get_available_files(websocket, lc_interface, help = False) -> tuple[list, str]:
    # This will not be a list of files in a path in the future, but a database query that returns a list of files associated with a user and their ids
    # probably filterable as well
    if help == True:
        return ["Get a list of available text files in the path passed in."], "help"
    path = lc_interface.get_notes_dir()
    path = path.strip().replace("..", "") # Shouldn't be needed anymore
    files_in_dir = os.listdir(path) # Files in dirs will be replaced with a database query
    available_files = [f"{path}{file}" for file in files_in_dir if file.endswith(".txt")]
    return available_files, "status"

def get_server_status(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the server status.", "help"
    gpu_info: dict = server_info.get_gpu_info()
    cpu_info: dict = server_info.get_cpu_info()
    disk_info: dict = server_info.get_disk_info()

    return json.dumps({"gpu_info": gpu_info, "cpu_info": cpu_info, "disk_info": disk_info}), "status"

def get_functions(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get a list of available backend functions.", "help"
    return json.dumps(list(available_request_functions.keys())), "status"

def get_user_history(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the user's command history.", "help"
    return lc_interface.get_user_history_str(), "user_history status"

def clear_user_history(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Clear the user's command history.", "help"
    lc_interface.clear_user_history()
    return "User history cleared.", "user_history status"

def login(websocket, lc_interface, username, help=False) -> tuple[str, str]:
    #TODO this needs some kind of authentication
    if help == True:
        return "Login to the server.", "help"
    lc_interface.login(username)
    return f"Logged in as {username}.", "status"

def end_session(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "End the current session.", "help"
    # await websocket.close()
    return "Ending session.", "status"

def get_help(websocket, lc_interface, help=False) -> tuple[str, str]:
    help_message = "Available functions:\n"
    help_message += "use any command followed by 'help' to get more information on that command.\n"
    help_message += json.dumps(get_functions(websocket, lc_interface, help=True)[0])
    return help_message, "help"

async def test_verify_idea(websocket, lc_interface, help=False) -> tuple[str, str]:
    if help == True:
        return "Test the idea verification function.", "help"
    # This function will be used to test the idea verification function
    ex_summary = lc_interface.get_summary("xcode wiki")
    ex_idea = ex_summary.summary[0]
    ex_content = lc_interface.get_article("xcode wiki").content
    new_idea = await lc_interface.verify_idea(ex_idea, ex_content)
    return new_idea.model_dump(), "verified idea"

available_request_functions = {
    "login": login,
    "chat": chat,
    "add_chat_character": add_chat_chatacter,
    "get_chat_characters": get_chat_characters,
    "update_chat_character": update_chat_character,
    "remove_chat_character": remove_chat_character,
    "get_configuration": get_configuration,
    "get_configuration_options": get_configuration_options,
    "get_secret_configuration": get_secret_configuration,
    "get_server_status": get_server_status,
    "server_status": get_server_status,
    "set_secret_configuration": set_secret_configuration,
    "configure": set_configuration,
    "summarize": summarize,
    "summarize_article": summarize_article,
    "summarize_file": summarize_file,
    "get_summary": get_summary,
    "get_summaries": get_summaries,
    "read_summary": read_summary,
    "get_articles": get_articles,
    "get_article": get_article,
    "test_verify_idea": test_verify_idea,
    "read_article": read_article,
    "wiki_search": wiki_search,
    "wiki": wiki,
    "wiki_results": get_wiki_results,
    "options": get_functions,
    "help": get_help,
    "list": get_available_files_str,
    "chat_history": get_chat_history,
    "clear_history": clear_chat_history,
    "clear_user_history": clear_user_history,
    "user_history": get_user_history,
    "quit": end_session,
}
