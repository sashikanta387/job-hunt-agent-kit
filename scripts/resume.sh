#!/bin/bash
# Resume the resume refresh jobs after scripts/pause.sh.
source "$(dirname "$0")/lib.sh"
rm -f "$KIT/PAUSED"
echo "Resumed. Sessions may have expired while paused: run scripts/login.sh <portal> if you get a sign-in notification."
