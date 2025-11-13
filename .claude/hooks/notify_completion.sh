#!/bin/bash
# Sends a notification when Claude finishes responding

TOPIC="junior-glacier-dialectical-tazmania"
MESSAGE="${1:-Task completed}"

curl -s -d "$MESSAGE" "ntfy.sh/$TOPIC" > /dev/null 2>&1
