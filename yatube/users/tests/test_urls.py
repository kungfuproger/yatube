from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Solo322")

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.auhorised_client = Client()
        self.auhorised_client.force_login(StaticURLTests.user)

    def test_users_guest_status_200(self):
        """Гостевые траницы доступны."""
        tested_urls = [
            '/auth/signup/',
            '/auth/login/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/Ng/61u-ab22660dd8f04e82e3d7/',
            '/auth/reset/done/',
        ]
        for url in tested_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_privat_status_200_(self):
        """Приватные страницы доступны."""
        tested_urls = [
            '/auth/password_change/',
            '/auth/password_change/done/',
            '/auth/logout/',
        ]
        for url in tested_urls:
            with self.subTest(url=url):
                response = self.auhorised_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
