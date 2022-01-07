import argparse

import os
from shutil import which
from glob import glob
import subprocess
     
if which('essentia_streaming_extractor_music') is None:
    raise FileNotFoundError('Essentia\'s essentia_streaming_extrator_music is not found in PATH')

parser = argparse.ArgumentParser(description='Eurovision Data Compute Audio Features')
parser.add_argument('--start', type=int, default=1956,
                    help='Start year range of the Eurovision Song Contest')
parser.add_argument('--end', type=int, default=2021,
                    help='End year range of the Eurovision Song Contest')
args = parser.parse_args()

audio_dir  = "audio"

start_year = int(args.start)
end_year   = int(args.end)


years = [d for d in os.listdir(audio_dir) if os.path.isdir(os.path.join(audio_dir, d))]

sorted_years = sorted(years)

opt_filtered_sorted_years = []

for y in sorted_years:
     
     if (start_year is not None) and int(y) < start_year:
          continue
     
     if (end_year is not None) and int(y) > end_year:
          continue

     opt_filtered_sorted_years.append(y)

for year in opt_filtered_sorted_years:
#     print("  " + year)


    files = glob('audio/'+str(year)+'/*.mp3')
    for f in files:
        output_path = os.path.join(os.path.splitext(f)[0] + '.json')
        print(output_path)
        if not os.path.exists(output_path):
            print('Extracting audio features from {}'.format(f))
            subprocess.call(['essentia_streaming_extractor_music', f, output_path, "essentia.profile"])
