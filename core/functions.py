# core/functions.py

from .skel import do_dhcpd, do_vlan_conf


def vlancreate(form):
    """
    ks/etc/dhcpd.conf
    ks/etc/vlan_XX.conf
    
    Those functions will either return False or a valid FileAsObj
    """
    dhcpd_conf = do_dhcpd(form)
    if not dhcpd_conf:
        return False
    vlan_conf = do_vlan_conf(form)
    if not vlan_conf:
        return False
    #
    # All is OK, save changes
    dhcpd_conf.write()
    vlan_conf.write()
    return True



def clientcreate(foo=False):
    pass


