import argparse

import glob
import json
import os
import re
import requests
import shutil
import sys
import time

# import unicodedata

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
    print("  " + year)
    
    mp3_files = glob.glob(u'audio/'+str(year)+'/*.mp3')

    prev_time_msecs = time.time_ns() // 1_000_000
    
    for mp3_file in mp3_files:
        src_json_file = mp3_file.replace(".mp3",".json")
        dst_json_file = src_json_file.replace(".json","-musicbrainz.json")

        if not os.path.exists(dst_json_file):
            print(f"Querying for AcousticBrainz ID match on chromaprint fingerprint: {src_json_file}");

            fin = open(src_json_file)
            essentia_features = json.load(fin);
            fin.close()

            chromaprint = essentia_features["chromaprint"]["string"][0]
            chromaprint_intdur = int(essentia_features["chromaprint"]["duration"])

            #####
            # ****** Change client=CHANGEME to your actual client-id
            #####
            acousticid_get_args = ["client=CHANGEME","meta=releasegroup",
                                   f"duration={chromaprint_intdur}",f"fingerprint={chromaprint}"];

            acousticid_url = "https://api.acoustid.org/v2/lookup?" + "&".join(acousticid_get_args)



            curr_time_msecs = time.time_ns() // 1_000_000

            # can only query acoustic-id 3 time per sec
            # print(f"current time msecs = {curr_time_msecs}, prev time msecs = {prev_time_msecs}")
            sleep_msecs = 334 - (curr_time_msecs - prev_time_msecs)
            
            if (sleep_msecs>0):
                sleep_secs = 0.001 * sleep_msecs
                print("Inserting throtling delay:" + str(sleep_secs) + " seconds")
                time.sleep(sleep_secs)
            
            response = requests.get(acousticid_url);

            jsonResponse = response.json();
            results = jsonResponse["results"]

            id = None
            for r in results:
                if r["id"]:
                    id=r["id"]
                    break

            if id is not None:
                print("Found id = " + id )
               
            
        else:
            print(f"{src_json_file} already exists => Skipping")


        prev_time_msecs = curr_time_msecs
