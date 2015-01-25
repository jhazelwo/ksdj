# core/kickstart.py
"""

This is the main engine for updating files on the kickstart server with client and vlan data.

"""

import os
import time
import shutil
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
from cfgksdj import ks_root_password  # 'password'
from cfgksdj import ks_nameservers    # '10.0.0.10,8.8.8.8'
from cfgksdj import ks_domainname     # 'mycompany.tld'

from cfgksdj import KSROOT        # /opt/kickstart/etc
from cfgksdj import KS_CONF_DIR   # KSROOT, ks.d
from cfgksdj import CLIENT_DIR    # KSROOT, clients.d
from cfgksdj import TFTP          # /opt/tftpboot/pxelinux.cfg

from cfgksdj import etc_hosts             # KSROOT, hosts
from cfgksdj import etc_hosts_allow       # KSROOT, hosts.allow
from cfgksdj import etc_pxe_clients_conf  # KSROOT, pxe_clients.conf

from cfgksdj import BK_DIR  # KSROOT, .archive

"""
# Nothing uses this right now.
def vlan_validate(view, form):
    try:
        network_cidr = '{0}/{1}'.format(form.cleaned_data['network'], form.cleaned_data['cidr'])
        netinfo = ipcalc.Network(network_cidr)
    except Exception as e:
        messages.error(view.request,
                       'Failed to determine network information from data provided. - {0}'.format(e),
                       extra_tags='danger')
        return False
    #
    if form.cleaned_data['server_ip'] not in netinfo:
        messages.warning(view.request, 'IP address {0} is not inside network {1}/{2}!'.format(
            form.cleaned_data['server_ip'],
            form.cleaned_data['network'],
            form.cleaned_data['cidr']))
        return False
"""


def vlan_create(view, form):
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
        netinfo = ipcalc.Network('{0}/{1}'.format(network, cidr))
    except Exception as e:
        messages.error(view.request,
                       'Unable to determine network from data provided. - {0}'.format(e),
                       extra_tags='danger')
        return False
    #
    if server_ip not in netinfo:
        messages.error(view.request,
                       'IP {0} is not inside network {1}/{2}!'.format(server_ip, network, cidr),
                       extra_tags='danger')
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
        messages.error(view.request, dhcpd_conf.Trace, extra_tags='danger')
        return False
    dhcpd_conf.add('include "{0}/vlan_{1}.conf";'.format(KSROOT, vlanname))
    #
    # KSROOT, vlan_XX.conf
    file = os.path.join(KSROOT, 'vlan_{0}.conf'.format(vlanname))
    if os.path.isfile(file):
        messages.error(view.request,
                       'Failed to add VLAN; "{0}" already exists!'.format(file),
                       extra_tags='danger')
        return False
    vlan_conf = FileAsObj(file)
    vlan_conf.contents = base_vlan.format(
        NETWORK=network,
        CIDR=cidr,
        GATEWAY=gateway,
        SERVER_IP=server_ip,
    ).split('\n')
    #
    # All is OK, save changes
    dhcpd_conf.write()
    vlan_conf.write()
    return True


def vlan_delete(view):
    """
    view.old = VLAN.objects.get(id=self.object.id)
    
    Remove vlan from dhcpd.conf and delete vlan_XX.conf file
    OK if vlan not found or file not found.
    The only real error state is if we are unable to edit dhcpd.conf
    
    """
    file_name = 'vlan_{0}.conf'.format(view.old.name)
    #
    dhcpd_conf = FileAsObj(os.path.join(KSROOT, 'dhcpd.conf'))
    if dhcpd_conf.Errors:
        messages.error(view.request, dhcpd_conf.Trace, extra_tags='danger')
        return False
    dhcpd_conf.rm(dhcpd_conf.grep(file_name))
    if not dhcpd_conf.virgin:
        dhcpd_conf.write()
    #
    fname = os.path.join(KSROOT, file_name)
    if os.path.isfile(fname):
        try:
            os.remove(fname)
        except:
            pass
    return True


