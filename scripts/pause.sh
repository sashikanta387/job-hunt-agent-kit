#!/bin/bash
# Pause all resume refresh jobs (e.g. once you've accepted an offer). Jobs stay scheduled but do nothing.
source "$(dirname "$0")/lib.sh"
mkdir -p "$KIT" && date > "$KIT/PAUSED"
echo "Paused ($KIT/PAUSED). Also disable the three Claude scheduled tasks. Undo with scripts/resume.sh"
