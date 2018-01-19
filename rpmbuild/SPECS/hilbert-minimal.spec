#%define user          imaginary
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

#%define buildroot %{_topdir}/%{origname}-%{version}
#BuildRoot:      %{buildroot}
Summary:        TestApp: Hilbert's minimal (empty) configuration
Name:           hilbert-minimal
Version:        0.9.0

License:        Apache License, Version 2.0
Release:        1%{?dist}

URL:            https://github.com/hilbert/%{origname}
Source:         %{origname}.tar.gz
# v%{version}.tar.gz
# https://github.com/hilbert/hilbert-cli/archive/v%{version}.tar.gz
#Source1:        OGL.tgz.tar.gz

#hilbert-default-config.tar.gz
#Source2:        station.cfg

#BuildRequires:  # gettext?

Requires:       bash
Requires:       util-linux
#Requires:       docker-engine
Requires:       %{origname}

## Any Architectur!?

# Prefix:         %{_prefix}
# /home/ur
# ~/

# Group:          Development/Tools

%description
Empty minimal Hilbert's station configuration

%prep
## echo 0 ; pwd ; ls -la ; echo $RPM_BUILD_ROOT ; export 

# mkdir hilbert-testapp-%{version}

rm -rf $RPM_BUILD_ROOT

%setup -c
# -a 0
#?# %setup -a 1
##%%%%setup -T -D -a 1
##%%autosetup
##%%patch

%build
##%%configure
##%%make_build

%install
## rm -rf $RPM_BUILD_ROOT

# Install Hilbert Client-tools into a separate location
#mkdir -p %{buildroot}/%{_bin_dir}/
#cp tools/hilbert-station station/{docker-gc,generate_ogl.sh,get-compose.sh} %{buildroot}/%{_bin_dir}/

# Make sure that 
# 1. hilbert-station and docker-compose can be found in the PATH
# 2. corresponding variables: HILBERT_STATION & DOCKER_COMPOSE are set accordingly
#mkdir -p %{buildroot}/etc/profile.d/
#cp station/etc/profile.d/hilbert-env.sh %{buildroot}/etc/profile.d/

## pwd

# Copy sample configs + sample xsession
mkdir -p $RPM_BUILD_ROOT/%{_cfg_dir}/
#cd hilbert-cli-0.9.0/
cp -R station/station_configs/minimal $RPM_BUILD_ROOT/%{_cfg_dir}/
#cp station/.xsession %{buildroot}/%{_cfg_dir}/

# OGL will be a separate story!
#!# cp OGL.tgz %{buildroot}/%{_cfg_dir}/

# Install NODM-related files
#!!# cp -R station/etc %{buildroot}/etc/
#!!# mv %{buildroot}/etc/nodm.conf %{buildroot}/etc/nodm.kiosk.xsession.conf
#!!# cp station/.xsession %{buildroot}/%{_cfg_dir}/../../

#sudo -g %{user} -u %{user} HILBERT_CONFIG_BASEDIR=%{buildroot}/%{_cfg_dir}/ -i %{buildroot}/%{_bin_dir}/hilbert-station -vv init 
#chown -R %{user}:%{user} %{buildroot}/%{_cfg_dir}/../../

#BASE=$PWD
#cd %{buildroot}/%{_bin_dir}/
#./get-compose.sh || exit 1 
#unlink ./compose
#cd $BASE


##%%make_install

%files
#%doc README.md CHANGELOG.md
#%doc doc/*.html
#%doc doc/*.jpg
#%doc doc/*.css
##%%config(noreplace) docker-compose.yml
#%{_bindir}/
#/etc/
##%%{_prefix}/share/icecast/*

## %defattr(-,%{user},%{user})
%{_cfg_dir}/

# %license LICENSE
# %doc add-docs-here


%clean
#echo 00
#rm -rf $RPM_BUILD_ROOT
#echo 11

%post

#docker load -i %{_cfg_dir}/configs/image
# rm -f %{_cfg_dir}/configs/image

## TODO: use random temporary directory instead of /tmp/minimal!
sudo -g %{user} -u %{user} bash -c "cp -R %{_cfg_dir}/minimal /tmp/" && \
sudo -g %{user} -u %{user} DOCKER_COMPOSE=%{_bin_dir}/docker-compose %{_bin_dir}/hilbert-station -q init /tmp/minimal || echo "Sorry: something failed during initialization!"
rm -Rf /tmp/minimal

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
* Mon Dec 4 2017 Alex
- Initial version of RPM .spec for minimal Hilbert configuration

