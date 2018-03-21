#!/bin/bash

while true; do	
	if ! pgrep python; then
		git pull && python start.py 
	fi
sleep 1s
done