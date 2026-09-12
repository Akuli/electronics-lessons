#!/bin/bash

set -e

if [ $# != 2 ]; then
    echo "Usage: $0 <input_file> <output_file>"
    exit 2
fi

set -x
ffmpeg -i "$1" -c:v libx264 -crf 23 -preset slow -vf "scale=-2:1080" -c:a aac -b:a 128k -movflags +faststart "$2"
