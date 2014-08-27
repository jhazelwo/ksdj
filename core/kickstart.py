# core/kickstart.py
"""

warnins vs errors -
    I've been going with the idea that errors related to input,
    like a typo in IP, should be warnings (yellow) but errors
    in the subsystem, like failure to update or create a file,
    should be errors (red). 


"""

import os
import time
from socket import gethostbyname
from django.contrib import messages
from vlan.models import VLAN
from client.models import Client

# https://github.com/tehmaze/ipcalc (ported to py3)
from . import ipcalc
# https://github.com/nullpass/npnutils/blob/master/fileasobj.py
from .fileasobj import FileAsObj
# base templates for files we create
from .skel import base_ks, base_sh, base_tftp, base_vlan

# Since we cannot include the real settings.py on github
# I have added examples for what these variables might be
from .settings import ks_root_password  # 'password'
from .settings import ks_nameservers    # '10.0.0.10,8.8.8.8'
from .settings import ks_domainname     # 'mycompany.tld'

from .settings import KSROOT        # /opt/kickstart/etc
from .settings import KS_CONF_DIR   # KSROOT, ks.d
from .settings import CLIENT_DIR    # KSROOT, clients.d
from .settings import TFTP          # /opt/tftpboot/pxelinux.cfg

from .settings import etc_hosts             # KSROOT, hosts
from .settings import etc_hosts_allow       # KSROOT, hosts.allow
from .settings import etc_pxe_clients_conf  # KSROOT, pxe_clients.conf

def vlan_validate(s, form):
    try:
        netinfo = ipcalc.Network('%s/%s' % (form.cleaned_data['network'],form.cleaned_data['cidr']))
    except Exception as e:
        messages.error(s.request, 'Failed to determine network information from data provided. - %s' % e, extra_tags='danger')
        return False
    #
    if form.cleaned_data['server_ip'] not in netinfo:
        messages.warning(s.request, 'IP address %s is not inside network %s/%s!' % (server_ip,network,cidr))
        return False

    

def vlan_create(s, form):
    """
    Add a VLAN to Kickstart
    
    1. Validate IP information
    2. If no gateway then set to lowest host
    3. Add 'include vlan_XX.conf' line to dhcpd.conf file
    4. Create vlan_XX.conf file
    
    If there is a problem generate an error and return False 
    """
    network = form.cleaned_data['network']
    cidr = form.cleaned_data['cidr']
    server_ip = form.cleaned_data['server_ip']
    vlanname = form.cleaned_data['name']
    #
    try:
        netinfo = ipcalc.Network('%s/%s' % (network,cidr))
    except Exception as e:
        messages.error(s.request, 'Failed to determine network information from data provided. - %s' % e, extra_tags='danger')
        return False
    #
    if server_ip not in netinfo:
        messages.warning(s.request, 'IP address %s is not inside network %s/%s!' % (server_ip,network,cidr))
        return False
    #
    # Set gateway
    if not form.cleaned_data['gateway']:
        form.instance.gateway = netinfo.host_first()
    gateway = form.instance.gateway
    #
    # KSROOT, dhcpd.conf
    dhcpd_conf = FileAsObj(os.path.join(KSROOT, 'dhcpd.conf'))
    if dhcpd_conf.Errors:
        messages.error(s.request, dhcpd_conf.Trace, extra_tags='danger')
        return False
    dhcpd_conf.add('include "%s/vlan_%s.conf";' % (KSROOT, vlanname))
    #
    # KSROOT, vlan_XX.conf
    fname = os.path.join(KSROOT, 'vlan_%s.conf' % vlanname)
    if os.path.isfile(fname):
        messages.error(s.request, 'Failed to add VLAN config. The file "vlan_%s.conf" already exists!' % vlanname, extra_tags='danger')
        return False
    vlan_conf = FileAsObj(fname)
    vlan_conf.contents = base_vlan.format(
        NETWORK=network,
        CIDR=cidr,
        GATEWAY=gateway,
        SERVER_IP=server_ip,
    ).split("\n")
    #
    # All is OK, save changes
    dhcpd_conf.write()
    vlan_conf.write()
    return True

def vlan_delete(old):
    """
    old = VLAN.objects.get(id=self.object.id)
    
    Remove vlan from dhcpd.conf and delete vlan_XX.conf file
    OK if vlan not found or file not found.
    The only real error state is if we are unable to edit dhcpd.conf
    
    """
    dhcpd_conf = FileAsObj(os.path.join(KSROOT, 'dhcpd.conf'))
    if dhcpd_conf.Errors:
        messages.error(s.request, dhcpd_conf.Trace, extra_tags='danger')
        return False
    dhcpd_conf.rm(dhcpd_conf.grep('vlan_%s.conf' % old.name))
    dhcpd_conf.write()
    fname = os.path.join(KSROOT, 'vlan_%s.conf' % old.name)
    if os.path.isfile(fname):
        try:
            os.remove(fname)
            print('Deleted {}'.format(fname))
        except Exception as e:
            print(e)
    return True

