#!/bin/bash
#
# pregrade.sh
# Script to run prior to grading a student's lab.
#
homedir=$1
destdir=$2
cd $homedir/$destdir

# Run reference extraction on the student's stego.wav file to check if it was successfully embedded
if [ -f stego.wav ]; then
    python3 /home/instructor/.local/instr_config/dsss_solution.py extract --stego stego.wav --bits 32 --seed 1234 --out check_stego.txt 2>/dev/null
fi
