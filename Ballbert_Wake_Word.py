import platform
import time
import pvporcupine
import speech_recognition as sr
from pvrecorder import PvRecorder
import threading
import numpy as np
import soxr
import zlib

import base64
from Config import Config

from Event_Handler import event_handler
from Hal.Assistant import initialize_assistant

assistant = initialize_assistant()

config = Config()


class Ballbert_Wake_Word:
    def __init__(self) -> None:
        self.porcupine = None

        self.porcupine_api_key = ""
        self.recogniser = sr.Recognizer()

        self.create_pvporcupine()

        event_handler.on("Ready", self.start)

    def create_pvporcupine(self):
        def get_porcupine_api_key(key):
            print("set", key)
            self.porcupine_api_key = key
            try:
                system = platform.system()

                if system == "Windows":
                    path = "./Skills/Ballbert_Wake_Word/Ball-Bert_en_windows_v2_2_0.ppn"
                elif system == "Darwin":
                    path = "./Skills/Ballbert_Wake_Word/Ball-Bert_en_mac_v2_2_0.ppn"
                elif system == "Linux":
                    path = "./Skills/Ballbert_Wake_Word/Ball-Bert_en_raspberry-pi_v2_2_0.ppn"
                else:
                    raise Exception("Invalid System")

                self.porcupine = pvporcupine.create(
                    access_key=self.porcupine_api_key,
                    keyword_paths=[path],
                )
            except Exception as e:
                event_handler.trigger("Error", e)
            
        assistant.websocket_client.add_route(get_porcupine_api_key)
        assistant.websocket_client.send_message("get_porcupine_api_key")
            


    def start(self):
        if not self.porcupine:
            print("no pork")
            self.create_pvporcupine()

            return
        mic = sr.Microphone(device_index=1)
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 5000

        with mic as source:
            print("Ready!")
            while True:
                audio_frames = source.stream.read(1410)

                np_audio_data = np.frombuffer(audio_frames, dtype=np.int16)

                np_audio_data = soxr.resample(np_audio_data, 44100, 16000)

                keyword_index = self.porcupine.process(np_audio_data)
                if keyword_index >= 0:
                    try:
                        print("keyword")
                        print("Keyword")
            
                        print("Keyword Detected")
                
                        audio_data = self.recogniser.listen(source)
                        
                        # Compress binary audio data using zlib
                        compressed_audio_data = zlib.compress(audio_data.frame_data)
                
                        # Convert compressed data to base64-encoded string
                        base64_compressed_audio_data = base64.b64encode(compressed_audio_data).decode(
                            "utf-8"
                        )
                
                        assistant.websocket_client.send_message(
                            "handle_audio",
                            audio_data=base64_compressed_audio_data,
                            sample_rate=audio_data.sample_rate,
                            sample_width=audio_data.sample_width,
                        )
                                
                    except Exception as e:
                        event_handler.trigger("Error", e)
