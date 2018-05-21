#!/bin/bash
filename=$(basename "$1")
wget "$1"
mp4_filename="cache/${filename%.*}.mp4"
ffmpeg -i $filename "$mp4_filename"
rm $filename