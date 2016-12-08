#! /bin/bash

#if hash docker-composei 2>/dev/null; then
#  echo "DEBUG: using $(which docker-compose), $(docker-compose --version)"
#  ln -s `which docker-compose` "${PWD}/compose"
#else
 #! Get Docker compose
 DOCKER_COMPOSE_VERSION=1.9.0 # NOTE: update to newer compose version if necessary!
 DOCKER_COMPOSE_BASE_URL="https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}"

 DOCKER_COMPOSE_BIN_URL="${DOCKER_COMPOSE_BASE_URL}/docker-compose-$(uname -s)-$(uname -m)"
 DOCKER_COMPOSE_SH_URL="${DOCKER_COMPOSE_BASE_URL}/run.sh"


 if [ ! -x ./docker-compose ]; then
  if hash curl 2>/dev/null; then
    curl -L "${DOCKER_COMPOSE_BIN_URL}"  > ./docker-compose && chmod +x ./docker-compose
  elif hash wget 2>/dev/null; then
    wget -q -O - "${DOCKER_COMPOSE_BIN_URL}" > ./docker-compose && chmod +x ./docker-compose
  fi
 fi

 if [ -x ./docker-compose ]; then
  if [ -x ./docker-compose ]; then 
    ln -s "${PWD}/docker-compose" "${PWD}/compose"
  fi 
 
 else
  if [ ! -x ./docker-compose.sh ]; then
    if hash curl 2>/dev/null; then
      curl -L "${DOCKER_COMPOSE_SH_URL}"  > ./docker-compose.sh && chmod +x ./docker-compose.sh
    elif hash wget 2>/dev/null; then
      wget -q -O - "${DOCKER_COMPOSE_SH_URL}" > ./docker-compose.sh && chmod +x ./docker-compose.sh
    fi
  fi

  if [ -x ./docker-compose.sh ]; then 
    ln -s "${PWD}/docker-compose.sh" "${PWD}/compose"
  fi
 fi
#fi

if [ ! -x ./compose ]; then 
 if hash docker-composei 2>/dev/null; then
  echo "DEBUG: using $(which docker-compose), $(docker-compose --version)"
  ln -s `which docker-compose` "${PWD}/compose"
 fi
fi

if [ ! -x ./compose ]; then 
   echo "Warning: could not get 'docker-compose' from 'https://github.com/docker/compose/releases'! 
         Please download it as '$PWD/docker-compose' and make it executable!"
else
  echo "DEBUG: using `readlink -f ${PWD}/compose`, `./compose --version`"
fi



###################################################################################
### docker login -u malex984 -p ... ... imaginary.mfo.de:5000

D="${HOME}/.docker/"
F="${D}/config.json"
mkdir -p "${D}"
HILBERT_SERVER_DOCKER_REPOSITORY="${HILBERT_SERVER_DOCKER_REPOSITORY:-imaginary.mfo.de:5000}"
HILBERT_SERVER_DOCKER_REPOSITORY_AUTH="${HILBERT_SERVER_DOCKER_REPOSITORY_AUTH:-bWFsZXg5ODQ6MzJxMzJx}"
### TODO: FIXME: update wrt server repository! Later on!
cat > "${F}~" <<EOF
{
	"auths": {
		"${HILBERT_SERVER_DOCKER_REPOSITORY}": {
			"auth": "${HILBERT_SERVER_DOCKER_REPOSITORY_AUTH}"
		}
	}
}
EOF
#mv "${F}~" "${F}"

exit 0

###################################################################################
## install Docker Volume 'local-persist' plugin following https://github.com/CWSpear/local-persist
## curl -fsSL https://raw.githubusercontent.com/CWSpear/local-persist/master/scripts/install.sh | sudo bash

## cd ./tmp/
### TODO: add the plugin for global installation?
#curl -fsSL https://github.com/CWSpear/local-persist/releases/download/v1.1.0/local-persist-linux-amd64 > ./local-persist-linux-amd64
#chmod +x ./local-persist-linux-amd64
#sudo ./local-persist-linux-amd64 1>./local-persist-linux-amd64.log 2>&1 &

#docker volume create -d local-persist -o mountpoint="$CFG_DIR/KV" --name=KV
#docker volume create -d local-persist -o mountpoint="$CFG_DIR/OMD" --name=OMD
#docker volume create -d local-persist -o mountpoint="$CFG_DIR/CFG" --name=CFG
