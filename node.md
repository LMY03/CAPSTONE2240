# Download the Ubuntu 22 Desktop ISO
https://releases.ubuntu.com/22.04/

# qemu agent

sudo apt install qemu-guest-agent -y

sudo systemctl enable qemu-guest-agent

sudo systemctl start qemu-guest-agent

# XRDP

sudo apt update -y

sudo apt upgrade -y

sudo apt install xfce4 xfce4-goodies -y

sudo apt install xrdp -y

sudo systemctl status xrdp

sudo systemctl start xrdp

sudo nano /etc/xrdp/xrdp.ini

sudo systemctl restart xrdp

<!-- # Netdata

wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh && sh /tmp/netdata-kickstart.sh

or

curl https://get.netdata.cloud/kickstart.sh > /tmp/netdata-kickstart.sh && sh /tmp/netdata-kickstart.sh

sudo nano /etc/netdata/stream.conf

[stream]
    enabled = yes
    destination = parent_vm_ip:19999
    api key = API_KEY

sudo nano /etc/netdata/netdata.conf

[global]
    hostname = HOST_NAME

sudo systemctl enable netdata

sudo systemctl restart netdata -->


# References

https://learn.netdata.cloud/docs/observability-centralization-points/metrics-centralization-points/configuring-metrics-centralization-points
https://www.linuxbuzz.com/install-configure-vnc-ubuntu-server/