def client_create(view, form):
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
            msg = 'DNS lookup failed for "{0}". Please update DNS or specify IP. - {1}'.format(hostname, e)
            messages.warning(view.request, msg)
            return False
    #
    #
    ip_count = Client.objects.filter(ip=form.instance.ip).count()
    if ip_count is not 1 and ip_count is not 0:
        msg = 'Critical error! IP {0} in use by multiple clients. Contact Sr. Kickstart Admin!'.format(form.instance.ip)
        messages.error(view.request, msg, extra_tags='danger')
        return False
    if ip_count == 1:
        """
        I'm finding it difficult to write a comment block explaining this sanity check part
        so I've put comments on lines as they execute in hopes others will understand.
        """
        try:
            # if this is a client edit, this will pass
            me = view.object.id
        except NameError:
            # view.object.id isn't set; this must be a client add then.
            me = None
        if me != Client.objects.filter(ip=form.instance.ip).get().id:
            msg = 'DNS returned "{0}", but that IP already in use by another kickstart client.'.format(form.instance.ip)
            messages.warning(view.request, msg)
            return False
        # else; the IP that's in use is the IP of the client we're changing and that's OK.
    #
    if not form.cleaned_data['vlan']:
        for thisv in VLAN.objects.all():
            network_cidr = '{0}/{1}'.format(thisv.network, thisv.get_cidr_display())
            getvlan = ipcalc.Network(network_cidr)
            if form.instance.ip in getvlan:
                form.instance.vlan = thisv
    if not form.instance.vlan:
        msg = 'IP {0} not valid for any known vlans!'.format(form.instance.ip)
        messages.warning(view.request, msg)
        return False
    #
    testing_net = ipcalc.Network('{0}/{1}'.format(form.instance.vlan.network, form.instance.vlan.get_cidr_display()))
    if form.instance.ip not in testing_net:
        msg = 'IP {0} not valid for VLAN {1}.'.format(form.instance.ip, form.instance.vlan)
        messages.warning(view.request, msg)
        return False
    #
    # etc/hosts
    hostsfile = FileAsObj(etc_hosts, verbose=True)
    if hostsfile.egrep('^[0-9].*[ \\t]{0}'.format(hostname)):
        messages.warning(view.request,
                         'Failed to update {0}, client "{1}" already exists!'.format(etc_hosts, hostname))
        return False
    if hostsfile.egrep('^{0}[ \\t]'.format(form.instance.ip)):
        messages.warning(view.request,
                         'Failed to update {0}, IP "{1}" already exists!'.format(etc_hosts, form.instance.ip))
        return False
    toadd = '{CLIENT_IP} {HOSTNAME}.{DOMAINNAME} {HOSTNAME} # Kickstart Client added {NOW}'.format(
        CLIENT_IP=form.instance.ip,
        HOSTNAME=hostname,
        DOMAINNAME=ks_domainname,
        NOW=time.strftime('%Y.%m.%d', time.localtime()),
    )
    hostsfile.add(toadd)
    #
    # etc/hosts.allow
    allowfile = FileAsObj(etc_hosts_allow, verbose=True)
    if allowfile.egrep('^ALL: ALL@{0} : ALLOW'.format(form.instance.ip)):
        messages.error(view.request,
                       'Failed to update {0}, IP "{1}" already present!'.format(etc_hosts_allow, form.instance.ip),
                       extra_tags='danger')
        return False
    allowfile.add('ALL: ALL@{0} : ALLOW'.format(form.instance.ip))
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
    if pxeconf.grep(' {0}.{1} '.format(hostname, ks_domainname)):
        messages.error(view.request,
                       'Failed to update {0}, host "{1}" already present!'.format(etc_pxe_clients_conf, hostname),
                       extra_tags='danger')
        return False
    if pxeconf.grep(mac_addr):
        messages.error(view.request,
                       'Failed to update {0}, MAC "{1}" already present!'.format(etc_pxe_clients_conf, mac_addr),
                       extra_tags='danger')
        return False
    toadd = 'host {HOSTNAME}.{DOMAINNAME} {{ hardware ethernet {MAC} ; fixed-address {CLIENT_IP} ;}}'.format(
        HOSTNAME=hostname,
        DOMAINNAME=ks_domainname,
        MAC=mac_addr,
        CLIENT_IP=form.instance.ip,
    )
    pxeconf.add(toadd)
    pxeconf.add('}')
    #
    # tftpboot/pxe.default/01-mac-address.lower().replace(":","-")
    dashmac = '-'.join(mac_addr.split(':'))
    dashmac = '01-{}'.format(dashmac)
    fname = os.path.join(TFTP, dashmac)
    if os.path.isfile(fname):
        messages.error(view.request,
                       'Failed to add client. The file "{0}" already exists!'.format(fname),
                       extra_tags='danger')
        return False
    tftp_pxe = FileAsObj(fname)
    tftp_pxe.contents = base_tftp.format(
        KS_CONF_DIR=KS_CONF_DIR,
        OS_RELEASE=os_release,
        HOSTNAME=hostname,
        SERVER_IP=form.instance.vlan.server_ip,
    ).split('\n')
    #
    # {ksroot}/etc/ks.d/{hostname}.ks - kickstart config file
    fname = os.path.join(KS_CONF_DIR, '{0}.ks'.format(hostname))
    if os.path.isfile(fname):
        messages.error(view.request,
                       'Failed to add client. The file "{0}" already exists!'.format(fname),
                       extra_tags='danger')
        return False
    if view.object:
        kscfg = view.old.kickstart_cfg
        kscfg = kscfg.replace(view.old.ip, form.instance.ip)
        kscfg = kscfg.replace(view.old.os_release, os_release)
        kscfg = kscfg.replace(view.old.vlan.get_cidr_display(), form.instance.vlan.cidr)
        kscfg = kscfg.replace(view.old.vlan.gateway, form.instance.vlan.gateway)
        kscfg = kscfg.replace(view.old.name, hostname)
        if view.old.os_release == 'el5':
            kscfg = kscfg.replace('ext3', fstype)
        if view.old.os_release == 'el6':
            kscfg = kscfg.replace('ext4', fstype)
        kscfg = kscfg.replace(view.old.vlan.server_ip, form.instance.vlan.server_ip,)
    else:
        kscfg = base_ks.format(
            CLIENT_IP=form.instance.ip,
            OS_RELEASE=os_release,
            QUAD_MASK=form.instance.vlan.cidr,
            GATEWAY=form.instance.vlan.gateway,
            HOSTNAME=hostname,
            EXT34=fstype,
            SERVER_IP=form.instance.vlan.server_ip,
            ROOT_PW=ks_root_password,
            NAME_SERVERS=ks_nameservers,
        )
    form.instance.kickstart_cfg = kscfg
    hostname_ks = FileAsObj(fname)
    hostname_ks.contents = kscfg.split('\n')
    #
    # {ksroot}/etc/clients.d/{hostname}.ks - shell variables for post build scripts to use
    fname = os.path.join(CLIENT_DIR, '{0}.sh'.format(hostname))
    if os.path.isfile(fname):
        messages.error(view.request,
                       'Failed to add client. The file "{0}" already exists!'.format(fname),
                       extra_tags='danger')
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
    ).split('\n')
    #
    # If you made it this far everything went OK. Now write all the files!
    pxeconf.write()
    tftp_pxe.write()
    hostsfile.write()
    allowfile.write()
    hostname_ks.write()
    client_sh.write()
    return True


