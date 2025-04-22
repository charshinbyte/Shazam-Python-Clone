import audioprts
import matplotlib.pyplot as plt
import argparse
import utils
import db

def plot_songs(audio, song_name: str = 'Unknown Song', file_format: str = 'wav'):
    if file_format == 'mp3':
        audio = utils.convert_mp3_to_wav(audio)
    elif file_format == 'm4a':
        audio = utils.convert_m4a_to_wav(audio)

    D, sr, n_fft = audioprts.generate_spectrogram(audio)
    hop_length = 512

    D_band, freqs_band = audioprts.spectrogram_band(D, sr, (0, 1200), n_fft)
    fingerprint_times, fingerprint_freqs = audioprts.get_fingerprints(D, n_fft, sr)

    duration = D_band.shape[1] * hop_length / sr  # correct time duration
    extent = [0, duration, freqs_band[0], freqs_band[-1]]
    
    plt.figure(figsize=(12, 8))
    plt.imshow(D_band, cmap='magma', aspect='auto', origin='lower', extent=extent)
    plt.scatter(fingerprint_times, fingerprint_freqs, c='cyan', s=5, label='Fingerprint')

    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title(f"Spectrogram with Fingerprints  of {song_name}")
    plt.colorbar(label="Amplitude (dB)")
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.show()

# plot_songs("snippets/Bruno.wav")

# To use in terminal
# python3 plot.py --audio snippets/Bruno.m4a --format m4a
parser = argparse.ArgumentParser(description= "Plot Song")
parser.add_argument('--audio', type=str, help="Audio File")
parser.add_argument('--name', type=str, default="Unknown Song Name", help="Artist Name")
parser.add_argument('--format', type=str, default="wav", help="file format (wav, mp3, m4a)")
args = parser.parse_args()

plot_songs(args.audio, args.name, args.format)