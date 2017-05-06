# nodm/X11 configuration

0. install `hilbert-cli` and some station configration (e.g. `hilbert-testapp`)
1. install `nodm` package
2. copy our custom [`etc/nodm.conf`](etc/nodm.conf) over the default one `/etc/nodm.conf`
3. copy our [`etc/pam.d/nodm`](etc/pam.d/nodm) into `/etc/pam.d`
4. make sure that our custom [`.xsession`](.xsession) is available on the system (see [`etc/nodm.conf`](etc/nodm.conf))
5. enable nodm startup: `sudo systemctl enable nodm.service`. NOTE: no other DM should be enabled beforehand!
6. check its status: `sudo systemctl status nodm.service`
