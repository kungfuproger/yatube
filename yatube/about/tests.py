from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):

    def test_about_status_code(self):
        """Страницы about доступны"""
        self.guest_client = Client()
        tested_urls = ['/about/author/', '/about/tech/']
        for url in tested_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
