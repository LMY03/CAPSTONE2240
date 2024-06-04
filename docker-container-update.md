df -h

du -ah / | sort -rh | head -n 20

sudo apt-get clean

sudo apt-get autoremove

sudo rm -rf /tmp/*

docker system prune -a -y

sudo find /var/log -type f -delete

git -C CAP2240_API pull origin main

docker compose -f ~/CAP2240_API/docker-compose.yml up --build -d