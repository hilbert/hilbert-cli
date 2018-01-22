# Customization for using NVidia GPU from within docker containers

Note that `nvidia-docker-plugin` expects the NVidia drivers and `nvidia-modprobe` to be installed native on the system

1. install `nvidia-docker` (after Docker and NVidia drivers but before `hilbert-cli`) on PCs with Nvidia GPU, e.g. following: [nvidia-docker-centos-instructions](https://github.com/NVIDIA/nvidia-docker#centos-distributions)
2. make sure to enable and start `nvidia-docker` service using `systemctl`, e.g.
```
sudo systemctl --system enable nvidia-docker
sudo systemctl --system start nvidia-docker
```
  * NOTE: if necessary one can run `nvidia-docker-plugin` manually via `sudo -b nohup nvidia-docker-plugin > /tmp/nvidia-docker.log`
3. make sure to run any `nvidia-docker` test at least once before installing `hilbert-cl`, e.g.
```
sudo nvidia-docker run --rm hilbert/gui nvidia-smi
```

4. With a running X11 server (with correct `DISPLAY` variable) one can test the use of OpenGL library as follows: 
```
sudo nvidia-docker run -e DISPLAY -v /tmp/:/tmp/:rw --rm hilbert/gui glxgears -info
```

## Using `nvidia-drivers` (as provided by `nvidia-docker-plugin`) by a docker container

Note that in order to make use of mounted `nvidia-driver` volume - one has to do the following **within** a docker image:
```
echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf
echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf
ldconfig
export PATH="/usr/local/nvidia/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/local/nvidia/lib:/usr/local/nvidia/lib64:${LD_LIBRARY_PATH}"
```

Moreover it is worth adding the following image label `com.nvidia.volumes.needed="nvidia_driver"` in order to make use of `nvidia-docker` CLI wrapper tool.


## Relocation of docker volumes

Note: the docker volume will be created using hard-links which cannot be created over different devices. 
Therefore if `/var` is on a different device than `/` it will be necessary to specify another location for the created volume.
Let us for example put it to `/opt/nvidia-docker-volumes` then we have to prepare it as follows (after installing `nvidia-docker` but **before** starting the service):

```
sudo mkdir -p /opt/nvidia-docker-volumes
sudo chown -R nvidia-docker:nvidia-docker /opt/nvidia-docker-volumes/
```

Now we can make the service create each docker volume with nvidia libraries within `/opt/nvidia-docker-volumes`
by using our modified unit file [usr/lib/systemd/system/nvidia-docker.service](usr/lib/systemd/system/nvidia-docker.service).

