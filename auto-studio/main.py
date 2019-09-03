from PyEDSDK import Camera
from audio import AudioDevice
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
import os
from moviepy.audio.io.AudioFileClip import AudioFileClip
import datetime

TIME_DELAY_AUDIO_VIDEO = 0.45
RAW_FOOTAGE = "raw"
SAVE_FOLDER = "out"

def add_time(fname):
    now = datetime.datetime.now()
    nname = fname[:-4]+'_'+now.isoformat()[:-7].replace(':','-')+fname[-4:]
    return nname

camera = Camera()
audio = AudioDevice()
raw_input("prepare camera before shooting...")
audio.start_recording(RAW_FOOTAGE)
camera.start_recording(RAW_FOOTAGE)
raw_input("press enter to finish recording...")
audio_filename = audio.stop_recording()
video_filename = camera.stop_recording()
del camera
# get choice from user
choice = None
while True:
    choice = raw_input("type [y]es to keep, or [n]o to abandon...").strip()
    if (choice == "y" or choice == "yes"):
        break
    elif (choice == "n" or choice == "no"):
        print("abandoned take")
        exit(0)
print("loading video clip into moviepy")
video_clip = VideoFileClip(video_filename)
# video_clip = VideoFileClip("raw/mov_2019-08-25T21-02-53.mp4")
print("got video clip in moviepy")
audio_clip = AudioFileClip(audio_filename)
# audio_clip = AudioFileClip("raw/audio_2019-08-25T23-06-23.wav")
print("got clips")
audio_clip = audio_clip.subclip(TIME_DELAY_AUDIO_VIDEO)
print("chopped audio")
video_clip = video_clip.set_audio(audio_clip)
print("set the audio")
# add effects to video
video_clip = video_clip.fx(vfx.fx.fadein.fadein, duration=0.5).fx(vfx.fx.fadeout.fadeout, duration=0.5)
print("added effects")
video_clip.write_videofile(os.path.join(SAVE_FOLDER, add_time("mixed_video.mp4")))
print("wrote video")
