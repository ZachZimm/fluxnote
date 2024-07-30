import asyncio
import websockets
import json
import queue
import aioconsole
import tts
import time
import sys
from threading import Thread

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
print_queue = queue.Queue()
is_fist_sentence = True
num_sentences_per_generation = 2
num_sentences_this_message = 0

def queue_audio(config, message):
    if config["speech_enabled"]:
        tts_generation_queue.put_nowait(message)

def is_full_sentence(message):
    message = message.strip().replace("\n", " ").replace("...", ",")

    if len(message) < 5: return False
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

def print_worker():
    while True:
        message = print_queue.get()
        print(message, end="", flush=True)
        print_queue.task_done()
        time.sleep(1e-4) # 0.1 ms, I think this needs to be a bit higer on windows (1e-3 ish)

thread = Thread(target=print_worker, daemon=True)
thread.start()
    
def aecho(message, end="\n", flush=False):
    def _print(message, end="\n"):
        i = 0
        messsage_len = 100
        _len = len(message)
        while i < _len:
            if i + messsage_len < _len:
                print_queue.put(message[i:i+messsage_len])
            else:
                print_queue.put(message[i:] + end)
            i += messsage_len
    try:
        _print(message, end=end)
    except Exception as e: print(e) # Not good 

def print_json_message(json_str) -> None:
    global streaming_message
    global is_fist_sentence
    dict_obj = json.loads(json_str)
    if dict_obj["mode"] == "chat":
        aecho(f"Chat: {dict_obj['message']}")
        return

    elif 'streaming' in dict_obj["mode"]:
        if 'finished' in dict_obj["mode"]:
            streaming_message = streaming_message.replace("\\\n", "").replace("\\n", "").replace("\\", "")
            streaming_message = streaming_message.strip()
            if len(streaming_message) > 0:
                queue_audio(config, streaming_message)
            aecho("\n> ", end="")
            streaming_message = ""
            is_fist_sentence = True
            return

        streaming_message += dict_obj["message"]
        streaming_message = fix_prefixes(streaming_message)
        aecho(dict_obj["message"], end="", flush=True)
        if is_full_sentence(streaming_message): # If a full sentance has been streamed, queue it for tts
            global num_sentences_this_message
            num_sentences_this_message += 1

            if (num_sentences_this_message >= num_sentences_per_generation) or is_fist_sentence:
                num_sentences_this_message = 0
                queue_audio(config, streaming_message)
                streaming_message = ""
                is_fist_sentence = False
        return

    elif "summary" in dict_obj["mode"]:
        if "error" in dict_obj["mode"]:
            aecho(f"Error: {dict_obj['message']}")
            return
        if '{' == dict_obj["message"][0]:
            dict_obj = json.loads(dict_obj["message"])
            print_summary(dict_obj["summary"])
            return
    elif "wiki search results" in dict_obj["mode"]:
        list_obj = json.loads(dict_obj["message"])
        for i in range(len(list_obj)):
            aecho(f"{i+1}: {list_obj[i]}")
    elif "wiki" == dict_obj["mode"]:
        wiki_obj = json.loads(dict_obj["message"])
        wiki_keys = wiki_obj.keys()
        if 'title' in wiki_keys:
            aecho(wiki_obj["title"])
        if 'summary' in wiki_keys:
            aecho(wiki_obj["summary"])
        if 'content' in wiki_keys:
            aecho(wiki_obj["content"])
    else:
        aecho(f"Mode: {dict_obj['mode']}\n")
        
        try:
            message = dict_obj["message"]
            if message[0] == '"' and message[-1] == '"':
                    message = message[1:-1]
            message = message.replace("\\n","").replace('\\"','"').replace('\\\\"',"'").replace("\\","")
            if message[0] == "[":
                message = message.replace("}{","},{").replace("} {","},{")
            try:
                message_obj = json.loads(message)
                if isinstance(message_obj, list):
                    for m in message_obj:
                        aecho(str(m))
                        
                elif isinstance(message_obj, dict):
                    for key in message_obj.keys():
                        aecho(f"{key}: {message_obj[key]}")
            except Exception as e:
                # 'message' is not json
                aecho(message)
        except Exception as e:
            aecho(f"Error: Could not parse json.\n{e}\n")
            aecho(dict_obj["message"])

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
    tts.VOICE = config["speech_voice"]
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
                # this should be easy enough to re-implement as REST
                # if that ever proves nessecary
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
        elif ('set' in user_command) and ('voice' in user_command):
            print("Available voices:")
            voices = tts.GOOD_FEMALE_VOICES
            i = 0
            for voice in tts.GOOD_FEMALE_VOICES:
                i += 1
                print(f"{i}: {voice}")
            voice = await aioconsole.ainput("Enter your selected voice: ")
            if voice in tts.GOOD_FEMALE_VOICES:
                tts.VOICE = voice 
            elif voice.isdigit() and int(voice) <= len(voices):
                tts.VOICE = voices[int(voice)-1]
            else: print("Invalid voice.")
            continue # this is a client method
        elif ('get' in user_command) and ('voice' in user_command):
            voice = tts.VOICE
            print(f"Selected voice: {voice}")
            continue # this is a client method
        elif 'voices' in user_command:
            voices = tts.GOOD_FEMALE_VOICES
            for voice in voices:
                print(voice)
            continue # this is a client method
        elif ('save' in user_command) and ('config' in user_command):
            with open(config_dir, 'w') as f:
                json.dump(config, f)
            print("Configuration saved.")
            continue
        elif 'history' == user_command:
            message_object['func'] = "chat_history"
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

async def standalone_tts(text):
    tts.VOICE = config["speech_voice"]
    output_name = await tts.aspeak_chunk(text)
    await tts.aplay_audio(output_name)
    

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if (len(sys.argv) == 3 and ('--tts' in sys.argv) or ('-t' in sys.argv)):
            if ('-f' in sys.argv) or ('--file' in sys.argv):
                with open(sys.argv[-1], 'r') as f:
                    text = f.read()
                text = text.strip()
                asyncio.run(standalone_tts(text))
            asyncio.run(standalone_tts(sys.argv[-1]))
    
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(create_websocket_connection())