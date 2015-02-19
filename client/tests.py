"""
client/tests.py
"""
from django.db.utils import IntegrityError
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from client.models import Client


def get_one():
    """
    Provide a properly formatted client object.
    """
    return Client.objects.create(
        name='mailserver01',
        mac='01:02:03:04:05:06',
        ip='127.0.0.1',
        build_type='01',
        os_release='el5'
    )


class ClientTestCase(TestCase):
    def test_tester_ok(self):
        # Ensure testing client validates OK.
        self.assertIsNone(get_one().full_clean())

    def test_empty(self):
        # Ensure can't make an empty client.
        with self.assertRaises(IntegrityError):
            Client.objects.create()

    def test_missing(self):
        self.assertEqual(Client.objects.filter(name='    missing    ').count(), 0)

    def test_find(self):
        get_one()
        count = Client.objects.filter(name='mailserver01').count()
        self.assertEqual(count, 1)

    def test_name_underbar(self):
        this = get_one()
        with self.assertRaises(ValidationError):
            this.name = '_'
            this.full_clean()

    def test_ip_underbar(self):
        this = get_one()
        with self.assertRaises(ValidationError):
            this.ip = '_'
            this.full_clean()

    def test_mac_underbar(self):
        this = get_one()
        with self.assertRaises(ValidationError):
            this.mac = '_'
            this.full_clean()

    def test_client_in_client_list(self):
        # Ensure new client shows in list of clients
        get_one()
        response = self.client.get(reverse('client:index'))
        self.assertQuerysetEqual(
            response.context['client_list'],
            ['<Client: mailserver01>']
        )
