# Pre-requisites

- Setup VM Templates
- Create a VM/Container in Proxmox 

## Setup VM Templates

### Download Ubuntu LTS 22 Desktop ISO 
https://releases.ubuntu.com/22.04/

### Install QEMU Agent PKG
```bash
sudo apt install qemu-guest-agent -y

sudo systemctl enable qemu-guest-agent

sudo systemctl start qemu-guest-agent
```

### Install XRDP PKG
```bash
sudo apt update -y

sudo apt upgrade -y

sudo apt install xfce4 xfce4-goodies -y

sudo apt install xrdp -y

sudo systemctl status xrdp

sudo systemctl start xrdp

sudo nano /etc/xrdp/xrdp.ini

sudo systemctl restart xrdp
```
## Setup VM/Container in Proxmox 
### Follow the guide in the official documentation to Install Docker

https://docs.docker.com/engine/install/

### add the user in to the docker group (replace USER_NAME)

```bash 
sudo usermod -aG docker USER_NAME
```

### Create a SSH keys
```bash 
ssh-keygen -t rsa -b 4096
```
### Clone Github Repository

git clone https://github.com/LMY03/CAPSTONE2240.git

docker compose -f ~/CAPSTONE2240/docker-compose.yml up --build -d

### Set up MySQL DB

```bash
mkdir -p ~/guacamole-initdb

docker run --rm guacamole/guacamole /opt/guacamole/bin/initdb.sh --mysql > ~/guacamole-initdb/initdb.sql

docker cp ~/guacamole-initdb/initdb.sql mysql:/docker-entrypoint-initdb.d

docker exec -it mysql bash
```

```bash
cd /docker-entrypoint-initdb.d

mysql -u root -p
```

```bash
CREATE DATABASE IF NOT EXISTS guacamole_db;

CREATE USER IF NOT EXISTS 'guacadmin'@'%' IDENTIFIED BY 'guacpassword';

GRANT SELECT, UPDATE, INSERT, DELETE ON guacamole_db.* TO 'guacadmin'@'%';

flush privileges;

use guacamole_db;

source initdb.sql;

exit;

exit
```

```bash
docker cp ~/CAPSTONE2240/init.sql mysql:init.sql

docker exec -it mysql bash
```

```bash
mysql -u root -p

source init.sql

exit;

exit

```

