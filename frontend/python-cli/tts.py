import os
import time
import asyncio
import edge_tts
import inflect
from pygame import mixer

GOOD_FEMALE_VOICES = ["en-US-AvaNeural", "en-GB-SoniaNeural", "en-IE-EmilyNeural", "en-IN-NeerjaExpressiveNeural", "en-IN-NeerjaNeural", "en-US-EmmaNeural", "en-US-MichelleNeural", "en-ZA-LeahNeural", "en-SG-LunaNeural", "el-GR-AthinaNeural", "de-DE-KatjaNeural", "fr-FR-VivienneMultilingualNeural", "hi-IN-SwaraNeural", "ml-IN-SobhanaNeural", "ps-AF-LatifaNeural", "zh-CN-liaoning-XiaobeiNeural", "zh-CN-shaanxi-XiaoniNeural", "zh-CN-XiaoxiaoNeural","zh-TW-HsiaoChenNeural"] # en-SG-LunaNeural and el-GR-AthinaNeural are questionable
VOICE = "en-US-AvaNeural"
OUTPUT_DIR = "test_output"
SPEECH_OUTPUT_DIR = "speech"

async def atest_voices(text) -> None:
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    # voices = await edge_tts.VoicesManager.create()
    # vs = voices.find(Gender="Female")
    for voice in GOOD_FEMALE_VOICES: 
        communicate = edge_tts.Communicate(text, voice)
        output_name = f"{OUTPUT_DIR}{os.sep}{voice}.mp3"
        await communicate.save(output_name)
        print(f"Finished {output_name}")
        await asyncio.sleep(1)

def replace_number_digits_with_words(text: str) -> str: # Replace numbers with words
    text = text.replace("0. ", "0 . ").replace("1. ", "1 . ").replace("2. ", "2 . ").replace("3. ", "3 . ").replace("4. ", "4 . ").replace("5. ", "5 . ").replace("6. ", "6 . ").replace("7. ", "7 . ").replace("8. ", "8 . ").replace("9. ", "9 . ")

    p = inflect.engine() # So TTS models for different languages can read numbers in english
    words = text.split(" ")
    for i in range(len(words)):
        try:
            num = int(words[i])
            words[i] = p.number_to_words(num)
        except:
            pass
    text = " ".join(words)
    text = text.replace("0 . ", "0. ").replace("1 . ", "1. ").replace("2 . ", "2. ").replace("3 . ", "3. ").replace("4 . ", "4. ").replace("5 . ", "5. ").replace("6 . ", "6. ").replace("7 . ", "7. ").replace("8 . ", "8. ").replace("9 . ", "9. ")
    return text

def clean_text_for_tts(text: str) -> str:
    text = text.replace("\n", " ").replace("*","")
    
    text = replace_number_digits_with_words(text)
    return text

async def aplay_audio(path: str):
    if AUDIO_ENABLED == False:
        return
    sound = mixer.Sound(path)
    sound.play()
    while mixer.get_busy():
        await asyncio.sleep(0.1)

async def aspeak_chunk(text: str) -> str:
    if AUDIO_ENABLED == False:
        return ""
    text = clean_text_for_tts(text)
    communicate = edge_tts.Communicate(text, VOICE)
    output_name = str(time.time()) + ".mp3"
    output_name = SPEECH_OUTPUT_DIR + os.sep + output_name
    await communicate.save(output_name)
    return output_name

if not os.path.exists(SPEECH_OUTPUT_DIR):
    os.mkdir(SPEECH_OUTPUT_DIR)

import contextlib

try:
    with contextlib.redirect_stdout(None): # Suppress pygame output - or its supposed to anyway
        mixer.init()
    AUDIO_ENABLED = True
except Exception as e:
    print(f"Error: {e}")
    AUDIO_ENABLED = False