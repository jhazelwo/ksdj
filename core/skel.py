# core/skel.py


def ks_d_hostname_ks(*args):
    return """
text
install
nfs --server=%s --dir=/path/to/kickstart/install/%s
network --onboot yes --bootproto static --ip %s --netmask %s --gateway %s --noipv6 --nameserver %s --hostname %s
lang en_US
keyboard us
network --onboot yes --bootproto dhcp
authconfig --useshadow --enablekrb5
bootloader --location=mbr --driveorder=sda
zerombr
clearpart --linux --drives=sda
part /boot --size=1024 --ondisk sda
part pv.01 --size=1    --ondisk sda --grow
volgroup vg1 pv.01
logvol /    --vgname=vg1 --size=10000  --name=root
logvol swap --vgname=vg1 --recommended --name=swap --fstype=swap
ignoredisk --only-use=sda
reboot 

%packages
@ base 
@ core 
%end

%pre
#!/bin/bash
thisDrive="`ls -ld /sys/block/sd*|grep -v usb|sort|head -1|awk -F/ '{print $4}'|awk '{print $1}'`"
cat << EOF >> /tmp/partout
clearpart --all --drives=${thisDrive} --initlabel
part /boot --fstype=ext3 --asprimary --size=512 --ondisk=${thisDrive}
part pv.rootvg_pv1 --ondisk=${thisDrive} --size=1 --grow
volgroup rootvg pv.rootvg_pv1
logvol swap --name=swap --vgname=rootvg --size=32768
logvol / --fstype=ext3 --name=root --vgname=rootvg --size=1 --grow
bootloader --location=mbr --driveorder=${thisDrive} --append="biosdevname=0 numa=off"
EOF
%end

%post --log=/root/post.log
#!/bin/bash
mkdir /root/ks
mount -t nfs -o ro,intr,nolock,vers=3 %s:/opt/kickstart/ /root/ks/
cp -v /root/ks/etc/clients.d/%s.sh /root/kickstart.source || exit $?
/root/ks/bin/build.d/00-fover.sh || exit $?
/root/ks/bin/build.d/10-lockdown.sh || exit $?
/root/ks/bin/build.d/70-bond.sh || exit $?
/root/ks/bin/build.d/80-byapp.sh || exit $?
/root/ks/bin/build.d/90-netbackup.sh || exit $?
%end

""" % (*args)

def client_d_hostname_sh(*args): return """
CLIENT_HOSTNAME="%s"
CLIENT_MAC="%s"
CLIENT_IPADDR="%s"
CLIENT_NETMASK="%s"
CLIENT_GATEWAY="%s"
CLIENT_TYPE="%s"
CLIENT_OS="%s"
SERVER_IPADDR="%s"

""" % (*args)

def tftpboot_mac(*args): return """

"""

def etc_vlan_conf(*args): return """
subnet %s netmask %s {
    authoritative ;
    option routers %s;
    next-server %s;
}

""" % (*args)
