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
sudo systemctl restart netdata

https://learn.netdata.cloud/docs/observability-centralization-points/metrics-centralization-points/configuring-metrics-centralization-points