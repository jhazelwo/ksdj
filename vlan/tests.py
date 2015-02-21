"""
VLAN/tests.py
"""
from django.db.utils import IntegrityError
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from vlan.models import VLAN


def get_one():
    """
    Provide a properly formatted client object.
    """
    return VLAN.objects.create(
        name='1029',
        network='10.29.0.0',
        server_ip='10.29.0.100',
        gateway='10.29.0.1',
        cidr='255.255.255.0',
        active=True
    )


class VLANTestCase(TestCase):
    def test_tester_ok(self):
        self.assertIsNone(get_one().full_clean())

    def test_empty(self):
        # Empty create is OK, but make sure it wouldn't validate.
        with self.assertRaises(ValidationError):
            this = VLAN.objects.create()
            this.full_clean()

    def test_missing(self):
        get_one()
        self.assertFalse(VLAN.objects.filter(name=' ` ` ` `missing / / | | | '))

    def test_find(self):
        get_one()
        count = VLAN.objects.filter(name='1029').count()
        self.assertEqual(count, 1)

    def test_name_underbar(self):
        this = get_one()
        with self.assertRaises(ValidationError):
            this.name = '_'
            this.full_clean()

    def test_vlan_in_vlan_list(self):
        get_one()
        response = self.client.get(reverse('vlan:index'))
        self.assertQuerysetEqual(
            response.context['vlan_list'],
            ['<VLAN: 1029>']
        )
