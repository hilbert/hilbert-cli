#!/bin/bash

sudo dnf info hilbert-cli
sudo dnf info hilbert-testapp

sudo dnf -y remove hilbert-cli hilbert-testapp # || exit $?
sudo dnf -y remove hilbert-testapp # || exit $?
sudo dnf -y remove hilbert-cli  # || exit $?

rpmbuild -ba ./SPECS/hilbert-cli.spec || exit $?
rpmbuild --target noarch -ba ./SPECS/hilbert-testapp.spec || exit $?

sudo dnf -y install './RPMS/x86_64/hilbert-cli-0.9.0-2.fc24.x86_64.rpm' || exit $?
sudo dnf -y install './RPMS/x86_64/hilbert-cli-0.9.0-2.fc24.x86_64.rpm' || exit $?
sudo dnf -y install './RPMS/noarch/hilbert-testapp-0.9.0-2.fc24.noarch.rpm' || exit $?
sudo dnf -y install './RPMS/noarch/hilbert-testapp-0.9.0-2.fc24.noarch.rpm' || exit $?


sudo dnf info hilbert-cli
sudo dnf info hilbert-testapp

