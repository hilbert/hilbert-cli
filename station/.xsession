#! /bin/bash

echo DISPLAY: $DISPLAY
echo WINDOWPATH: $WINDOWPATH
echo XAUTHORITY: $XAUTHORITY
echo

export
echo 
declare -p
echo
env
echo
set
echo

xhost + || exit $?
xset s off -dpms || exit $?
xset q

ps auwwwxf
docker ps -a
docker images -a

echo "=============== ALSA AUDIO ==============="
alsa-info.sh --no-upload --stdout --with-devices --with-dmesg --with-aplay --with-amixer --with-alsactl --with-configs 

# unset DISPLAY 
if [ -r /etc/profile.d/pa_system-env.sh ]; then 
  . /etc/profile.d/pa_system-env.sh
fi

if [ -n "${PULSE_SERVER}" ]; then
  echo "=============== PULSEAUDIO ==============="

  echo "PA Server: '${PULSE_SERVER}', Cookie: '${PULSE_COOKIE}'"

  sudo pactl info
  sudo pactl list 

  #sudo pactl set-card-profile 0 "output:analog-stereo"
  #sudo pactl set-sink-port 0 "analog-output-headphones"

  # Note: the following tries to workaround the plugged-in headphones issue...
  sudo alsactl restore
  sudo pactl suspend-sink 0 1
  sudo pactl suspend-sink 0 0
  sudo alsactl restore

  sudo pactl set-sink-volume 0 "50%"
  sudo pactl set-source-volume 0 "100%"
fi

if [ -r /etc/profile.d/hilbert-env.sh ]; then 
  . /etc/profile.d/hilbert-env.sh
fi

export HILBERT_STATION="${HILBERT_STATION:-hilbert-station}"

${HILBERT_STATION} -vV

${HILBERT_STATION} -v list_services
${HILBERT_STATION} -v list_applications

${HILBERT_STATION} -v init || echo "Hilbert: 'init' failed with error code: $?"
${HILBERT_STATION} -v start || echo "Hilbert: 'start' failed with error code: $?"

# openbox # NOTE: uncomment if WM is required

# Endless loop (only remote control is expected)
while : 
do
#  ls -la /dev/pts/ptmx
  sudo chmod a+rw /dev/pts/ptmx # || exit $?
  sudo chvt 7 || exit $? # NOTE: compare with nodm.conf!

  sleep 120
done

exit 0
# exec $HOME/bin/store_wait.sh

