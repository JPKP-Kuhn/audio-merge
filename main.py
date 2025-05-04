#!/usr/bin/env python3
import os
import argparse
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from pydub import AudioSegment

def process_song(file_path, target_sample_rate, target_channels, output_dir):
    """
    Processes a single audio file and saves it in temporary format to save memory.
    """
    try:
        # Create a temporary filename in the output directory
        temp_filename = os.path.join(output_dir, f"temp_{os.path.basename(file_path)}")
        
        # Loads and processes the song
        song = AudioSegment.from_file(file_path)
        song = song.set_frame_rate(target_sample_rate).set_channels(target_channels)
        
        # Saves the processed file in the temporary directory
        song.export(temp_filename, format="wav")
        
        # Explicitly free memory
        del song
        return temp_filename
    except Exception as e:
        print(f"Error when processing {file_path}: {e}")
        return None

def combine_audio_files(temp_files, output_file, bitrate="192k"):
    """
    Combines temporary audio files into a single output file,
    without loading them all into memory simultaneously.
    """
    if not temp_files:
        print("None file to merge")
        return False
    
    # Initialize with the first file
    combined = AudioSegment.from_file(temp_files[0])
    
    # Add the rest of the files, one by one
    for i, temp_file in enumerate(tqdm(temp_files[1:], desc="Merging audios")):
        try:
            # Only loads the next segment
            next_segment = AudioSegment.from_file(temp_file)
            combined += next_segment
            
            # Release memory
            del next_segment
            
            # Every 10 files or when the size exceeds 100MB, save and reload
            if (i + 1) % 10 == 0 or len(combined) > 100 * 1024 * 1024:
                tmp_output = f"{output_file}.tmp"
                combined.export(tmp_output, format="mp3", bitrate=bitrate)
                del combined
                combined = AudioSegment.from_file(tmp_output)
                os.remove(tmp_output)
                
        except Exception as e:
            print(f"Error when merging {temp_file}: {e}")
    
    # Exporta o arquivo final
    print("Exporting final file...")
    combined.export(output_file, format="mp3", bitrate=bitrate)
    return True

def get_directory_size(directory):
    """Calculate the total size of a file in MB."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    return total_size / (1024 * 1024)

def combine_songs(song_dir, output_file="combined.mp3", max_workers=None, bitrate="192k", 
                 target_sample_rate=44100, target_channels=2):
    """
    Main function for combining music files.

    Parameters:
    - song_dir: Directory containing the audio files
    - output_file: Name of the output file
    - max_workers: Maximum number of parallel processes (None = automatic)
    - bitrate: Quality of the final MP3 (default: "192k")
    - target_sample_rate: Desired sample rate (default: 44100Hz)
    - target_channels: Number of audio channels (1=mono, 2=stereo)
    """
    # Remove the output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Create a temporary directory to store the processed files
    temp_dir = tempfile.mkdtemp(prefix="audio_process_")
    
    try:
        # List of files in the directory that are audio files
        supported_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac')
        song_files = [
            os.path.join(song_dir, file) for file in os.listdir(song_dir)
            if os.path.isfile(os.path.join(song_dir, file)) and 
            os.path.splitext(file)[1].lower() in supported_extensions
        ]
        
        if not song_files:
            print(f"None audio file was found{song_dir}")
            return
        
        print(f"Found {len(song_files)} audio files to process.")
        
        # Determine the size of the directory to adjust the number of workers
        dir_size = get_directory_size(song_dir)
        print(f"Total size of files: {dir_size:.2f} MB")
        
        # Set the number of workers based on data size and available resources
        if max_workers is None:
            import multiprocessing
            system_cores = multiprocessing.cpu_count()
            # Limit the number of workers to avoid overloading the system
            if dir_size > 1000:  # > 1GB
                max_workers = max(1, system_cores // 2)  # Half the cores for very large files
            elif dir_size > 500:  # > 500MB
                max_workers = max(2, system_cores - 1)  # One less than total cores
            else:
                max_workers = system_cores  # Use all cores for smaller files
        
        print(f"Using {max_workers} process(es) for conversation")
        
        # Process files in parallel
        temp_files = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    process_song, 
                    file, 
                    target_sample_rate, 
                    target_channels,
                    temp_dir
                ) for file in song_files
            ]
            
            # Collect results with progress bar
            for future in tqdm(futures, total=len(song_files), desc="Processando áudios"):
                result = future.result()
                if result:
                    temp_files.append(result)
        
        # Sort temporary files to maintain order
        temp_files.sort()
        
        if combine_audio_files(temp_files, output_file, bitrate):
            print(f"Merged file exported to {output_file}")
        else:
            print("Failed to combine files")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        print("Cleaning up temporary files...")
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine multiple audio files into a single MP3 file.")
    parser.add_argument("--dir", "-d", default="songs/", help="Directory containing audio files")
    parser.add_argument("--output", "-o", default="combined.mp3", help="Output file name")
    parser.add_argument("--workers", "-w", type=int, default=None, help="Number of parallel workers (processes, None = automatic)")
    parser.add_argument("--bitrate", "-b", default="192k", help="Final MP3 Quality (ex: 128k, 192k, 256k)")
    parser.add_argument("--sample-rate", "-s", type=int, default=44100, help="Sample rate (Hz)")
    parser.add_argument("--channels", "-c", type=int, default=2, choices=[1, 2], help="Channels (1=mono, 2=stereo)")
    
    args = parser.parse_args()
    
    combine_songs(
        args.dir, 
        args.output, 
        args.workers, 
        args.bitrate,
        args.sample_rate,
        args.channels
    )