def client_create(s,form):
    """
    1. Get IP if Null
    2. Figure out VLAN from IP
    2a. make sure IP is valid for VLAN
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
    os_release = form.cleaned_data['os_release']
    #
    # We use ext4 by default, if it's a EL5.x build we use ext3.
    fstype = 'ext4'
    if form.cleaned_data['os_release'] == 'el5':
        fstype = 'ext3'
    #
    #
    if not form.cleaned_data['ip']:
        try:
            form.instance.ip = gethostbyname(hostname)
        except Exception as e:
            messages.warning(s.request, 'DNS lookup failed for "%s". Please correct hostname, update DNS, or specify IP. - %s' % (hostname,e))
            return False
    #
    #
    ip_count = Client.objects.filter(ip=form.instance.ip).count()
    if ip_count is not 1 and ip_count is not 0:
        messages.error(s.request, 'Critical error! IP %s in use by multiple clients. Contact Sr. Kickstart Admin!' % (form.instance.ip), extra_tags='danger')
        return False
    if ip_count == 1:
        """
        I'm finding it difficult to write a comment block explaining this sanity check part
        so I've put comments on lines as they execute in hopes others will understand.
        """
        try:
            # if this is a client edit, this will pass
            me = s.object.id
        except NameError:
            # s{elf}.object.id isn't set; this must be a client add then.
            me = None
        if me != Client.objects.filter(ip=form.instance.ip).get().id:
            messages.warning(s.request, 'DNS returned "%s", but that IP is already in use by another kickstart client.' % form.instance.ip)
            return False
        # else; the IP that's in use is the IP of the client we're changing and that's OK.
    #
    if not form.cleaned_data['vlan']:
        for thisv in VLAN.objects.all():
            getvlan = ipcalc.Network('%s/%s' % (thisv.network,thisv.get_cidr_display()))
            if form.instance.ip in getvlan:
                form.instance.vlan = thisv
    if not form.instance.vlan:
        messages.warning(s.request, 'IP %s not valid for any known vlans. Please check address and/or add needed VLAN.' % form.instance.ip)
        return False
    #
    if form.instance.ip not in ipcalc.Network('%s/%s' % (form.instance.vlan.network,form.instance.vlan.get_cidr_display())):
        messages.warning(s.request, 'IP %s not valid for VLAN %s. Please check address and/or add needed VLAN.' % (form.instance.ip,form.instance.vlan))
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
    if pxeconf.grep(' %s.%s ' % (hostname, ks_domainname) ):
        messages.error(s.request, 'Failed to update %s, host "%s" already present!' % (etc_pxe_clients_conf,hostname), extra_tags='danger')
        return False
    if pxeconf.grep(mac_addr):
        messages.error(s.request, 'Failed to update %s, MAC "%s" already present!' % (etc_pxe_clients_conf,mac_addr), extra_tags='danger')
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
    dashmac = '-'.join(mac_addr.split(":"))
    dashmac = '01-{}'.format(dashmac)
    fname = os.path.join(TFTP,dashmac)
    if os.path.isfile(fname):
        messages.error(s.request, 'Failed to add client. The file "%s" already exists!' % fname, extra_tags='danger')
        return False
    tftp_pxe = FileAsObj(fname)
    tftp_pxe.contents = base_tftp.format(
        KS_ROOT=KSROOT,
        OS_RELEASE=os_release,
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
        OS_RELEASE=os_release,
        QUAD_MASK=form.instance.vlan.cidr,
        GATEWAY=form.instance.vlan.gateway,
        HOSTNAME=hostname,
        EXT34=fstype,
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
        OS_RELEASE=os_release,
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

def client_delete(old):
    """
    Files to update:
        pxeconf
        hostsfile
        allowfile
        
    Files to remove:
        tftp_pxe
        hostname_ks
        client_sh
    """
    hostname = old.name
    mac_addr = old.mac
    client_ip = old.ip
    dashmac = '-'.join(mac_addr.split(":"))
    dashmac = '01-{}'.format(dashmac)
    #
    pxeconf = FileAsObj(etc_pxe_clients_conf)
    pxeconf.rm(pxeconf.grep(mac_addr))
    pxeconf.rm(pxeconf.grep(' {}.{} '.format(hostname,ks_domainname)))
    #
    hostsfile = FileAsObj(etc_hosts, verbose=True)
    hostsfile.rm(hostsfile.grep('{} # Kickstart Client '.format(hostname)))
    hostsfile.rm(hostsfile.egrep('^{} '.format(client_ip)))
    #
    allowfile = FileAsObj(etc_hosts_allow, verbose=True)
    allowfile.rm(allowfile.grep(client_ip))
    #
    for thisfile in [os.path.join(TFTP,dashmac),
                     os.path.join(KS_CONF_DIR,'%s.ks' % hostname),
                     os.path.join(CLIENT_DIR,'%s.sh' % hostname),
                     ]:
        try:
            os.remove(thisfile)
            print('Deleted {}'.format(thisfile))
        except Exception as e:
            print(e)
    #
    pxeconf.write()
    hostsfile.write()
    allowfile.write()
    return True
