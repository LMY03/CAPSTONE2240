sudo apt update -y

sudo apt install xfce4 xfce4-goodies -y

sudo apt install tightvncserver -y

vncserver

vncserver -kill :1

mv ~/.vnc/xstartup ~/.vnc/xstartup.bak

nano ~/.vnc/xstartup

#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &

sudo chmod +x ~/.vnc/xstartup

vncserver 

# References
https://www.linuxbuzz.com/install-configure-vnc-ubuntu-server/
