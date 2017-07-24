# Customization for using NVidia GPU from within docker containers

Note that `nvidia-docker-plugin` expects the NVidia drivers and `nvidia-modprobe` to be installed native on the system

1. install `nvidia-docker` (after Docker and NVidia drivers but before `hilbert-cli`) on PCs with Nvidia GPU, e.g. following: [nvidia-docker-centos-instructions](https://github.com/NVIDIA/nvidia-docker#centos-distributions)
2. make sure to enable and start `nvidia-docker` using `systemctl`, e.g.
```
sudo systemctl --system enable nvidia-docker
sudo systemctl --system start nvidia-docker
```
  * NOTE: if necessary one can run `nvidia-docker-plugin` manually via `sudo -b nohup nvidia-docker-plugin > /tmp/nvidia-docker.log`
3. make sure to run any `nvidia-docker` test at least once before installing `hilbert-cl`, e.g.
```
sudo nvidia-docker run --rm nvidia/cuda:6.5-runtime-ubuntu14.04 nvidia-smi
sudo docker rmi nvidia/cuda:6.5-runtime-ubuntu14.04 # cleanup 
```
