from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='JustName')
        cls.user2 = User.objects.create_user(username='AnotherName')
        Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание тестовой группы',
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста',
            author=URLTests.user,
        )
        cls.guest_urls = [
            '/',
            '/group/test_group/',
            f'/profile/{URLTests.user.username}/',
            f'/posts/{URLTests.post.id}/',
        ]
        cls.autorised_urls = [
            '/',
            '/group/test_group/',
            f'/profile/{URLTests.user.username}/',
            f'/posts/{URLTests.post.id}/',
            '/create/',
            f'/posts/{URLTests.post.id}/edit/',
            '/follow/',
        ]
        cls.login_redirect_urls = [
            '/create/',
            f'/posts/{URLTests.post.id}/edit/',
            '/follow/',
            f'/posts/{URLTests.post.id}/comment/',
            f'/profile/{URLTests.user.username}/follow/',
            f'/profile/{URLTests.user.username}/unfollow/',
        ]
        cls.normal_redirect_urls = [
            f'/posts/{URLTests.post.id}/comment/',
            f'/profile/{URLTests.user.username}/follow/',
            f'/profile/{URLTests.user.username}/unfollow/',
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(URLTests.user)
        cache.clear()

    def test_urls_guest_status_200(self):
        """Гостевые сраницы доступны."""
        for url in URLTests.guest_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_autorised_status_200(self):
        """Авторизованные страницы доступны."""
        for url in URLTests.autorised_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_redirect(self):
        """
        Неавторизованный пользователь правильно редиректится
        с приватных страниц
        """
        for url in URLTests.login_redirect_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                expected_url = '/auth/login/?next=' + url
                self.assertRedirects(response, expected_url)

    def test_wrong_author_redirect(self):
        self.authorized_client.force_login(URLTests.user2)
        post_id = URLTests.post.id
        url = f'/posts/{post_id}/edit/'
        response = self.authorized_client.get(url)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': post_id}
            )
        )

    def test_urls_status_302(self):
        for url in URLTests.normal_redirect_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_wrong_url_404_status(self):
        """Ответ 404 на неверный запрос."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_return_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        url_template = {
            '/': 'posts/index.html',
            '/group/test_group/': 'posts/group_list.html',
            f'/profile/{URLTests.user.username}/': 'posts/profile.html',
            f'/posts/{URLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{URLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
            f'/posts/{URLTests.post.id}/comment/': 'posts/post_detail.html',
            f'/profile/{URLTests.user.username}/follow/': 'posts/follow.html',
            f'/profile/{URLTests.user.username}/unfollow/': 'posts/follow.html'
        }
        for url, template in url_template.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url, follow=True)
                self.assertTemplateUsed(response, template)

    def test_urls_index_is_cached(self):
        response1 = self.authorized_client.get(reverse('posts:index'))
        content1 = response1.content
        Post.objects.all().delete()
        response2 = self.authorized_client.get(reverse('posts:index'))
        content2 = response2.content
        self.assertEqual(content1, content2)
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))
        content3 = response3.content
        self.assertNotEqual(content1, content3)
