import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post
from posts.forms import PostForm

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
TEST_COUNT = 99


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='JustName')
        cls.follow_user = User.objects.create_user(username='AnotherName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы',
        )
        cls.another_group = Group.objects.create(
            title='Другая группа',
            slug='another_group',
            description='Тестовое описание другой  группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x00'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста1',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.post_id = PostPagesTests.post.id
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_reverse_name = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'JustName'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': self.post_id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in template_reverse_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_post_comparator(self, context, post):
        try:
            page_obj = context['page_obj'][0]
        except KeyError:
            page_obj = context['post']
        self.assertEqual(page_obj.id, post.id)
        self.assertEqual(page_obj.text, post.text)
        self.assertEqual(page_obj.author, post.author)
        self.assertEqual(page_obj.group, post.group)
        self.assertEqual(page_obj.image, post.image)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.context_post_comparator(
            response.context,
            PostPagesTests.post,
        )

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug})
        )
        group_object = response.context['group']
        group_title = group_object.title
        group_slug = group_object.slug
        group_description = group_object.description
        self.assertEqual(group_title, 'Тестовая группа')
        self.assertEqual(group_slug, PostPagesTests.group.slug)
        self.assertEqual(group_description, 'Тестовое описание группы')
        self.context_post_comparator(
            response.context,
            PostPagesTests.post,
        )

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'JustName'})
        )
        author_object = response.context['author']
        author_username = author_object.username
        self.assertEqual(author_username, 'JustName')
        self.context_post_comparator(
            response.context,
            PostPagesTests.post,
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_id})
        )
        self.context_post_comparator(
            response.context,
            PostPagesTests.post,
        )

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_id})
        )
        post_id = response.context['form'].instance.id
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(post_id, self.post_id)

    def test_post_create_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_not_in_incorrect_group(self):
        """Пост не сохраняется в неправильной группе."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostPagesTests.another_group.slug})
        )
        self.assertNotIn(PostPagesTests.post, response.context['page_obj'])

    def test_follow_work_correct(self):
        """Подписка работает правильно."""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.follow_user.username})
        )
        follow = Follow.objects.filter(
            user=PostPagesTests.user,
            author=User.objects.get(
                username=PostPagesTests.follow_user.username)
        ).exists()
        self.assertTrue(follow)
        unfollow_user = User.objects.create_user(username='AnotherName2')
        unfollow_client = Client()
        unfollow_client.force_login(unfollow_user)
        follow_post = Post.objects.create(
            text='Текст для теста подписок',
            author=PostPagesTests.follow_user,
        )
        Post.objects.create(
            text='Неправильный текст для теста подписок',
            author=unfollow_user,
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        page_objects = response.context['page_obj']
        self.assertIn(follow_post, page_objects)
        response = unfollow_client.get(
            reverse('posts:follow_index')
        )
        page_objects = response.context['page_obj']
        self.assertNotIn(follow_post, page_objects)

    def test_unfollow_work_correct(self):
        """Отписка работает правильно."""
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostPagesTests.follow_user.username}
            )
        )
        unfollow = Follow.objects.filter(
            user=PostPagesTests.user,
            author=User.objects.get(
                username=PostPagesTests.follow_user.username)
        ).exists()
        self.assertFalse(unfollow)


class PaginatorViewsTest(TestCase):
    """Паджинатор правильно разбивает страницы."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='JustName')
        cls.another_user = User.objects.create_user(username='JustAnotherName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание тестовой группы',
        )
        objs = [
            Post(
                text=f'Текст тестового поста{x}',
                author=cls.user,
                group=cls.group,
            )
            for x in range(TEST_COUNT)
        ]
        Post.objects.bulk_create(objs=objs)
        Follow.objects.create(
            user=cls.another_user,
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        cache.clear()

    def paginator_pages_test(self, url, client):
        response_first = client.get(url)
        page_obj = response_first.context['page_obj']
        first_page_value = page_obj.paginator.per_page
        self.assertEqual(len(page_obj), first_page_value)
        page_index = TEST_COUNT // first_page_value
        last_page_value = TEST_COUNT % first_page_value
        response_last = (
            client.get(url + f'?page={page_index + 1}'))
        page_obj_last = response_last.context['page_obj']
        self.assertEqual(len(page_obj_last), last_page_value)

    def test_index_paginator(self):
        client = self.authorized_client
        url = reverse('posts:index')
        self.paginator_pages_test(url, client)

    def test_group_list_paginator(self):
        client = self.authorized_client
        url = reverse(
            'posts:group_list',
            kwargs={'slug': PaginatorViewsTest.group.slug}
        )
        self.paginator_pages_test(url, client)

    def test_profile_paginator(self):
        client = self.authorized_client
        url = reverse('posts:profile', kwargs={'username': 'JustName'})
        self.paginator_pages_test(url, client)

    def test_follow_index_paginator(self):
        client = Client()
        client.force_login(PaginatorViewsTest.another_user)
        url = reverse('posts:follow_index')
        self.paginator_pages_test(url, client)
