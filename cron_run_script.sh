#!/bin/bash

program_name="fids-bird-detection-an-tracking"
script_path=`dirname $(realpath $0)`
python_interpreter_path="/home/fids/.local/share/virtualenvs/fids_bird_detection_and_tracking-igiTmoPq/bin/python"

mkdir -p "$HOME/tmp"
mkdir -p "$HOME/.birdwatchpy"
PIDFILE="$HOME/tmp/$program_name.pid"

if [ -e "${PIDFILE}" ] && (ps -u $(whoami) -opid= |
                           grep -P "^\s*$(cat ${PIDFILE})$" &> /dev/null); then
  echo "Already running."
  exit 99
fi

echo $script_path
cd $script_path
export DISPLAY=:0.0
echo $!
"$python_interpreter_path" -m birdwatchpy.StreamReceiver --type stream  &> "$HOME/.birdwatchpy/fids_bird_detection_and_tracking_start_script.log" &

echo $! > "${PIDFILE}"
chmod 644 "${PIDFILE}"
