
import audioprts
import utils
import os
from db import collection
import asyncio
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
import library
import argparse
from typing import Optional 
# No 1: RAW MATCHES (Doesn't consider offset times)
async def find_matches(clipHash):
    matchCount = 0
    matchdict = dict()
    for key, clip_metadata_list in clipHash.items():
        try:
            # For EACH HASH
            documents = await collection.find_one({"_id": str(key)})
            if documents is not None:
                # FOR EACH MATCH 
                for doc in documents['metadata']:
                    detectedSong = str(doc[0]["song title"])
                    if detectedSong in matchdict:
                        matchdict[detectedSong] += 1
                    else:
                        matchdict[detectedSong] = 0         
        except Exception as e:
            print(f"No Key in Library {key} - {e}")
    return matchdict

# No 2: Matching with offset times:
async def find_matches_with_offset(clipHash):
    offset_dict = defaultdict(lambda: defaultdict(int))  # song_title -> offset -> count

    for key, clip_metadata_list in clipHash.items():
        try:
            # Get the list of song fingerprints from the DB
            documents = await collection.find_one({"_id": str(key)})

            if documents is not None:
                for clip_meta in clip_metadata_list:
                    clip_time = clip_meta["anchor_time"]

                    # metadata is a list of lists of dicts
                    for song_list in documents["metadata"]:
                        for song_meta in song_list:
                            song_time = song_meta["anchor_time"]
                            song_title = song_meta["song title"]

                            # Compute time offset
                            # offset_bin_size = 0.5  # try 0.5 or 1 second bins
                            # offset = round((song_time - clip_time) / offset_bin_size) * offset_bin_size


                            offset = round(song_time - clip_time,1)

                            offset_dict[song_title][offset] += 1

        except Exception as e:
            print(f"No Key in Library {key} - {e}")

    # Aggregate results by most common offset for each song
    match_scores = {}
    for song_title, offset_counts in offset_dict.items():
        best_offset_count = max(offset_counts.values()) # get_best_offset(offset_counts, window_size = 1)
        match_scores[song_title] = best_offset_count

    return match_scores

def get_best_offset(offset_counter, window_size=1):
    offsets = sorted(offset_counter.keys())
    best_score = 0
    for i, center in enumerate(offsets):
        window_sum = sum(offset_counter[o] for o in offsets if abs(o - center) <= window_size)
        if window_sum > best_score:
            best_score = window_sum
    return best_score

# Noisy Audio Signal
def plot_matches(wav_file, config, highlighted_song : Optional[str] = None, add_noise = False, offset=False):

    if add_noise:
        utils.add_noise(wav_file, "snippets/noisyinput.wav", snr_db = 10)
        clipHash = audioprts.clip2hash("snippets/noisyinput.wav", config)
    else:
        clipHash = audioprts.clip2hash(wav_file, config)

    if offset:
        matchedsongs = asyncio.run(find_matches_with_offset(clipHash))
    else:
        matchedsongs = asyncio.run(find_matches(clipHash))

    colors = ['r' if song == highlighted_song else 'g' for song in matchedsongs.keys()]
    # print(matchedsongs)

    plt.bar(matchedsongs.keys(), matchedsongs.values(), color=colors)
    plt.ylabel("Matches")
    plt.tick_params(axis='x', labelrotation=90, labelsize=9)

    print(max(matchedsongs, key=matchedsongs.get))
    plt.subplots_adjust(bottom=0.6)
    plt.show()

def plot_offset_histogram(clipHash, target_song, offset_bin_size=0.5):
    from collections import defaultdict
    import asyncio

    offset_counts = defaultdict(int)  # offset -> count

    async def compute_offsets():
        for key, clip_metadata_list in clipHash.items():
            try:
                documents = await collection.find_one({"_id": str(key)})

                if documents is not None:
                    for clip_meta in clip_metadata_list:
                        clip_time = clip_meta["anchor_time"]

                        for song_list in documents["metadata"]:
                            for song_meta in song_list:
                                song_title = song_meta["song title"]
                                if song_title == target_song:
                                    song_time = song_meta["anchor_time"]
                                    offset = round((song_time - clip_time),2 )
                                    offset_counts[offset] += 1

            except Exception as e:
                print(f"No Key in Library {key} - {e}")

    asyncio.run(compute_offsets())

    # Sort and plot
    sorted_offsets = sorted(offset_counts.items())
    offsets, counts = zip(*sorted_offsets) if sorted_offsets else ([], [])

    plt.figure(figsize=(10, 4))
    plt.bar(offsets, counts, width=offset_bin_size * 0.9, color='Blue')
    plt.xlabel("Offset Time (s)")
    plt.ylabel("Match Count")
    plt.title(f"Offset Time Match Distribution for: {target_song}")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.show()


if __name__ == "__main__":
    config = library.get_config()

    plot_matches(
        wav_file=config.snippet,
        config=config,
        highlighted_song=config.highlight,
        offset=config.offset,
        add_noise=config.noise
    )


    plot_matches(wav_file= "snippets/perfect.wav", config=config, offset=True, add_noise=False)