# Find My Music

## Setting up the environment
```
conda create -n findmymusic -r requirements.txt
```

## Plotting a snippet
Add youre recorded snippet audio file into the snippets folder and run the following command.

```
python3 plot.py --config config.yaml
```


## Generating the Music Libary
Set your parameters in config.yaml (input, output_dir, n_fft, hop_length, bands, fan_value and max time delta).
Add your .mp3 files into the music directory and run the following command.

```
 python3 library.py --config config.yaml
```

The script will convert the mp3 files into a wav files and save the audio fingerprint hashes into a mongoDB database. Adjust the database location in `db.py`


# Finding a Match

Upload a snippet of audio onto `/snippets`

```
python3 match.py --config config.yaml
```