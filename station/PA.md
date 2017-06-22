# Sound/PulseAudio configuration

NOTE: do the following **before** starting`hilbert-cli` and NoDM

1. install the following packages with the minimal required dependencies:
   `pulseaudio`, `alsa-utils`, `alsa-plugins-pulseaudio`, 
   `pulseaudio-utils`, `pulseaudio-libs`, `alsa-lib`
2. add users to groups as follows:
```
sudo usermod -aG audio pulse
sudo usermod -aG audio kiosk
sudo usermod -aG audio root
sudo usermod -aG pulse-access kiosk
sudo usermod -aG pulse-access root
```
3. copy our custom configs [`etc/pulse`](etc/pulse) over the default ones `/etc/pulse`
  * NOTE: System-Wide PulseAudio server socket: `/var/run/pulse/native` 
4. copy our custom systemd unit [`etc/systemd/system/pulseaudio.service`](etc/systemd/system/pulseaudio.service) into `/etc/systemd/system/`
5. copy our script [`etc/profile.d/pa_system-env.sh`](etc/profile.d/pa_system-env.sh) into `/etc/profile.d/`
6. enable PulseAudio system startup: `sudo systemctl --system enable pulseaudio.service`. 
  * NOTE: no other application should have started pulseaudio server until this point
7. if necesssary start PulseAudio server right now: `sudo systemctl --system start pulseaudio.service`. 
8. check its status: `sudo systemctl --system status pulseaudio.service`
