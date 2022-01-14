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

aid_clientid_filename="acousticid_clientid.txt"
if not os.path.isfile(aid_clientid_filename):
    print(f"Failed to find: {aid_clientid_filename}")
    print(f"Have you copied over {aid_clientid_filename}.in and then edited the 'CHANGEME' content?")
    sys.exit(1)
    
fin = open(aid_clientid_filename,"r")
aid_clientid = fin.read().strip()
fin.close()

if aid_clientid == "CHANGEME":
    print("AcousticID client-id was 'CHANGEME'")
    print(f"Have you registered an app via https://acousticid.biz and then updated {aid_clientid_filename} to contain that value?")
    print("Continuing anyway, however it is likely the AcousticID API calls will fail")


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

    prev_time_msecs = None
    
    for mp3_filename in mp3_files:
        src_json_filename = mp3_filename.replace(".mp3",".json")
        dst_json_filename = src_json_filename.replace(".json","-musicbrainz.json")

        match = re.search(r"^audio/(\d{4})/([^_]+)_([^_]+)_([^_]+)\.json$",src_json_filename)
          
        if match:
            year    = match.group(1)
            country = match.group(2)
            title   = match.group(3) # unused
            artist  = match.group(4) # unused
        
        if not os.path.exists(dst_json_filename):
            print(f"Querying for AcousticBrainz ID match on chromaprint fingerprint: {src_json_filename}");

            fin = open(src_json_filename)
            essentia_features = json.load(fin);
            fin.close()

            chromaprint = essentia_features["chromaprint"]["string"][0]
            chromaprint_intdur = int(essentia_features["chromaprint"]["duration"])

            #####
            # ****** Change the entry in acousticid_clientid.txt to your actual client-id
            #####
            acousticid_get_args = [f"client={aid_clientid}","meta=releasegroup",
                                   f"duration={chromaprint_intdur}",f"fingerprint={chromaprint}"];

            acousticid_url = "https://api.acoustid.org/v2/lookup?" + "&".join(acousticid_get_args)



            curr_time_msecs = time.time_ns() // 1_000_000

            # can only query acoustic-id 3 time per sec
            # print(f"current time msecs = {curr_time_msecs}, prev time msecs = {prev_time_msecs}")
            sleep_msecs = 334 - (curr_time_msecs - prev_time_msecs) if not prev_time_msecs is None else 0
            
            if (sleep_msecs>0):
                sleep_secs = 0.001 * sleep_msecs
                print("Inserting throtling delay: %.3f seconds" % sleep_secs)
                time.sleep(sleep_secs)
            
            response = requests.get(acousticid_url);

            # Made an API call, so update timing info
            prev_time_msecs = curr_time_msecs

            jsonResponse = response.json();
            results = jsonResponse["results"]

            id = None
            for r in results:
                if r["id"]:
                    id=r["id"]
                    break

            if id is not None:
                score = r["score"]
                print(f"Found id = {id} with confidence score of {score}")


                # metadata.json format
                # {
                #    "DirectoryMetadata": [
                #        {
                #            "FileSet": [
                #                {
                #                    "FileName": "Netherlands1975\\.nul"
                #                },
                #                {
                #                    "Description": {
                #                        "Metadata": [
                #                            {
                #                                "name": "musicbrainz.id",
                #                                "content": "f668ff8d-797d-48b5-bb14-54675de19a35"
                #                            }
                #                        ]
                #                    }
                #                }
                #            ]
                #        }
                #    ]
                # }

                filename_re = f"{country}{year}\\.nul"
                metadata_id    = { "name" : "musicbrainz.id", "content": id }
                metadata_score = { "score": "musicbrainz.id", "content": score }
                
                metadata_json = {}
                metadata_json["DirectoryMetadata"] = [ {
                    "FileSet": { "FileName": filename_re },
                    "Description" : { "Metadata" : [ metadata_id, metadata_score ] }
                } ]
                
                fout = open(dst_json_filename,"w")
                json.dump(metadata_json,fout)
                # print("**** = " + repr(metadata_json))
                fout.close()
                
            
        else:
            print(f"{dst_json_filename} already exists => Skipping")


