#!/bin/bash
. venv/bin/activate
while true; do	
	if ! pgrep python; then
		git pull && python2 start.py
	fi
sleep 2s
done
