#!/bin/bash

find audio/ -type f -name "*.json" > af_json_files.list \
    && tar -cvzf audio--essentia-json-files.tar.gz --files-from ./af_json_files.list \
    && /bin/rm af_json_files.list
