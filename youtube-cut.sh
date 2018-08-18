#!/bin/bash

filename="youtube/$(basename "$1")-no-audio.mp4"
audio="135"

if [[ $4 == "-a" ]]; then
	filename="youtube/$(basename "$1").mp4"
	audio="22"
fi

outputname="$(md5sum <<< ${2}_${3}${filename})"
outputname="${outputname:0:32}"

if [[ ! -f $filename ]]; then
	youtube-dl -f $audio $1 -o $filename
fi
	
ffmpeg -n -ss $2 -i $filename -c copy -t $3 "cache/${outputname}.mp4"
