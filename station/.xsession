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

xhost +local: || exit $? # TODO	

xset s off -dpms || exit $?
xset q

lsblk -a -O

ps auwwwxf

sudo systemctl status --system
sudo systemctl status --system pulseaudio.service

echo "=============== ALSA AUDIO ==============="
alsa-info.sh --no-upload --stdout --with-devices --with-dmesg --with-aplay --with-amixer --with-alsactl --with-configs 
#lspci | grep -i audio
#cat /proc/asound/cards

# unset DISPLAY 

if hash amixer 2>/dev/null; then
  amixer
  sudo alsactl restore
  amixer
  amixer sset 'Capture' 0 mute
  amixer sset 'Master' "100%" unmute nocap
  sudo alsactl store
 
  for ALSA_CARD in $(cat /proc/asound/cards | grep -E '^ *[0-9]+ ' | sed -e 's@^ *@@g' -e 's@ .*$@@g'); 
  do
    echo "Card: ${ALSA_CARD}"

    amixer -c "${ALSA_CARD}"
    sudo alsactl restore "${ALSA_CARD}"
    amixer -c "${ALSA_CARD}"

    amixer -c "${ALSA_CARD}" -- sset 'Capture' 0 mute
    amixer -c "${ALSA_CARD}" -- sset 'Master' "100%" unmute nocap
    amixer -c "${ALSA_CARD}" -- sset 'Auto-Mute Mode' 'Disabled' 
    amixer -c "${ALSA_CARD}" -- sset 'Loopback Mixing' 'Enabled'

    for CTL in "Beep" "Speaker" "Speaker+LO"; 
    do
      amixer -c "${ALSA_CARD}" -- sset "${CTL}" 0 mute nocap
    done

    for CTL in "Line Out" "PCM" "Headphone" "Digital"; 
    do
      amixer -c "${ALSA_CARD}" -- sset "${CTL}" "100%" unmute nocap
    done


    sudo alsactl store "${ALSA_CARD}"
  done
fi

if [ -r /etc/profile.d/pa_system-env.sh ]; then 
  . /etc/profile.d/pa_system-env.sh
fi

if [ -n "${PULSE_SERVER}" ]; then
  echo "=============== PULSEAUDIO ==============="

  echo "PA Server: '`ls -la ${PULSE_SERVER}`', Cookie: '${PULSE_COOKIE}'"

  sudo pactl info
  sudo pactl list 

  #sudo pactl set-card-profile 0 "output:analog-stereo"
  #sudo pactl set-sink-port 0 "analog-output-headphones"

  # Note: the following tries to workaround the plugged-in headphones issue...
  sudo pactl suspend-sink 0 1
  sudo pactl suspend-sink 0 0

  sudo pactl set-sink-volume 0 "50%"
  sudo pactl set-source-volume 0 "100%"


fi

sudo systemctl status --system docker.service

ls -la /var/run/docker*

docker -D version
docker -D info
docker -D ps -a
docker -D stats -a --no-stream
docker -D images -a
docker -D volume ls

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

