"""
    Running:
        python 3.4.1 && django 1.7c2


Really sick of screwing up plural/non-plural names; I know where it makes sense to add an 's'; but it burned so much typo/recompile time in the past
I'm just going to make everything singular going forward.


    TODO:

Auth:
    py3+ldap && a couple local backup accounts though it kills me that i'd have to enforce access controls for this project.
    crazy suits.
    For locals override username with lower(email)
    
    I think we're going to use the is_staff flag on account to determine if they can edit/add kickstart clients and vlans.
    My philosophy stands that all users who can get to the site should have read-access.
    If you have to hide client/server info from your employees what the fsck kind of business are you running?

django-braces:
    I'm trying this again, still don't like it. It's a gigantic trade-off, giving up customization for a slightly thinner code-base.

Files we modify: 

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

"""
