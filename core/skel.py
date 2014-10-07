# core/skel.py

# Base kickstart config, please keep this as short as possible
# and as agnostic as possible. Put rel differences in post-build
# scripts or kickstart.py
base_ks = """#
install
text
nfs --server={SERVER_IP} --dir=/opt/kickstart/install/{OS_RELEASE}
network --onboot yes --bootproto static --ip {CLIENT_IP} --netmask {QUAD_MASK} --gateway {GATEWAY} --noipv6 --nameserver {NAME_SERVERS} --hostname {HOSTNAME}
reboot
lang en_US.UTF-8
keyboard us
rootpw {ROOT_PW}
firewall --disabled
authconfig --enableshadow --passalgo=sha512
firstboot --disabled
selinux --disabled
timezone --utc UTC
skipx
zerombr

%include /tmp/partout

%pre
#!/bin/bash
thisDrive="`ls -ld /sys/block/sd*|grep -v usb|sort|head -1|awk -F/ '{{print $4}}'|awk '{{print $1}}'`"
cat << EOF >> /tmp/partout
clearpart --all --drives=${{thisDrive}} --initlabel
part /boot --fstype={EXT34} --asprimary --size=512 --ondisk=${{thisDrive}}
bootloader --location=mbr --driveorder=${{thisDrive}} --append="biosdevname=0 numa=off"
part swap --fstype=swap     --size=32768           --ondisk=${{thisDrive}}
part /    --fstype={EXT34}  --size=1 --grow        --ondisk=${{thisDrive}}
EOF
%end

services --disabled=rdisc

%packages
@Base
@Core

%post --log=/root/post.log
#!/bin/bash
#
mkdir /root/ks
mount -t nfs -o ro,intr,nolock,vers=3 {SERVER_IP}:/opt/kickstart/ /root/ks/
cp -v /root/ks/etc/clients.d/{HOSTNAME}.sh /root/kickstart.source || exit $?
/root/ks/bin/build.d/00-fover.sh || exit $?
/root/ks/bin/build.d/10-lockdown.sh || exit $?
/root/ks/bin/build.d/70-bond.sh || exit $?
/root/ks/bin/build.d/80-byapp.sh || exit $?
/root/ks/bin/build.d/90-netbackup.sh || exit $?
%end
"""

#
# clients.d/hostname.sh -- shell variables that the post-build scripts use
base_sh = """CLIENT_HOSTNAME="{HOSTNAME}"
CLIENT_MAC="{MAC}"
CLIENT_IPADDR="{CLIENT_IP}"
CLIENT_NETMASK="{QUAD_MASK}"
CLIENT_GATEWAY="{GATEWAY}"
CLIENT_TYPE="{BUILD_TYPE}"
CLIENT_OS="{OS_RELEASE}"
SERVER_IPADDR="{SERVER_IP}"
"""

base_tftp = """default menu.c32
prompt 0
timeout 32
ONTIMEOUT Kickstart

MENU TITLE PXE Menu

LABEL Kickstart
    MENU LABEL Kickstart Install - {HOSTNAME} {OS_RELEASE}
    menu default
    KERNEL images/{OS_RELEASE}/vmlinuz
    IPAPPEND 2
    APPEND initrd=images/{OS_RELEASE}/initrd.img ramdisk_size=10000 ks=nfs:{SERVER_IP}:{KS_ROOT}/{HOSTNAME}.ks ksdevice=bootif

"""

# vlan_XX.conf file used by dhcpd.
base_vlan = """#
subnet {NETWORK} netmask {CIDR} {{
    authoritative;
    option routers {GATEWAY};
    next-server {SERVER_IP};
}}
"""

example_dhcpd_conf = """
#
# This file is called by an include statement in /etc/dhcp/dhcpd.conf
#
# DHCP Server Configuration file.
#   see /usr/share/doc/dhcp*/dhcpd.conf.sample
#   see 'man 5 dhcpd.conf'
#
allow bootp;
allow booting;
default-lease-time 600;
max-lease-time 7200;
option domain-name "google.com";
option domain-name-servers 10.25.18.51;
max-lease-time 604800;
default-lease-time 604800;
deny unknown-clients;

#subnet 10.25.23.0 netmask 255.255.255.192 { }
#subnet 10.168.248.0 netmask 255.255.248.0 { }

include "/opt/kickstart/etc/pxe_clients.conf";
include "/opt/kickstart/etc/vlan_26.conf";
#include "/opt/kickstart/etc/vlan_35.conf";
include "/opt/kickstart/etc/vlan_48.conf";

"""

