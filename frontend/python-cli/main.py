import asyncio
import websockets
import json
import aioconsole
import tts

config_dir = "config.json"
config = json.load(open(config_dir))

def print_summary(summary):
    i = 0
    num_ideas = len(summary)
    print(f"Summary has {num_ideas} ideas.")

    for idea in range(num_ideas):
        print(f"{idea}: {summary[idea]['idea']}")
        i += 1

streaming_message = ""
tts_generation_queue = asyncio.Queue()
tts_playback_queue = asyncio.Queue()
num_sentences_per_generation = 2
num_sentences_this_message = 0

def queue_audio(config, message):
    if config["speech_enabled"]:
        tts_generation_queue.put_nowait(message)

def is_full_sentence(message):
    message = message.strip().replace("\n", " ").replace("...", ",")

    if len(message) < 3: return False
    if message.endswith("..."): return True
    if message.endswith("."): return True
    if message.endswith("!"): return True
    if message.endswith("?"): return True
    return False

def fix_prefixes(message: str) -> str:
    message = message.replace("Dr.", "Doctor")
    message = message.replace("Mr.", "Mister")
    message = message.replace("Mrs.", "Misses")
    message = message.replace("Ms.", "Miss")
    return message
    

def print_json_message(json_str) -> None:
    global streaming_message
    dict_obj = json.loads(json_str)
    if dict_obj["mode"] == "chat":
        print(f"Chat: {dict_obj['message']}")
        return

    elif 'streaming' in dict_obj["mode"]:
        if 'finished' in dict_obj["mode"]:
            if len(streaming_message) > 0:
                queue_audio(config, streaming_message)
            print("\n\n> ", end="")
            streaming_message = ""
            return

        streaming_message += dict_obj["message"]
        streaming_message = fix_prefixes(streaming_message)
        print(dict_obj["message"], end="", flush=True)
        if is_full_sentence(streaming_message):
            global num_sentences_this_message
            num_sentences_this_message += 1

            if num_sentences_this_message >= num_sentences_per_generation:
                num_sentences_this_message = 0
                queue_audio(config, streaming_message)
                streaming_message = ""
        return

    elif "summary" in dict_obj["mode"]:
        if "error" in dict_obj["mode"]:
            print(f"Error: {dict_obj['message']}")
            return
        if '{' == dict_obj["message"][0]:
            dict_obj = json.loads(dict_obj["message"])
            print_summary(dict_obj["summary"])
            return
    elif "wiki search results" in dict_obj["mode"]:
        list_obj = json.loads(dict_obj["message"])
        for i in range(len(list_obj)):
            print(f"{i+1}: {list_obj[i]}")
    elif "wiki" == dict_obj["mode"]:
        wiki_obj = json.loads(dict_obj["message"])
        wiki_keys = wiki_obj.keys()
        if 'title' in wiki_keys:
            print(wiki_obj["title"])
        if 'summary' in wiki_keys:
            print(wiki_obj["summary"])
        if 'content' in wiki_keys:
            print(wiki_obj["content"])
    else:
        print(f"Mode: {dict_obj['mode']}")
        try:
            print(json.dumps(dict_obj["message"], indent=4).replace("\\"*3, "\\"))
        except:
            print("Error: Could not parse json.")
            print(dict_obj)
            print(dict_obj["message"])
        return


async def tts_generator():
    while True:
        message = await tts_generation_queue.get()
        output_name = await tts.aspeak_chunk(message)
        tts_playback_queue.put_nowait(output_name)
        tts_generation_queue.task_done()

async def tts_player():
    while True:
        path = await tts_playback_queue.get()
        await tts.aplay_audio(path)
        tts_playback_queue.task_done()

async def listen_for_messages(websocket) -> None:
    while True:
        message = await websocket.recv()
        print_json_message(message)

async def close_and_exit(websocket) -> None:
    await websocket.close()

# This function is used to send messages to the server
# I think it should be in a seperate file and further refactored
async def send_messages(websocket) -> None: # consider checking for success and returning a boolean
    while True:
        message_object = {}
        should_continue = False
        print("Enter a command: ")
        user_command = await aioconsole.ainput()
        print()
        user_command = user_command.lower().strip()
        if user_command == "quit":
            await close_and_exit(websocket)

        elif user_command == "chat" or ('chat' in user_command and len(user_command.split(" ")) == 2 and user_command.split(" ")[1].isdigit()):
            # Streaming chat loop
            while True:
                message = await aioconsole.ainput()
                if message == "exit":
                    should_continue = True
                    break
                elif message == "quit":
                    await close_and_exit(websocket)
                print()
                # some examples:
                """
                {"func": "chat", "message": "Hello"}
                {"func": "get_current_configuration"}
                {"func": "get_configuration_options", "field": "character"}
                {"func": "configure", "selected_character": "Sherlock-Holmes"}
                {"func": "summmarize", "file_path": "path/to/file"}
                {"func": "summmarize", "file_index": "1"}
                {"func": "options", "message": "options"}
                {"func": "quit"}
                """
                user_command_list = user_command.split(" ")
                if len(user_command_list) == 2:
                    if user_command_list[1].isdigit():
                        message_object['max_tokens'] = int(user_command_list[1])
                message_object['func'] = "chat"
                message_object['message'] = message
                await websocket.send(json.dumps(message_object))

        elif 'help' == user_command:
            message_object['func'] = "help"

        elif 'summarize' in user_command:
            command_list = user_command.split(" ")
            if len(command_list) == 1:
                file_index = await aioconsole.ainput("Enter the file index: ")
                file_index = file_index.strip()
                if file_index == "quit": close_and_exit(websocket)
                if file_index == "exit": break
                if not file_index.isdigit():
                    print("File index must be a digit.")
                    continue
                else:
                    command_list.append(file_index)

            message_object['func'] = "summarize"
            message_object['file_index'] = str(command_list[1])

        elif 'wiki s' in user_command:
            message_object['func'] = "wiki_search"
            user_command_list = user_command.split(" ")
            if len(user_command_list) == 2:
                message_object['query'] = await aioconsole.ainput("Enter your search query: ")
            else:
                message_object['query'] = user_command_list[2]

        elif 'wiki r' in user_command:
            message_object['func'] = "wiki_results"

        elif 'wiki' in user_command:
            should_save_string = await aioconsole.ainput("Save this wiki page? (y/n): ")
            should_save = True if 'y' in should_save_string else False
            if not should_save: 
                return_full_string = await aioconsole.ainput("Return full content? (y/n): ")
            else: return_full_string = "n"
            message_object['func'] = "wiki"
            message_object['query'] = user_command.split("wiki ")[1]
            message_object['should_save'] = should_save
            message_object['return_full'] = True if 'y' in return_full_string else False

        elif ('get' in user_command) and ('char' in user_command):
            message_object['func'] = "get_chat_characters"

        elif ('ad' in user_command) and ('char' in user_command):
            message_object['func'] = "add_chat_character"
            if len(user_command.split(" ")) == 2:
                character_name = await aioconsole.ainput("Enter the character name: ")
            else: character_name = user_command.split(" ")[2]
            message_object['character_name'] = character_name
            character_prompt = await aioconsole.ainput("Enter the character prompt: ")
            message_object['character_prompt'] = character_prompt

        elif (('rem' in user_command) or ('del' in user_command)) and ('char' in user_command):
            message_object['func'] = "remove_chat_character"
            if len(user_command.split(" ")) == 2:
                character_name = await aioconsole.ainput("Enter the character name: ")
            else: character_name = user_command.split(" ")[2]
            message_object['character_name'] = character_name

        elif ('set' in user_command) and ('char' in user_command):
            message_object['func'] = "configure"
            character_name = await aioconsole.ainput("Enter the character name: ")
            message_object['chat_character'] = character_name

        elif ('set' in user_command) and ('config' in user_command):
            message_object['func'] = ""
            configuration = await aioconsole.ainput("Enter the configuration field: ")
            configuration_value = await aioconsole.ainput("Enter the configuration value: ")
            message_object[configuration] = configuration_value
        elif 'clear' in user_command:
            message_object['func'] = "clear_history"
        else:
            message_object = {"func": user_command}
        
        if 'help' in user_command:
            message_object['help'] = True
        
        if should_continue: continue
        else: await websocket.send(json.dumps(message_object))

async def create_websocket_connection() -> None:
    def print_close_message():
        print('-'*18)
        print("Connection closed.")
        print()

    uri = f"ws://{config['hostname']}:{config['port']}/ws"  
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")
        try:
            await asyncio.gather(listen_for_messages(websocket), send_messages(websocket), tts_generator(), tts_player())
        except websockets.exceptions.ConnectionClosedOK: print_close_message()
        except websockets.exceptions.ConnectionClosedError: print_close_message()
        except KeyboardInterrupt:
            await websocket.close()
            print_close_message()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(create_websocket_connection())