def client_delete(obj):
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
    client = obj.old
    hostname = client.name
    mac_addr = client.mac
    client_ip = client.ip
    dashmac = '-'.join(mac_addr.split(':'))
    dashmac = '01-{}'.format(dashmac)
    #
    pxeconf = FileAsObj(etc_pxe_clients_conf)
    pxeconf.rm(pxeconf.grep(mac_addr))
    pxeconf.rm(pxeconf.grep(' {}.{} '.format(hostname, ks_domainname)))
    #
    hostsfile = FileAsObj(etc_hosts, verbose=True)
    hostsfile.rm(hostsfile.grep('{} # Kickstart Client '.format(hostname)))
    hostsfile.rm(hostsfile.egrep('^{} '.format(client_ip)))
    #
    allowfile = FileAsObj(etc_hosts_allow, verbose=True)
    allowfile.rm(allowfile.grep(client_ip))
    #
    for thisfile in [os.path.join(TFTP, dashmac),
                     os.path.join(KS_CONF_DIR, '{0}.ks'.format(hostname)),
                     os.path.join(CLIENT_DIR, '{0}.sh'.format(hostname)),
                     ]:
        if os.path.isfile(thisfile):
            try:
                newname = '{}_{}'.format(os.path.basename(thisfile), int(time.time()))
                target = os.path.join(BK_DIR, newname)
                shutil.move(thisfile, target)
            except Exception as e:
                messages.error(obj.request, e, extra_tags='danger')
                return False
    #
    pxeconf.write()
    hostsfile.write()
    allowfile.write()
    return True


def update_kickstart_file(view, form):
    """
    Update The kickstart config file for a client: ./etc/ks.d/hostname.ks
    """
    fname = os.path.join(KS_CONF_DIR, '{0}.ks'.format(view.object.name))
    this_file = FileAsObj(fname, verbose=True)
    if this_file.Errors:
        messages.error(view.request, this_file.Trace, extra_tags='danger')
        return False
    this_file.contents = [form.cleaned_data['kickstart_cfg'].replace('\r', '')]
    this_file.write()
    return True
