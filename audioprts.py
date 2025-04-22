import configargparse
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import maximum_filter
from db import collection
import asyncio


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


def generate_spectrogram(audio_path, n_fft, hop_length):
    y, sr = librosa.load(audio_path)
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length)), ref=np.max)
    return D, sr, n_fft

def spectrogram_band(D, sr, freq_range, n_fft):
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    min_freq, max_freq = freq_range
    freq_indices = np.where((freqs >= min_freq) & (freqs <= max_freq))[0]
    return D[freq_indices, :], freqs[freq_indices]

def plot_spectrogram(D, f, sr, hop_length):
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(D, sr=sr, hop_length=hop_length, x_axis='time', y_axis='linear', cmap='magma', y_coords=f)
    plt.colorbar(format='%+2.0f dB')
    plt.title('Spectrogram')
    plt.tight_layout()
    plt.show()

def get_energy_peaks(D):
    peaks = np.zeros_like(D)
    max_indices = np.argmax(D, axis=0)
    for col, row in enumerate(max_indices):
        peaks[row, col] = D[row, col]
    
    nonzero_vals = peaks[peaks < 0]
    if len(nonzero_vals) > 0:
        threshold = np.percentile(nonzero_vals, 80)
        peaks = np.where(peaks >= threshold, peaks, 0)

    peaks = abs(peaks)
    neighborhood_size = (10, 10)
    min_value_threshold = 1e-6

    filtered_max = maximum_filter(peaks, size=neighborhood_size, mode='constant')
    local_max = (peaks == filtered_max)
    nonzero_mask = (peaks > min_value_threshold)

    return local_max & nonzero_mask

def get_fingerprints(D, n_fft, sr, bands, hop_length):
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    freq_indices = np.where((freqs >= bands[0]) & (freqs <= bands[-1]))[0]
    freqs_band = freqs[freq_indices]

    peaks = []
    for i in range(len(bands) - 1):
        D1, _ = spectrogram_band(D, sr, (bands[i], bands[i + 1]), n_fft)
        peak_band = get_energy_peaks(D1)
        peaks.append(peak_band)

    fingerprints = np.vstack(peaks)
    i, j = np.where(fingerprints != 0)
    duration = D.shape[1] * hop_length / sr
    time = np.linspace(0, duration, D.shape[1])

    fingerprint_times = time[j]
    fingerprint_freqs = freqs_band[i]

    sorted_indices = np.argsort(fingerprint_times)
    return fingerprint_times[sorted_indices], fingerprint_freqs[sorted_indices]

def generate_hash(times, freqs, artist, song, fan_value, max_time_delta):
    hash_map = {}
    num_peaks = len(times)

    for i in range(num_peaks):
        anchor_time, anchor_freq = times[i], freqs[i]
        count, j = fan_value, 1

        while count > 0 and i + j < num_peaks:
            target_time, target_freq = times[i + j], freqs[i + j]
            delta_time = target_time - anchor_time
            if delta_time > max_time_delta:
                break
            if target_time != anchor_time:
                hash_key = (int(anchor_freq), int(target_freq), round(delta_time, 1))
                metadata = {"anchor_time": anchor_time, "artist": artist, "song title": song}
                hash_map.setdefault(hash_key, []).append(metadata)
                count -= 1
            j += 1
    return hash_map

def song2hash(audio, artist, song, config):
    D, sr, n_fft = generate_spectrogram(audio, config.n_fft, config.hop_length)
    times, freqs = get_fingerprints(D, n_fft, sr, config.bands, config.hop_length)
    return generate_hash(times, freqs, artist, song, config.fan_value, config.max_time_delta)

def clip2hash(audio, config):
    D, sr, n_fft = generate_spectrogram(audio, config.n_fft, config.hop_length)
    times, freqs = get_fingerprints(D, n_fft, sr, config.bands, config.hop_length)

    hash_map = {}
    num_peaks = len(times)

    for i in range(num_peaks):
        anchor_time, anchor_freq = times[i], freqs[i]
        count, j = config.fan_value, 1

        while count > 0 and i + j < num_peaks:
            target_time, target_freq = times[i + j], freqs[i + j]
            delta_time = target_time - anchor_time
            if delta_time > config.max_time_delta:
                break
            if target_time != anchor_time:
                hash_key = (int(anchor_freq), int(target_freq), round(delta_time, 1))
                hash_map.setdefault(hash_key, []).append({"anchor_time": anchor_time})
                count -= 1
            j += 1
    return hash_map

async def savehash(hashed_song):
    for hash_key, metadata_list in hashed_song.items():
        doc_id = str(hash_key)
        await collection.update_one(
            {"_id": doc_id},
            {"$push": {"metadata": metadata_list}},
            upsert=True
        )

