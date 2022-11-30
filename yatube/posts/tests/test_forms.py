import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestForms(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='FormsUserName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание тестовой группы',
        )
        cls.post = Post.objects.create(
            text='Test post 1',
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TestForms.user)

    def test_forms_create_post(self):
        """Валидная форма создания записи создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Test post 2',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': 'FormsUserName'}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(image='posts/small.gif').exists())

    def test_forms_edit_post(self):
        """Валидная форма изменения записи изменяет запись в Post."""
        post_id = TestForms.post.id
        form_data = {
            'text': 'Test post 3',
            'group': TestForms.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True,
        )
        text = Post.objects.get(id=post_id).text
        group = Post.objects.get(id=post_id).group
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': post_id}
            )
        )
        self.assertEqual(text, 'Test post 3')
        self.assertEqual(group, TestForms.group)

    def test_forms_add_comment(self):
        """Валидня форма комментария добавляет комментарий к посту."""
        form_data = {
            'text': 'Test comment 1',
            'author': TestForms.user,
            'post': TestForms.post,
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': TestForms.post.id}
            ),
            data=form_data,
            follow=True,
        )
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': TestForms.group.id}
            )
        )
        self.assertEqual(
            response.context['comments'][0].text,
            'Test comment 1'
        )
