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

bootloader --location=mbr --driveorder=${{thisDrive}} --append="crashkernel=auto biosdevname=0 numa=off rhgb quiet"

clearpart --all --drives=${{thisDrive}} --initlabel

part /boot --fstype=ext4 --asprimary --size=512 --ondisk=${{thisDrive}}
part pv.008018 --grow --size=1

volgroup rootvg --pesize=32768 pv.008018

logvol /opt --fstype={EXT34} --name=opt  --vgname=rootvg --grow --size=1
logvol /    --fstype={EXT34} --name=root --vgname=rootvg --size=2048
logvol swap                  --name=swap --vgname=rootvg --size=32768
logvol /tmp --fstype={EXT34} --name=tmp  --vgname=rootvg --size=16384
logvol /usr --fstype={EXT34} --name=usr  --vgname=rootvg --size=6144
logvol /var --fstype={EXT34} --name=var  --vgname=rootvg --size=8192

EOF
%end

services --disabled=rdisc

%packages
@Base
@Core
@network-file-system-client
@server-policy

cloog-ppl
compat-libcap1
compat-libstdc++-33
cpp
gcc
gcc-c++
glibc-devel
glibc-headers
ksh
libICE
libSM
libXmu
libXt
libXtst
libXv
libXxf86dga
libXxf86misc
libXxf86vm
libaio-devel
libdmx
libgomp
libstdc++-devel
make
mpfr
ppl
xorg-x11-utils
xorg-x11-xauth


elfutils-libs
elfutils-libelf-devel
elfutils-devel
glibc-devel.i686
libstdc++-devel.i686
libaio.i686
libaio-devel.i686
unixODBC
unixODBC-devel
unixODBC.i686
unixODBC-devel.i686
compat-libstdc++-296-2.96-144.el6.i686
compat-libstdc++-33-3.2.3-69.el6.i686
compat-db
compat-db.i686
libxml2.i686
libattr.i686
libacl.i686
xinetd
libXp
libXp.i686
libXtst.i686
gdb
ncompress
openldap-clients
pam_krb5
sssd
procmail
sendmail
sysstat
nscd
perl
device-mapper-multipath
telnet
ftp
dump
rmt
compat-libtermcap.i686
compat-libtermcap.x86_64
dos2unix

-acpid
-avahi-dnsconfd
-conman
-cups
-cyrus-imapd
-dovecot
-gpm
-hplip
-httpd
-lm_sensors
-mailman
-mcstrans
-microcode_ctl
-postgresql
-psacct
-radvd
-rhnsd
-selinux-policy-targeted
-setroubleshoot
-spamassassin
-squid
-tog-pegasus
-wpa_supplicant
-ypbind
-ypserv
-samba-winbind
-samba-winbind-clients
-cifs-utils
-samba-client
-samba-common
-kexec-tools
-pm-utils
-hal
-hal-info
-hal-libs
-foomatic-db-ppds
-foomatic-db
-foomatic
-cups
%end

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
    APPEND initrd=images/{OS_RELEASE}/initrd.img ramdisk_size=10000 ks=nfs:{SERVER_IP}:{KS_CONF_DIR}/{HOSTNAME}.ks ksdevice=bootif

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

