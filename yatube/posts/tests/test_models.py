from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='authUSERNAME')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Вот такой вот пост, вот об этом',
            author=cls.user,
        )

    def test_models_objects_have_correct_names(self):
        """Метод __str__ объектов post и group корректно работает."""
        group = PostModelTest.group
        post = PostModelTest.post
        object_value = {
            group: 'Тестовая группа',
            post: 'Вот такой вот п'
        }
        for object, expected_value in object_value.items():
            with self.subTest(object=object):
                self.assertEqual(str(object), expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        group = PostModelTest.group
        post = PostModelTest.post
        field_verbose_group = {
            'title': 'Название группы',
            'slug': 'Уникальный идентификатор в URL',
            'description': 'Опсание группы',
        }
        field_verbose_post = {
            'text': 'Текст поста',
            'created': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verbose_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)
        for field, expected_value in field_verbose_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        group = PostModelTest.group
        post = PostModelTest.post
        field_help_text_group = {
            'title': 'Придумайте название группы',
            'slug': 'Придумайте никнейм группы, для адресной строки',
            'description': 'Опишите в чем назначение группы',
        }
        field_help_text_post = {
            'text': 'Напишите свой пост, пусть этот будет самый лучший',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)
        for field, expected_value in field_help_text_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
