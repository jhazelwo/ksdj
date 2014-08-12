# core/skel.py
import os
from .fileasobj import FileAsObj

# Kickstart config-file root
KSROOT = os.path.join(os.sep,'opt','kickstart','etc')

# base tftpboot directory, usually just 'tftpboot' 
TFTP = os.path.join(KSROOT, 'tftpboot')

# Where we write the hostname.sh files that contain
# client variables
CLIENT_DIR = os.path.join(KSROOT,'clients.d') 

# Kickstart config files saved here, named by hostname.
KS_CONF_DIR = os.path.join(KSROOT,'ks.d')

# equiv of /etc/hosts
etc_hosts = os.path.join(KSROOT,'hosts')

# equiv of /etc/hosts.allow (if you use tcpwrappers)
etc_hosts_allow = os.path.join(KSROOT,'hosts.allow')

# Where we tell DHCPD about the kickstart clients
etc_pxe_clients_conf = os.path.join(KSROOT,'pxe_clients.conf')

def do_dhcpd(form):
    """
    add
    include "/opt/kickstart/etc/vlan_XX.conf";
    to dhcpd.conf
    """
    this_file = FileAsObj(os.path.join(KSROOT, 'dhcpd.conf'))
    if this_file.Errors:
        print(this_file.Trace)
        return False
    this_file.add('include "%s%svlan_%s.conf";' % (os.path.join(KSROOT), os.sep, form.cleaned_data['name']))
    return this_file

def do_vlan_conf(form):
    """
    create vlan_XX.conf
    """
    fname = os.path.join(KSROOT, 'vlan_%s.conf' % form.cleaned_data['name'])
    if os.path.isfile(fname):
        print('File %s already exist' % fname)
        return False
    this_file = FileAsObj(fname)
    this_file.contents = []
    this_file.add('#')
    this_file.add('subnet %s netmask %s {' % ( form.cleaned_data['network'], form.cleaned_data['cidr'] ) )
    this_file.add('    authoritative;')
    this_file.add('    option routers %s;' % form.instance.gateway)
    this_file.add('    next-server %s;' % form.cleaned_data['server_ip'])
    this_file.dump()
    return this_file
