#!/bin/bash

while true; do	
	if ! pgrep python2; then
		git pull && python2 start.py
	fi
sleep 1s
done