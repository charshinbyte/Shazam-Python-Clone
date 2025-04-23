import audioprts
import matplotlib.pyplot as plt
import utils
import db
import library

def plot_songs(audio, song_name: str = 'Unknown Song', file_format: str = 'wav', config=None):
    # Convert to WAV if needed
    if file_format == 'mp3':
        audio = utils.convert_mp3_to_wav(audio, output_dir=config.wav_output_dir)
    elif file_format == 'm4a':
        audio = utils.convert_m4a_to_wav(audio, output_dir=config.wav_output_dir)

    # Generate spectrogram
    D, sr, n_fft = audioprts.generate_spectrogram(audio, n_fft=config.n_fft, hop_length=config.hop_length)
    hop_length = config.hop_length

    # Select band-limited spectrogram
    D_band, freqs_band = audioprts.spectrogram_band(D, sr, (0, 1200), n_fft)

    # Get fingerprints
    fingerprint_times, fingerprint_freqs = audioprts.get_fingerprints(D, n_fft, sr, config.bands, hop_length)

    # Compute plot extent
    duration = D_band.shape[1] * hop_length / sr
    extent = [0, duration, freqs_band[0], freqs_band[-1]]

    # Plotting
    plt.figure(figsize=(12, 8))
    plt.imshow(D_band, cmap='magma', aspect='auto', origin='lower', extent=extent)
    plt.scatter(fingerprint_times, fingerprint_freqs, c='cyan', s=5, label='Fingerprint')

    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.title(f"Spectrogram with Fingerprints of '{song_name}'")
    plt.colorbar(label="Amplitude (dB)")
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    config = library.get_config()
    file_format = config.snippet.split('.')[-1]  # Extract file extension

    plot_songs(
        audio=config.snippet,
        song_name=config.highlight,
        file_format=file_format,
        config=config
    )