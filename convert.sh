#!/bin/bash
cd cache/
filename=$(basename "$1")
wget "$1"
mp4_filename="${filename%.*}.mp4"
ffmpeg -i $filename $mp4_filename
rm $filename