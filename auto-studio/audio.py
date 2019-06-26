import pyaudio
import wave
import time
import threading
import datetime
from pydub import AudioSegment
import tempfile
import Queue
import sys
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)
import os


WAVE_OUTPUT_FILENAME = "audio.wav"
WAVE_NORMALIZED_OUTPUT_FILENAME = "audio_normalized.wav"

def add_time(fname):
    now = datetime.datetime.now()
    nname = fname[:-4]+'_'+now.isoformat()[:-7].replace(':','-')+fname[-4:]
    return nname

def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

def recording(self):
    q = Queue.Queue()
    
    def callback(indata, frames, time, status):
        q.put(indata.copy())

    # Make sure the file is opened before recording anything:
    with sf.SoundFile(self.filename, mode='x', samplerate=self.samplerate, channels=1, subtype=None) as file:
        with sd.InputStream(samplerate=self.samplerate, device=None, channels=1, callback=callback):
            while self.recording:
                file.write(q.get())

class AudioDevice:

    def __init__(self):
        self.device = sd.query_devices(None, 'input')
        self.samplerate = int(self.device['default_samplerate'])

    def start_recording(self, save_folder):
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        self.recording = True
        self.save_folder = save_folder
        self.filename = os.path.join(save_folder, add_time(WAVE_OUTPUT_FILENAME))
        self.thread = threading.Thread(target=recording, args=(self,))
        self.thread.start()
    
    def stop_recording(self):
        self.recording = False
        self.thread.join()
        print("finished recording audio")
        sound = AudioSegment.from_file(self.filename, "wav")
        normalized_sound = match_target_amplitude(sound, -20.0)
        normalized_filename = add_time(WAVE_NORMALIZED_OUTPUT_FILENAME)
        normalized_sound.export(os.path.join(self.save_folder, normalized_filename), format="wav")
        print("finished normalizing audio recording")

        return os.path.join(self.save_folder, normalized_filename)

        # return normalized_filename
if __name__ == "__main__":
    device = AudioDevice()
    device.start_recording("raw")
    time.sleep(60)
    device.stop_recording()