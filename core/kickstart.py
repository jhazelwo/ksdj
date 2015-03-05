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
# https://github.com/nullpass/fileasobj/blob/master/__init__.py
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


def vlan_create(form):
    """
    Add a VLAN to Kickstart
    
    1. Validate IP information
    2. Set gateway to lowest host
    3. Set kickstart server IP to highest host minus 2.
    4. Add 'include vlan_XX.conf' line to dhcpd.conf file
    5. Create vlan_XX.conf file
    
    On error raise an exception, let the view handle it.

    :param: form - A cleaned form object from view.form_valid()
    :return: form
    """
    netinfo = ipcalc.Network('{0}/{1}'.format(form.instance.network, form.instance.cidr), version=4)
    #
    # Set model data to actual network, it's often entered incorrectly.
    form.instance.network = netinfo.network()
    #
    # Gateway and ServerIP are auto-selected during VLAN.Create, but specified during VLAN.Update.
    if 'gateway' not in form.cleaned_data:
        form.instance.gateway = netinfo.host_first()
    else:
        #
        # If user entered no gateway during VLAN.Update then set to lowest host.
        if not form.cleaned_data['gateway']:
            form.instance.gateway = netinfo.host_first()
        elif form.cleaned_data['gateway'] not in netinfo:
            raise ValueError('Gateway is outside this VLAN!')
    #
    if 'server_ip' not in form.cleaned_data or not form.cleaned_data['server_ip']:
        #
        # No server IP given, default to
        form.instance.server_ip = ipcalc.IP(int(netinfo.host_last()) - 2, version=4)
    else:
        if form.cleaned_data['server_ip'] not in netinfo:
            raise ValueError('Kickstart Server IP is outside this VLAN!')
    #
    name = form.cleaned_data['name']
    dhcpd_conf = FileAsObj(os.path.join(KSROOT, 'dhcpd.conf'))  # /opt/kickstart/etc/dhcpd.conf
    dhcpd_conf.add('include "{0}/vlan_{1}.conf";'.format(KSROOT, name))
    #
    vlan_conf = FileAsObj()
    vlan_conf.filename = os.path.join(KSROOT, 'vlan_{0}.conf'.format(name))  # /opt/kickstart/etc/vlan_{name}.conf
    vlan_conf.contents = base_vlan.format(
        NETWORK=form.instance.network,
        CIDR=form.instance.cidr,
        GATEWAY=form.instance.gateway,
        SERVER_IP=form.instance.server_ip,
    ).split('\n')
    #
    # All is OK, save changes and return form.
    dhcpd_conf.write()
    vlan_conf.write()
    return form


def vlan_delete(obj):
    """
    Remove vlan from dhcpd.conf and delete vlan_XX.conf file
    OK if vlan not found.
    The only real errors are if we are unable to edit dhcpd.conf or if there a clients in the VLAN.

    No return values; just raise an exception if there's a problem.
    """
    if obj.client.count() is not 0:
        raise ValueError('Unable to delete, there are clients in this vlan!')
    file_name = 'vlan_{0}.conf'.format(obj.name)
    #
    dhcpd_conf = FileAsObj(os.path.join(KSROOT, 'dhcpd.conf'))  # /opt/kickstart/etc/dhcpd.conf
    #
    dhcpd_conf.rm(dhcpd_conf.grep(file_name))
    if not dhcpd_conf.virgin:
        dhcpd_conf.write()
    #
    filename = os.path.join(KSROOT, file_name)  # /opt/kickstart/etc/vlan_{name}.conf
    try:
        os.remove(filename)
    except:
        pass
    return


