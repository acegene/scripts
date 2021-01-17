#!/bin/bash

echo "[SeatDefaults]" > /usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf
echo "user-session=ubuntu" >> /usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf
echo "greeter-session=unity-greeter" >> /usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf
echo "allow-guest=false" >> /usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf




