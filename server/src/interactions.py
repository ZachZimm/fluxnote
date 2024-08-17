import os
import json
import server_info
from fastapi import WebSocket

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

async def summarize(websocket, lc_interface, file_path: str="sample_data/", file_index:str=None, help:bool=False) -> tuple[str, str]:
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
            return e, "summary error"
    for idea in summary.summary:
        summary_string += idea.idea + " \n"
    history = lc_interface.append_history(summary_string, history, is_human = False)
    print("Summary added to history.")
    if summary_string != "":
        return summary_string, "summary"
    else:
        return f"Error summarizing text. Summary: {summary_string}", "summary error"
    
async def wiki_search(websocket, lc_interface, wiki, query, help=False) -> tuple[str, str]:
    if help == True:
        return "Search the configured wiki for a query.", "help"
    query_results = wiki.search(query)
    max_results = 10
    wiki_results[lc_interface.userid] = []
    for i, result in enumerate(query_results):
        if i >= max_results:
            break
        wiki_results[lc_interface.userid].append(result)
    return json.dumps(wiki_results[lc_interface.userid]), "wiki search results"

async def get_wiki_results(websocket, lc_interface, wiki, help=False) -> tuple[str, str]:
    if help == True:
        return "Get the results of the last wiki search.", "help"
    global wiki_results
    try:
        _wiki_results = json.dumps(wiki_results[lc_interface.userid])
        return _wiki_results, "wiki search results"
    except KeyError:
        return "No search results. Enter 'wiki search' to search for a topic.", "wiki error"


async def wiki(websocket, lc_interface, wiki, query, should_save=False, return_full=False, help=False) -> tuple[dict, str]:
    if help == True:
        return "Get the content of a wiki page.", "help"
    if len(wiki_results[lc_interface.userid]) == 0:
        return "No search results. Enter 'wiki search' to search for a topic.", "wiki error"
    if not query.isdigit():
        return "Invalid input. Enter a number corresponding to a search result.", "wiki error"
    data = wiki.get_data(wiki_results[lc_interface.userid][int(query) - 1])
    return_object = {
        "title": data.title,
        "summary": data.summary,
    }
    if return_full:
        return_object["content"] = data.content
    return_object["message"] = f"Keys are {', '.join(return_object.keys())}"

    if should_save: # This should probably also save the summary in a separate file
        # This will also save to a database as soon as I integrate that 
        filepath = f"sample_data/{data.title.replace(' ', '_')}_wikidownload.txt"
        with open(filepath, "w") as file:
            file.write(data.content)
        # await send_ws_message(websocket, f"Content downloaded to {filepath}", mode="wiki")
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

# Dictionary to map function names to functions
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
    "wiki_search": wiki_search,
    "wiki": wiki,
    "wiki_results": get_wiki_results,
    "options": get_functions,
    "help": get_help,
    "list": get_available_files_str,
    "chat_history": get_chat_history,
    "clear_history": clear_chat_history,
    "quit": end_session,
}
# End that seperate file
