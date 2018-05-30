#!/bin/bash
filename=$(basename "$1")
ffmpeg -i  $1 "cache/${filename%.*}.mp4"