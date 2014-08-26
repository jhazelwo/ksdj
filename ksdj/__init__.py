"""
    Running:
        python 3.4.1 && django 1.7c2


Really sick of screwing up plural/non-plural names; I know where it makes sense to add an 's'; but I burned so much typo/recompile time in the past
I'm just going to make everything singular going forward.


    TODO:

Auth:
    py3+ldap && a couple local backup accounts though it kills me that i'd have to enforce access controls for this project.
    crazy suits.
    For locals override username with lower(email)
    
    I wonder if I can trim down the LOC count for human.LogOut() without using a FBV

vlan_modify
    I've decided to do a 'delete, then create' for the update function instead of editing/moving files because I believe D&C will prove
    to be more robust in the future if we get into an out-of-sync situation where files were manually moved/changed/deleted on the ks server
    I'll be doing the same with clients when I get there.



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
