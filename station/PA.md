# Sound/PulseAudio configuration

NOTE: please check the audio-related BIOS settings beforehand (e.g. disable Microphone, Speakers etc. if possible)

NOTE: do the following **before** starting`hilbert-cli` and NoDM

1. install the following packages with the minimal required dependencies:
   `pulseaudio`, `alsa-utils`, `alsa-plugins-pulseaudio`, 
   `pulseaudio-utils`, `pulseaudio-libs`, `alsa-lib`
```
sudo dnf install pulseaudio alsa-utils alsa-plugins-pulseaudio pulseaudio-utils pulseaudio-libs alsa-lib
```

2. add users to groups as follows:
```
sudo usermod -aG audio pulse
sudo usermod -aG audio kiosk
sudo usermod -aG audio root
sudo usermod -aG pulse-access kiosk
sudo usermod -aG pulse-access root
```
3. copy one of custom config folders [`etc/pulse.micro/*`](etc/pulse.micro) or [`etc/pulse.tower/*`](etc/pulse.tower) (depending of PC type) over the default ones `/etc/pulse`
  * NOTE: System-Wide PulseAudio server socket: `/var/run/pulse/native` 
4. copy our custom systemd unit [`etc/systemd/system/pulseaudio.service`](etc/systemd/system/pulseaudio.service) into `/etc/systemd/system/`
5. copy our script [`etc/profile.d/pa_system-env.sh`](etc/profile.d/pa_system-env.sh) into `/etc/profile.d/`
6. enable PulseAudio system startup: `sudo systemctl --system enable pulseaudio.service`. 
  * NOTE: no other application should have started pulseaudio server until this point
7. if necesssary start PulseAudio server right now: `sudo systemctl --system start pulseaudio.service`. 
8. check its status: `sudo systemctl --system status pulseaudio.service`

NOTE: it may be also necessary to put [`.asoundrc`](.asoundrc) into `$KIOSK_HOME` and [`etc/asound.conf`](etc/asound.conf) into `/etc/`

NOTE: default ALSA settings are set in [`.xsession`](.xsession). 
It may be worth to do the following during the setup instead:

```
  amixer sset 'Capture' 0 mute
  amixer sset 'Master' "100%" unmute nocap
  sudo alsactl store
 
  for ALSA_CARD in $(cat /proc/asound/cards | grep -E '^ *[0-9]+ ' | sed -e 's@^ *@@g' -e 's@ .*$@@g'); 
  do
    echo "Card: ${ALSA_CARD}"

    amixer -c "${ALSA_CARD}" -- sset 'Capture' 0 mute
    amixer -c "${ALSA_CARD}" -- sset 'Auto-Mute Mode' 'Disabled' 
    amixer -c "${ALSA_CARD}" -- sset 'Loopback Mixing' 'Enabled'

    for CTL in "Beep" "Speaker" "Speaker+LO"; 
    do
      amixer -c "${ALSA_CARD}" -- sset "${CTL}" 0 mute nocap
    done

    amixer -c "${ALSA_CARD}" -- sset 'Master' "100%" unmute nocap
    for CTL in "Line Out" "PCM" "Headphone" "Digital"; 
    do
      amixer -c "${ALSA_CARD}" -- sset "${CTL}" "100%" unmute nocap
    done

    sudo alsactl store "${ALSA_CARD}"
  done
```

NOTE: 
* One can check the ALSA controls visually using `alsamixer`.

* One can check the pulseaudio functioning using `paman` and `pavucontrol` (which may be installed separatly).


