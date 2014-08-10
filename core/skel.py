# core/skel.py

ks_d_hostname_ks(*args):
    return """
text
install
url --url=http://foo.bar.tld/rel/9001/
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

""" % (*args)

client_d_hostname_sh(*args):
    return """
CLIENT_HOSTNAME="%s"
CLIENT_MAC="%s"
CLIENT_IPADDR="%s"
CLIENT_NETMASK="%s"
CLIENT_GATEWAY="%s"
CLIENT_TYPE="%s"
CLIENT_OS="%s"
SERVER_IPADDR="%s"

""" % (*args)

tftpboot_mac = """

"""

etc_vlan_conf = """

"""