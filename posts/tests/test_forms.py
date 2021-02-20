import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post
from yatube.settings import BASE_DIR

User = get_user_model()

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)

MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    group = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.form = PostForm()
        cls.user = User.objects.create(username='SlavaKVS')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание тестовой группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

        form_data = {
            'group': PostCreateFormTests.group.id,
            'text': 'Тестовый пост',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.post.author,
                text=self.post.text,
                group=self.post.group,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """При редактировании поста, изменяется запись в базе данных."""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Измененный пост',
            'group': self.group.id,
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.user,
        )
        kwargs = {'username': self.user.username, 'post_id': test_post.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs=kwargs),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse('posts:post', kwargs=kwargs))
