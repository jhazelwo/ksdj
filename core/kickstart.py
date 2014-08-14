# core/kickstart.py
import os
import time
from socket import gethostbyname
from django.contrib import messages

from .fileasobj import FileAsObj
# https://github.com/tehmaze/ipcalc (ported to py3)
from core import ipcalc

from vlan.models import VLAN

# Really tempted to move all of these variables back to core/settings.py
from ksdj.settings import ks_root_password, ks_nameservers, ks_domainname

# Kickstart config-file root
KSROOT = os.path.join(os.sep,'opt','kickstart','etc')

# equiv of /opt/tftpboot/pxelinux.cfg/ 
# where we put grub menus for pxe clients named by mac address
TFTP = KSROOT

# equiv of /opt/kickstart/etc/clients.d
# Where we write the hostname.sh files that contain client variables
CLIENT_DIR = KSROOT

# equiv of /opt/kickstart/etc/ks.d
# Kickstart config files saved here, named by hostname.
KS_CONF_DIR = KSROOT

# equiv of /etc/hosts
etc_hosts = os.path.join(KSROOT,'hosts.txt')

# equiv of /etc/hosts.allow (if you use tcpwrappers)
etc_hosts_allow = os.path.join(KSROOT,'hosts.allow.txt')

# Where we tell DHCPD about the kickstart clients
etc_pxe_clients_conf = os.path.join(KSROOT,'pxe_clients.conf')

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

services --disabled=rdisc

%packages
@Base
@Core

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

def vlan_create(s, form):
    """
    Add a VLAN to Kickstart
    
    1. Validate IP information
    2. If no gateway then set to lowest host
    3. Add 'include vlan_XX.conf' line to dhcpd.conf file
    4. Create vlan_XX.conf file
    
    If there is a problem generate an error and return False 
    """
    n = form.cleaned_data['network']
    c = form.cleaned_data['cidr']
    i = form.cleaned_data['server_ip']
    netinfo = ipcalc.Network('%s/%s' % (n,c))
    if i not in netinfo:
        messages.warning(s.request, 'IP address %s is not inside network %s/%s!' % (i,n,c))
        return False
    if not form.cleaned_data['gateway']:
        form.instance.gateway = netinfo.host_first()
    #
    dhcpd_conf = FileAsObj(os.path.join(KSROOT, 'dhcpd.conf'))
    if dhcpd_conf.Errors:
        messages.error(s.request, 'Failed to update dhcpd.conf Have the Kickstart admin check logs.', extra_tags='danger')
        print(dhcpd_conf.Trace)
        return False
    dhcpd_conf.add('include "%s%svlan_%s.conf";' % (os.path.join(KSROOT), os.sep, form.cleaned_data['name']))
    #
    fname = os.path.join(KSROOT, 'vlan_%s.conf' % form.cleaned_data['name'])
    if os.path.isfile(fname):
        messages.error(s.request, 'Failed to add VLAN config. The file "vlan_%s.conf" already exists!' % form.cleaned_data['name'], extra_tags='danger')
        return False
    vlan_conf = FileAsObj(fname)
    vlan_conf.contents = []
    vlan_conf.add('#')
    vlan_conf.add('subnet %s netmask %s {' % ( form.cleaned_data['network'], form.cleaned_data['cidr'] ) )
    vlan_conf.add('    authoritative;')
    vlan_conf.add('    option routers %s;' % form.instance.gateway)
    vlan_conf.add('    next-server %s;' % form.cleaned_data['server_ip'])
    # All is OK, save changes
    dhcpd_conf.write()
    vlan_conf.write()
    return True

def vlan_update(s,form):
    """
    Change information about a VLAN
    
    1. Validate IP information
    2. Assign gateway if needed (low host)
    3. Edit dhcpd.conf, rename old VLAN # to new one
    4. Move vlan_XX.conf file to new name
    
    If there is a problem then generate an error and return False
    """
    messages.warning(s.request, 'poop')
    return False

