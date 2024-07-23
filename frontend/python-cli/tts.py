import os
import time
import asyncio
import edge_tts
from pygame import mixer

GOOD_FEMALE_VOICES = ["en-GB-SoniaNeural", "en-IE-EmilyNeural", "en-IN-NeerjaExpressiveNeural", "en-IN-NeerjaNeural","en-US-AvaNeural", "en-US-EmmaNeural", "en-US-MichelleNeural", "en-ZA-LeahNeural", "en-SG-LunaNeural", "el-GR-AthinaNeural", "de-DE-KatjaNeural", "fr-FR-VivienneMultilingualNeural", "hi-IN-SwaraNeural", "ml-IN-SobhanaNeural", "ps-AF-LatifaNeural", "zh-CN-liaoning-XiaobeiNeural", "zh-CN-shaanxi-XiaoniNeural", "zh-CN-XiaoxiaoNeural","zh-TW-HsiaoChenNeural"] # en-SG-LunaNeural and el-GR-AthinaNeural are questionable
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

async def aplay_audio(path):
    sound = mixer.Sound(path)
    sound.play()
    while mixer.get_busy():
        await asyncio.sleep(0.1)

async def aspeak_chunk(text) -> str:
    communicate = edge_tts.Communicate(text, VOICE)
    output_name = str(time.time()) + ".mp3"
    output_name = SPEECH_OUTPUT_DIR + os.sep + output_name
    await communicate.save(output_name)
    return output_name

if not os.path.exists(SPEECH_OUTPUT_DIR):
    os.mkdir(SPEECH_OUTPUT_DIR)

mixer.init()

if __name__ == "__main__":
    time_start = time.time()
    text = "Hi Zach, I hope you had a great day! How can I help you?"
    asyncio.run(aspeak_chunk(text))
    print(f"Runtime: {round(time.time() - time_start, 1)} seconds")
    input("Press Enter to exit...")