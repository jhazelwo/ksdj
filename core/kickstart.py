# core/kickstart.py
import os
from socket import gethostbyname
from django.contrib import messages
from .fileasobj import FileAsObj
# https://github.com/tehmaze/ipcalc (ported to py3)
from core import ipcalc

from vlan.models import VLAN


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
    pass


def client_create(s,form):
    """
    1. Get IP if Null
    2. Figure out VLAN from IP
    3. create ks.d/hostname.ks file (kickstart)
    4. create clients.d/hostname.sh (shell variables)
    5. put client in pxe_clients.conf
    6. create tftpboot/01-mac-address
    7. add to etc/hosts
    8. add to etc/hosts.allow
    
    on first failure generate message and return false.
    """
    if not form.cleaned_data['ip']:
        try:
            form.instance.ip = gethostbyname(form.cleaned_data['name'])
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
    hostname_ks = FileAsObj(os.path.join(KS_CONF_DIR,form.cleaned_data['name']))
    return True

 