# A simple audio merging
Sometimes I like to download my songs localy, as it can be a lot of songs, I decided to create this tool for merging faster.

As I tried to merge more and more songs, I needed to use different features here.
I have used uv for package installer.

## How to use?
1. Clone this repository, take a look at [required dependencies](pyproject.toml)
2. Put yout songs inside the songs directory
3. run main.py

#### main.py has some parameters:
- song_dir: Directory containing the audio files
- output_file: Name of the output file
- max_workers: Maximum number of parallel processes (None = automatic)
- bitrate: Quality of the final MP3 (default: "192k")
- target_sample_rate: Desired sample rate (default: 44100Hz)
- target_channels: Number of audio channels (1=mono, 2=stereo)
