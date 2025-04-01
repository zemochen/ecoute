import custom_speech_recognition as sr
import os
from audio_system import get_default_speaker
from datetime import datetime

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    if os.name != "nt":
        import pyaudio
    else:
        raise

RECORD_TIMEOUT = 3
ENERGY_THRESHOLD = 1000
DYNAMIC_ENERGY_THRESHOLD = False

class BaseRecorder:
    def __init__(self, source):
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = ENERGY_THRESHOLD
        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

        if source is None:
            raise ValueError("audio source can't be None")

        self.source = source

    def adjust_for_noise(self, device_name, msg):
        print(f"[INFO] Adjusting for ambient noise from {device_name}. " + msg)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        print(f"[INFO] Completed ambient noise adjustment for {device_name}.")

    def record_into_queue(self, audio_queue):
        def record_callback(_, audio:sr.AudioData) -> None:
            data = audio.get_raw_data()
            audio_queue.put((data, datetime.utcnow()))

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=RECORD_TIMEOUT)

class DefaultMicRecorder(BaseRecorder):
    def __init__(self):
        super().__init__(source=sr.Microphone(sample_rate=16000))
        self.adjust_for_noise("Default Mic", "Please make some noise from the Default Mic...")

class DefaultSpeakerRecorder(BaseRecorder):

    # Different implementations of obtaining the info dict of a default speaker, for different platforms
    if os.name == "nt":
        def _get_default_speaker(self):
            # Requires PyAudioWPatch >= 0.2.12.6
            with pyaudio.PyAudio() as p:
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                if not default_speakers["isLoopbackDevice"]:
                    for loopback in p.get_loopback_device_info_generator():
                        if default_speakers["name"] in loopback["name"]:
                            default_speakers = loopback
                            break
                    else:
                        print("[ERROR] No loopback device found.")
                        return
                return default_speakers

    else:
        def find_blackhole_device(self, p):
            # find blackhole
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if "BlackHole" in dev["name"] and dev["maxInputChannels"] > 0:
                    print(
                        f"Found BlackHole device: {dev['name']} (Index: {dev['index']})")
                    return dev
            raise Exception(
                "BlackHole device not found. Please ensure it is installed and configured.")

        def _get_default_speaker(self):
            p = pyaudio.PyAudio()
            try:
                # find blackhole
                blackhole_device = self.find_blackhole_device(p)
            finally:
                p.terminate()
            return blackhole_device


    def __init__(self):
        default_speakers = self._get_default_speaker()
        source = sr.Microphone(speaker=True,
                               device_index= default_speakers["index"],
                               sample_rate=int(default_speakers["defaultSampleRate"]),
                               chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
                               channels=default_speakers["maxInputChannels"])
        super().__init__(source=source)
        self.adjust_for_noise("Default Speaker", "Please make or play some noise from the Default Speaker...")