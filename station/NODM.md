# nodm/X11 configuration

0. install `hilbert-cli` and some station configration (e.g. `hilbert-testapp`)
1. install `nodm` package
2. copy our custom [`etc/nodm.conf`](etc/nodm.conf) over the default one `/etc/nodm.conf`
  * NOTE: using `/etc/X11/xinit/Xsession` as `NODM_XSESSION` makes sure that SSH agent is started together with X11 server...
3. copy our [`etc/pam.d/nodm`](etc/pam.d/nodm) into `/etc/pam.d`
4. make sure that our custom [`.xsession`](.xsession) is available on the system (see [`etc/nodm.conf`](etc/nodm.conf))
  * NOTE: `~/.xsession` has to be executable (or a link).
  * NOTE: If you have installed `hilbert-cli` RPM - you can just copy or link `/opt/hilbert-cli/share/hilbert-cli/.xsession` into the home directory
5. enable nodm startup: `sudo systemctl enable nodm.service`. 
  * NOTE: no other DM should be enabled beforehand!
6. start nodm: `sudo systemctl start nodm.service`. 
  * NOTE: will start X11 and the installed hilbert station configuration
7. check its status: `sudo systemctl status nodm.service`
