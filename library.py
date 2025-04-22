import audioprts
import utils
import os
from db import collection
import asyncio
import matplotlib.pyplot as plt
import configargparse

def get_config():
    parser = configargparse.ArgParser(default_config_files=['config.yaml'],
                                      config_file_parser_class=configargparse.YAMLConfigFileParser)
    parser.add('-c', '--config', is_config_file=True, help='Path to config file')

    parser.add('--music_dir', type=str, default='music', help='Directory with original MP3 music files')
    parser.add('--wav_output_dir', type=str, default='musicWav', help='Directory to save converted WAV files')
    parser.add('--n_fft', type=int, default=4096)
    parser.add('--hop_length', type=int, default=512)
    parser.add('--bands', nargs='+', type=int, default=[0, 10, 40, 80, 120, 180, 300, 500, 800, 1200])
    parser.add('--fan_value', type=int, default=10)
    parser.add('--max_time_delta', type=float, default=5.0)


    parser.add('--snippet', type=str, default='snippets/perfect.wav', help="snippet file to analyze")
    parser.add('--highlight', type=str, default="Unknown Song Name", help="Song to highlight in plot")
    parser.add('--offset', action='store_true', help="Use offset-based matching")
    parser.add('--noise', action='store_true', help="Add noise to audio before matching")

    return parser.parse_args()

# Generates our song library and saves it to a MongoDB database

async def process_songs(config):
    for song in (os.listdir(config.music_dir)):
        if not song.endswith(".mp3"):
            continue

        try:
            artist = song.split(']')[0].split('[')[1]
            songname = song.split('.mp3')[0].split(']')[1]
        except IndexError:
            print(f"Skipping improperly named file: {song}")
            continue

        input_path = os.path.join(config.music_dir, song)
        output_path = os.path.join(config.wav_output_dir, f"{os.path.splitext(song)[0]}.wav")

        os.makedirs(config.wav_output_dir, exist_ok=True)
        utils.convert_mp3_to_wav(input_path, output_path)

        song_hash = audioprts.song2hash(output_path, artist, songname, config)
        await audioprts.savehash(song_hash)
        print(f"Processed and saved hashes for: {artist} - {songname}")

if __name__ == "__main__":
    config = get_config()
    asyncio.run(process_songs(config))