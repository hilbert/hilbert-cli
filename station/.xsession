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


if [ -r /etc/profile.d/hilbert-env.sh ]; then 
  . /etc/profile.d/hilbert-env.sh
fi

export HILBERT_STATION="${HILBERT_STATION:-hilbert-station}"

${HILBERT_STATION} -vV

${HILBERT_STATION} -v list_services
${HILBERT_STATION} -v list_applications

${HILBERT_STATION} -v init || exit $?
${HILBERT_STATION} -v start || exit $?
#autostart.sh || exit $?


sudo chvt ${XDG_VTNR}

# Endless loop (only remote control is expected)
while : 
do
#  ls -la /dev/pts/ptmx
  sudo chmod a+rw /dev/pts/ptmx # || exit $?
  sudo chvt ${XDG_VTNR} || exit $? # NOTE: compare with nodm.conf!

  sleep 120
done

exit 0
# exec $HOME/bin/store_wait.sh
