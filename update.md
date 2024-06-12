sudo df -h

sudo du -ah / | sort -rh | head -n 20

sudo apt-get clean

sudo apt-get autoremove

sudo rm -rf /tmp/*

docker system prune -a -y

sudo find /var/log -type f -delete

git -C CAPSTONE2240 pull origin main

docker compose -f ~/CAPSTONE2240/docker-compose.yml up --build -d