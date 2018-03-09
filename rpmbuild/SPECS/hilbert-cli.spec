####%define user          imaginary
%global debug_package %{nil}
%define origname      hilbert-cli
%define user          kiosk
# ur
# %define _prefix      /scratch/home/%{user}
%define _prefix      /opt/%{origname}
# /home/%{user}
%define _bin_dir     %{_prefix}/bin
%define _cfg_dir     %{_prefix}/share/%{origname}
# /scratch/home/%{user}/.config/hilbert-station/


%define buildroot %{_topdir}/%{origname}-%{version}
# BuildRoot:      %{buildroot}
Summary:        Hilbert: client-side tools with a basic minimal configuration
Name:           hilbert-cli
Version:        0.9.1

License:        Apache License, Version 2.0
Release:        8%{?dist}

URL:            https://github.com/hilbert/%{origname}
Source0:        https://cloud.imaginary.org/index.php/s/WSGU4yEaR4RaH3T/download?path=%2F&files=hilbert-cli.tar.gz
# hilbert-cli.tar.gz
# v%{version}.tar.gz
# https://github.com/hilbert/hilbert-cli/archive/v%{version}.tar.gz
Source1:        https://cloud.imaginary.org/index.php/s/WSGU4yEaR4RaH3T/download?path=%2F&files=hilbert-compose-customizer.tar.gz
# hilbert-compose-customizer.tar.gz
Source2:        https://cloud.imaginary.org/index.php/s/WSGU4yEaR4RaH3T/download?path=%2F&files=docker-compose.tar.gz
# docker-compose.tar.gz

#hilbert-default-config.tar.gz
#Source2:        station.cfg

#BuildRequires:  # gettext?

BuildRequires:  bash

Requires:       bash
Requires:       util-linux
Requires:       docker-engine
#Requires:       nodm

## Any Architectur!?

# Prefix:         %{_prefix}
# /home/ur
# ~/

# Group:          Development/Tools

#### Moreover %{user} has to be already pre-configured before installing this package!
%description
Hilbert: client side tools + minimal configuration

NOTE: ATM Requires internet connection to GitHub to download docker-compose 1.13.0 binary bundle. 


%prep
## pwd ; ls -la ; echo $RPM_BUILD_ROOT ; echo %{buildroot}; export 
rm -rf $RPM_BUILD_ROOT

#%setup
%setup -c -a 0
%setup -D -a 1
%setup -D -a 2

##%%%%setup -T -D -a 1
##%%autosetup
##%%patch

%build
##%%configure
##%%make_build

%install
# pwd ; ls -la


# Install Hilbert Client-tools into a separate location
mkdir -p "%{buildroot}/%{_bin_dir}/" || exit $?
cp tools/hilbert-station station/docker-gc "%{buildroot}/%{_bin_dir}/"  || exit $?
# station/generate_ogl.sh station/get-compose.sh 

# Make sure that 
# 1. hilbert-station and docker-compose can be found in the PATH
# 2. corresponding variables: HILBERT_STATION & DOCKER_COMPOSE are set accordingly
mkdir -p "%{buildroot}/etc/profile.d/"
cp station/etc/profile.d/hilbert-env.sh "%{buildroot}/etc/profile.d/"

# Copy minimal sample configuration + sample xsession
mkdir -p "%{buildroot}/%{_cfg_dir}/"
#cp -R station/station_configs/minimal "%{buildroot}/%{_cfg_dir}/"
cp station/.xsession "%{buildroot}/%{_cfg_dir}/"

mkdir -p "%{buildroot}/etc/tmpfiles.d/"
echo "D /var/run/hilbert 0755 %{user} %{user} - " > "%{buildroot}/etc/tmpfiles.d/hilbert.conf"


# OGL will be a separate story!
#!# cp OGL.tgz %{buildroot}/%{_cfg_dir}/

# Install NODM-related files
#!!# cp -R station/etc %{buildroot}/etc/
#!!# mv %{buildroot}/etc/nodm.conf %{buildroot}/etc/nodm.kiosk.xsession.conf
#!!# cp station/.xsession %{buildroot}/%{_cfg_dir}/../../

#sudo -g %{user} -u %{user} HILBERT_CONFIG_BASEDIR=%{buildroot}/%{_cfg_dir}/ -i %{buildroot}/%{_bin_dir}/hilbert-station -vv init 
#chown -R %{user}:%{user} %{buildroot}/%{_cfg_dir}/../../

cp hilbert-compose-customizer "%{buildroot}/%{_bin_dir}/" || exit $?
cp docker-compose "%{buildroot}/%{_bin_dir}/" || exit $?

##%%make_install

%files
%doc README.md CHANGELOG.md
#%doc doc/*.html
#%doc doc/*.jpg
#%doc doc/*.css
##%%config(noreplace) docker-compose.yml
%{_bindir}/
/etc/
##%%{_prefix}/share/icecast/*
## %defattr(-,%{user},%{user})
%{_cfg_dir}/
# %license LICENSE
# %doc add-docs-here

%clean
rm -rf $RPM_BUILD_ROOT

%post

#docker load -i %{_cfg_dir}/configs/image
# rm -f %{_cfg_dir}/configs/image

## TODO: use random temporary directory instead of /tmp/minimal or /tmp/testapp!
#sudo -g %{user} -u %{user} bash -c "cp -R %{_cfg_dir}/minimal /tmp/" && \
#sudo -g %{user} -u %{user} DOCKER_COMPOSE=%{_bin_dir}/docker-compose %{_bin_dir}/hilbert-station -q init /tmp/minimal || echo "Sorry: something failed during initialization!"
#rm -Rf /tmp/minimal

##cd /tmp/ && (echo "0"; echo) | %{_bin_dir}/generate_ogl.sh && \
##sudo -g %{user} -u %{user} bash -c "cd; cp /tmp/OGL.tgz .config/hilbert-station"
##rm -Rf /tmp/OGL.tgz
##docker rmi hilbert/dummy:latest

#mv /etc/nodm.conf /etc/nodm.conf.original.save
#cp /etc/nodm.kiosk.xsession.conf /etc/nodm.conf || exit 1
#systemctl enable nodm.service || exit 1

%postun
# docker rmi hello-world:latest

%changelog
* Thu Mar 8 2018 Alex
- major update of CLI tools (e.g. hilbert-station)
- update of hilbert-compose-customizer (to detect all video devices in /dev/dri)
- update of docker-compose, docker-gc

* Sun Oct 1 2017 Alex
- Updated hilbert-station to avoid unnecessary output from `docker pull` 
- Updated hilbert-compose-customizer to workaround nvidia-docker issue with the host networking driver/mode

* Tue Jul 18 2017 Alex
- Updated hilbert-station + added hilbert-compose-customizer


* Fri May  5 2017 Alex
- Fixed and updated hilbert-cli tools


* Tue Apr  4 2017 Alex
- Initial version of RPM .spec

