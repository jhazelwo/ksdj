"""
    Running:
        python 3.4.1 && django 1.7c2

    TODO:
    
    vlans
        fileasojb is now in place and ported ipcalc seems to work
        Need to:
            1. decide on a filemgt entry point for vlanCreate to use
            2. pick a name for what is basically core\kickstart.py
            3. port file path variables


core/kickstart.py - Main engine
    client_create
        if DNS returns a client IP that is already in use we fail in an ugly way, fix it.

        make her 80% checking, 20% execution.
        
        warnins vs errors - I've been going with the idea that errors related to input, like a typo in IP, should be warnings (yellow) but
        errors in the subsystem, like failure to update or create a file, should be errors (red). 

core/skel.py
    Variables that are templates we use when creating files
    
core/settings.py
    mostly file and dir locations so we know where to read/write files.


ks/etc/hosts
ks/etc/hosts.allow
ks/etc/pxe_clients.conf
ks/etc/ks.d/{hostname}.ks
ks/etc/clients.d/{hostname}.sh
    CLIENT_HOSTNAME="
    CLIENT_MAC="
    CLIENT_IPADDR="
    CLIENT_NETMASK="
    CLIENT_GATEWAY="
    CLIENT_TYPE="
    CLIENT_OS="
    SERVER_IPADDR="
tftp/01-{mac address}

ks/etc/dhcpd.conf
ks/etc/vlan_XX.conf

Auth:
    py3+ldap && a couple local backup accounts though it kills me that i'd have to enforce access controls for this project.
    crazy suits.
    For locals override username with lower(email)

Really sick of screwing up plural/non-plural names; I know where it makes sense to add an 's'; but it burned so much typo/recompile time in the past I'm just going to make everything singular going forward.
"""
