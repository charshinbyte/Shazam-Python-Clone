from pydub import AudioSegment
from scipy.io import wavfile
import numpy as np
from pydub.utils import make_chunks
import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import soundfile as sf
from typing import Optional

# Converts MP3 Files to WAV files
def convert_mp3_to_wav(mp3_file_path, wav_file_path : Optional[str] = None ):
  if wav_file_path == None:
    wav_file_path = mp3_file_path.split(".mp3")[0] + ".wav"

  audio = AudioSegment.from_mp3(mp3_file_path)
  audio = audio.set_channels(1)
  audio = audio.set_frame_rate(8192)
  audio.export(wav_file_path,
               format="wav")
  return wav_file_path

# Converts M4A Files to WAV files
def convert_m4a_to_wav(m4a_file_path):
  wav_file_path = m4a_file_path.split(".m4a")[0] + ".wav"
  audio = AudioSegment.from_file(m4a_file_path, format = 'm4a')
  audio = audio.set_channels(1)
  audio = audio.set_frame_rate(8192)
  audio.export(wav_file_path,
                format="wav")
  return wav_file_path

# Splits song into 8 second clips (Useful for testing identification later)
def process_audio(file_name):
  myaudio = AudioSegment.from_file(file_name, "wav")
  chunk_length_ms = 8000  # pydub calculates in millisec
  chunks = make_chunks(myaudio, chunk_length_ms)  # Make chunks of 8 seconds

  SongTitle = file_name.split(".")[0]
  if not os.path.exists(f"./{SongTitle}"):
    os.makedirs(f"./{SongTitle}")

  for i, chunk in enumerate(chunks):
    chunk_name = f'./{SongTitle}/' + file_name + "_{0}.wav".format(i)
    print("exporting", chunk_name)
    chunk.export(chunk_name, format="wav")

# Adds a Gaussian noise to a song
def add_noise(wav_file_name, noisy_wav_file_name, snr_db=10):
    y, sr = librosa.load(wav_file_name, sr=None)
    signal_power = np.mean(y ** 2)
    snr_linear = 10 ** (snr_db / 10)
    noise_power = signal_power / snr_linear
    noise = np.random.normal(0, np.sqrt(noise_power), y.shape)
    y_noisy = y + noise
    sf.write(noisy_wav_file_name, y_noisy, sr)

# Shows a Spectrogram of an audio
def save_spectrogram(audio_path):
    y, sr = librosa.load(audio_path)
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    plt.figure(figsize=(20, 6))
    librosa.display.specshow(D, x_axis='time', y_axis='log', sr=sr)
    plt.colorbar(format='%+2.0f dB')
    plt.title(f'{audio_path.split(".")[0]} Spectrogram')
    output_image_path = str(audio_path.split(".")[0] + '_spectrogram.png')
    plt.savefig(output_image_path)

