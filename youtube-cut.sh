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
	
ffmpeg -n -i $filename -ss $2 -to $3 -c copy -copyts "cache/${outputname}.mp4"
ffmpeg -err_detect ignore_err -i "cache/${outputname}.mp4" -c copy "cache/${outputname}fixed.mp4"
rm "cache/${outputname}.mp4"