def client_create(s,form):
    """
    1. Get IP if Null
    2. Figure out VLAN from IP
    3. unqie add to etc/hosts
    4. unqie add to etc/hosts.allow
    5. unqie add client in pxe_clients.conf
    6. create ks.d/hostname.ks file (kickstart)
    7. create clients.d/hostname.sh (shell variables)
    8. create tftpboot/01-mac-address
    
    on first failure generate message and return false.
    """
    hostname = form.cleaned_data['name'].lower()
    mac_addr = form.cleaned_data['mac'].lower()
    build_type = form.instance.get_build_type_display().lower()
    #
    # We use ext4 by default, if it's a EL5.x build we use ext3.
    use_ext = 'ext4'
    if form.cleaned_data['os_release'] == 'el5':
        use_ext = 'ext3'
    #
    #
    if not form.cleaned_data['ip']:
        try:
            form.instance.ip = gethostbyname(hostname)
        except Exception as e:
            messages.warning(s.request, 'DNS lookup failed for "%s". Please correct hostname, update DNS, or specify IP. - %s' % (form.cleaned_data['name'],e))
            return False
    if not form.cleaned_data['vlan']:
        for thisv in VLAN.objects.all():
            getvlan = ipcalc.Network('%s/%s' % (thisv.network,thisv.get_cidr_display()))
            if form.instance.ip in getvlan:
                form.instance.vlan = thisv
    if not form.instance.vlan:
        messages.warning(s.request, 'IP %s not valid for any known vlans. Please check address and/or add needed VLAN.' % form.instance.ip)
        return False
    #
    # etc/hosts
    hostsfile = FileAsObj(etc_hosts, verbose=True)
    if hostsfile.egrep('^[0-9].* %s ' % hostname):
        messages.warning(s.request, 'Failed to update hosts file, client "%s" already exists!' % hostname)
        return False
    if hostsfile.egrep('^%s ' % form.instance.ip):
        messages.warning(s.request, 'Failed to update hosts file, IP "%s" already exists!' % form.instance.ip)
        return False
    toadd = '{CLIENT_IP} {HOSTNAME}.{DOMAINNAME} {HOSTNAME} # Kickstart Client added {NOW}'.format(
        CLIENT_IP=form.instance.ip,
        HOSTNAME=hostname,
        DOMAINNAME=ks_domainname,
        NOW=time.strftime("%Y.%m.%d", time.localtime()),
    )
    hostsfile.add(toadd)
    #
    # etc/hosts.allow
    allowfile = FileAsObj(etc_hosts_allow, verbose=True)
    if allowfile.egrep('^ALL: ALL@%s : ALLOW' % form.instance.ip):
        messages.error(s.request, 'Failed to update %s, IP "%s" already present!' % (etc_hosts_allow,form.instance.ip), extra_tags='danger')
        return False
    allowfile.add('ALL: ALL@%s : ALLOW' % form.instance.ip)
    #
    # etc/pxe_clients.conf
    """ 
    group {
    filename "pxelinux.0";
    host ks-client01.example.tld  { hardware ethernet 00:1a:8g:4C:94:5E ; fixed-address ks-client01.example.tld ;}
    host ks-client11.example.tld  { hardware ethernet 00:1f:8b:c4:g4:5d ; fixed-address ks-client11.example.tld ;}
    host mail08.example.tld       { hardware ethernet 00:2f:e8:g9:e2:6f ; fixed-address mail08.example.tld ;}
    }
    Unique add host, don't use verbose mode- and add "}" at the end of the file.
    """
    pxeconf = FileAsObj(etc_pxe_clients_conf)
    if pxeconf.grep(' %s.%s ' % (hostname,ks_domainname) ):
        messages.error(s.request, 'Failed to update %s, host "%s" already present!' % (etc_pxe_clients_conf,hostname), extra_tags='danger')
        return False
    toadd = 'host {HOSTNAME}.{DOMAINNAME} {{ hardware ethernet {MAC} ; fixed-address {HOSTNAME}.{DOMAINNAME} ;}}'.format(
        HOSTNAME=hostname,
        DOMAINNAME=ks_domainname,
        MAC=mac_addr,
    )
    pxeconf.add(toadd)
    pxeconf.add('}')
    #
    # tftpboot/pxe.default/01-mac-address.lower().replace(":","-")
    dashmac = '-'.join(form.cleaned_data['mac'].split(":"))
    dashmac = '01-{}'.format(dashmac)
    fname = os.path.join(TFTP,dashmac)
    if os.path.isfile(fname):
        messages.error(s.request, 'Failed to add client. The file "%s" already exists!' % fname, extra_tags='danger')
        return False
    tftp_pxe = FileAsObj(fname)
    tftp_pxe.contents = base_tftp.format(
        KS_ROOT=KSROOT,
        OS_RELEASE=form.cleaned_data['os_release'],
        HOSTNAME=hostname,
        SERVER_IP=form.instance.vlan.server_ip,
    ).split("\n")
    #
    # {ksroot}/etc/ks.d/{hostname}.ks - kickstart config file
    fname = os.path.join(KS_CONF_DIR,'%s.ks' % hostname)
    if os.path.isfile(fname):
        messages.error(s.request, 'Failed to add client. The file "%s" already exists!' % fname, extra_tags='danger')
        return False
    hostname_ks = FileAsObj(fname)
    hostname_ks.contents = base_ks.format(
        CLIENT_IP=form.instance.ip,
        OS_RELEASE=form.cleaned_data['os_release'],
        QUAD_MASK=form.instance.vlan.cidr,
        GATEWAY=form.instance.vlan.gateway,
        HOSTNAME=hostname,
        EXT34=use_ext,
        SERVER_IP=form.instance.vlan.server_ip,
        ROOT_PW=ks_root_password,
        NAME_SERVERS=ks_nameservers,
    ).split("\n")
    #
    # {ksroot}/etc/clients.d/{hostname}.ks - shell variables for post build scripts to use
    fname = os.path.join(CLIENT_DIR,'%s.sh' % hostname)
    if os.path.isfile(fname):
        messages.error(s.request, 'Failed to add client. The file "%s" already exists!' % fname, extra_tags='danger')
        return False
    client_sh = FileAsObj(fname)
    client_sh.contents = base_sh.format(
        HOSTNAME=hostname,
        MAC=mac_addr,
        CLIENT_IP=form.instance.ip,
        QUAD_MASK=form.instance.vlan.cidr,
        GATEWAY=form.instance.vlan.gateway,
        BUILD_TYPE=build_type,
        OS_RELEASE=form.cleaned_data['os_release'],
        SERVER_IP=form.instance.vlan.server_ip,
    ).split("\n")
    #
    # If you made it this far everything went OK. Now write all the files!
    pxeconf.write()
    tftp_pxe.write()
    hostsfile.write()
    allowfile.write()
    hostname_ks.write()
    client_sh.write()
    return True
