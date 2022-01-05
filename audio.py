import argparse

import os
import subprocess
import pandas as pd
import youtube_dl

parser = argparse.ArgumentParser(description='Eurovision Data Audio Downloader')
parser.add_argument('--start', type=int, default=1956,
                    help='Start year range of the Eurovision Song Contest')
parser.add_argument('--end', type=int, default=2021,
                    help='End year range of the Eurovision Song Contest')
args = parser.parse_args()

year_range = [y for y in range(args.start, args.end+1)]
        
audio_dir = 'audio'
if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)

contestants = pd.read_csv('contestants.csv')
for i, r in contestants.iterrows():
    year = r['year']
    if year not in year_range:
        continue
    
    destination_dir = os.path.join(audio_dir, str(year))
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    youtube_url = r['youtube_url']
    if youtube_url:
        fn = '{}_{}_{}'.format(
            r['to_country'], r['song'], r['performer'])

        # Skip if file already exists
        fp = os.path.join(destination_dir, fn)
        if not os.path.exists(fp + '.mp3'):

            ydl_opts = {
                'outtmpl': fp + '.%(ext)s',
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])
            except Exception as e:
                print(e)
                pass
        else:
            print('{} already exists'.format(fp))
        

        # studio_rec_dir = os.path.join(destination_dir, "studio_recording")
        # if not os.path.exists(studio_rec_dir):
        #     os.makedirs(studio_rec_dir)
        
        # # Additionally, try non-live versions:
        # query = f"{r['song']} {r['performer']}"
        # subprocess.call(["spotdl", "-f", studio_rec_dir, "--song", query])