def client_create(form, old=False):
    """
    1. Get IP if Null
    2. Figure out VLAN from IP
    2a. make sure IP is valid for VLAN
    3. unquie add to etc/hosts
    4. unquie add to etc/hosts.allow
    5. unquie add client in pxe_clients.conf
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
        #
        # No client_IP given, get from DNS (or fail)
        form.instance.ip = gethostbyname(hostname)
        if Client.objects.filter(ip=form.instance.ip).count() is not 0:
            raise ValueError('DNS returned {0} but that IP already in use.'.format(form.instance.ip))
    #
    if not form.cleaned_data['vlan']:
        for thisv in VLAN.objects.all():
            network_cidr = '{0}/{1}'.format(thisv.network, thisv.get_cidr_display())
            getvlan = ipcalc.Network(network_cidr)
            if form.instance.ip in getvlan:
                form.instance.vlan = thisv
    if not form.instance.vlan:
        raise ValueError('IP {0} not valid for any known vlans!'.format(form.instance.ip))
    #
    testing_net = ipcalc.Network('{0}/{1}'.format(form.instance.vlan.network, form.instance.vlan.get_cidr_display()))
    if form.instance.ip not in testing_net:
        raise ValueError('IP {0} not valid for VLAN {1}.'.format(form.instance.ip, form.instance.vlan))
    #
    # Validate that client IP is not already a server IP, network or gateway.
    if VLAN.objects.filter(server_ip=form.instance.ip).count() is not 0 or \
        VLAN.objects.filter(gateway=form.instance.ip).count() is not 0 or \
            VLAN.objects.filter(network=form.instance.ip).count() is not 0:
        raise ValueError('Client IP "{0}" is in use by a VLAN object.'.format(form.instance.ip))
    #
    # etc/hosts
    hostsfile = FileAsObj(etc_hosts, verbose=True)
    if hostsfile.egrep('^[0-9].*[ \\t]{0}'.format(hostname)):
        raise ValueError('Failed to update {0}, client "{1}" already exists!'.format(etc_hosts, hostname))
    if hostsfile.egrep('^{0}[ \\t]'.format(form.instance.ip)):
        raise ValueError('Failed to update {0}, IP "{1}" already exists!'.format(etc_hosts, form.instance.ip))
    toadd = '{CLIENT_IP} {HOSTNAME}.{DOMAINNAME} {HOSTNAME} # Kickstart Client added {NOW}'.format(
        CLIENT_IP=form.instance.ip,
        HOSTNAME=hostname,
        DOMAINNAME=ks_domainname,
        NOW=time.strftime('%Y.%m.%d', time.localtime()),
    )
    hostsfile.add(toadd)
    #
    allowfile = FileAsObj(etc_hosts_allow, verbose=True)  # /etc/hosts.allow
    pattern = 'ALL: ALL@{0} : ALLOW'.format(form.instance.ip)
    if pattern not in allowfile.contents:
        allowfile.add(pattern)
    #
    pxeconf = FileAsObj(etc_pxe_clients_conf)  # /opt/kickstart/etc/pxe_clients.conf
    if pxeconf.grep(' {0}.{1} '.format(hostname, ks_domainname)):
        raise ValueError('{0} already present in {1}'.format(hostname, etc_pxe_clients_conf))
    if pxeconf.grep(mac_addr):
        raise ValueError('Failed to update {0}, MAC "{1}" already present!'.format(etc_pxe_clients_conf, mac_addr))
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
    dashmac = '01-{0}'.format(dashmac)
    filename = os.path.join(TFTP, dashmac)
    if os.path.isfile(filename):
        raise ValueError('Failed to add client. The file "{0}" already exists!'.format(filename))
    tftp_pxe = FileAsObj()
    tftp_pxe.filename = filename
    tftp_pxe.contents = base_tftp.format(
        KS_CONF_DIR=KS_CONF_DIR,
        OS_RELEASE=os_release,
        HOSTNAME=hostname,
        SERVER_IP=form.instance.vlan.server_ip,
    ).split('\n')
    #
    # {ksroot}/etc/ks.d/{hostname}.ks - kickstart config file
    filename = os.path.join(KS_CONF_DIR, '{0}.ks'.format(hostname))
    if os.path.isfile(filename):
        raise ValueError('Failed to add client. The file "{0}" already exists!'.format(filename))
    if old is not False:
        kscfg = old.kickstart_cfg
        kscfg = kscfg.replace(old.ip, form.instance.ip)
        kscfg = kscfg.replace(old.os_release, os_release)
        kscfg = kscfg.replace(old.vlan.cidr, form.instance.vlan.cidr)
        kscfg = kscfg.replace(old.vlan.gateway, form.instance.vlan.gateway)
        kscfg = kscfg.replace(old.name, hostname)
        if old.os_release == 'el5':
            kscfg = kscfg.replace('ext3', fstype)
        if old.os_release == 'el6':
            kscfg = kscfg.replace('ext4', fstype)
        kscfg = kscfg.replace(old.vlan.server_ip, form.instance.vlan.server_ip,)
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
    hostname_ks = FileAsObj()
    hostname_ks.filename = filename
    hostname_ks.contents = kscfg.split('\n')
    if form.cleaned_data['os_release'] == 'el5':
        #
        # EntLinux 5(.5) cannot understand multiple %end statements, remove all then re-add the last one.
        hostname_ks.rm('%end')
        hostname_ks.add('%end')
    #
    # {ksroot}/etc/clients.d/{hostname}.sh - shell variables for post build scripts to use
    filename = os.path.join(CLIENT_DIR, '{0}.sh'.format(hostname))
    if os.path.isfile(filename):
        raise ValueError('Failed to add client. The file "{0}" already exists!'.format(filename))
    client_sh = FileAsObj()
    client_sh.filename = filename

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
    return form


def client_delete(client):
    """
    Files to update: (these files must exist)
        pxeconf
        hostsfile
        allowfile
        
    Files to remove: (ok if already do not exist)
        tftp_pxe
        hostname_ks
        client_sh
    """
    # client = obj.old
    hostname = client.name
    mac_addr = client.mac
    client_ip = client.ip
    dashmac = '-'.join(mac_addr.split(':'))
    dashmac = '01-{0}'.format(dashmac)
    #
    file = FileAsObj(etc_pxe_clients_conf, verbose=True)  # /opt/kickstart/etc/pxe_clients.conf
    file.rm(file.grep(mac_addr))
    pattern = ' {0}.{1} '.format(hostname, ks_domainname)
    file.rm(file.grep(pattern))
    if not file.virgin:
        file.write()
    #
    file = FileAsObj(etc_hosts, verbose=True)  # /etc/hosts
    pattern = '{0} # Kickstart Client '.format(hostname)
    file.rm(file.grep(pattern))
    pattern = '^{0} '.format(client_ip)
    file.rm(file.egrep(pattern))
    if not file.virgin:
        file.write()
    #
    file = FileAsObj(etc_hosts_allow, verbose=True)  # /etc/hosts.allow
    pattern = 'ALL: ALL@{0} : ALLOW'.format(client_ip)
    file.rm(pattern)
    if not file.virgin:
        file.write()
    #
    for this in [os.path.join(TFTP, dashmac),
                 os.path.join(KS_CONF_DIR, '{0}.ks'.format(hostname)),
                 os.path.join(CLIENT_DIR, '{0}.sh'.format(hostname)),
                 ]:
        if os.path.isfile(this):
            newname = '{0}_{1}'.format(os.path.basename(this), int(time.time()))
            target = os.path.join(BK_DIR, newname)
            shutil.move(this, target)
    #
    return


def update_kickstart_file(form):
    """
    Update The kickstart config file for a client:
    """
    filename = os.path.join(KS_CONF_DIR, '{0}.ks'.format(form.instance.name))
    content = form.cleaned_data['kickstart_cfg'].replace('\r', '')
    #
    file = FileAsObj(filename, verbose=True)  # /opt/kickstart/etc/ks.d/hostname.ks
    file.contents = [content]
    file.write()
    return form
