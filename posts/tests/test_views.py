import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User
from yatube.settings import BASE_DIR

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)

MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


class GroupPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='leo')
        cls.another_user = User.objects.create(username='esenin')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы'
        )

        cls.group_without_post = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Описание тестовой группы 2'
        )

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        user = get_user_model()
        self.user = user.objects.create_user(username='SlavaKVS')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'index.html': reverse('posts:index'),
            'posts/new.html': reverse('posts:new_post'),
            'group.html': (
                reverse('posts:group', kwargs={'slug': self.group.slug})
            ),
            'profile.html':
                reverse("posts:profile",
                        kwargs={'username': self.post.author}),
            'posts/post.html':
                reverse("posts:post", kwargs={'username': self.post.author,
                                              'post_id': self.post.id})
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('posts')[0], self.post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(response.context.get('post'), self.post)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:group', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context.get('group'), self.group)

    def test_post_got_to_the_index(self):
        """Новый пост попал на главную страницу с нужной группой"""
        group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug4',
            description='Описание тестовой группы'
        )
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=group
        )
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('posts')[0], post)
        self.assertEqual(response.context.get('posts')[0].group, post.group)

    def test_group_page_show_context_in_group(self):
        """Новый пост попал в группу, для которой был предназначен."""
        group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug10',
            description='Описание тестовой группы'
        )
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=group
        )
        response = self.guest_client.get(
            reverse('posts:group', kwargs={'slug': group.slug}))
        self.assertIn(post, response.context['page'])

    def test_group_page_dont_show_context_from_other_group(self):
        """Новый пост не попал в группу, для которой не был предназначен."""
        response = self.guest_client.get(
            reverse('posts:group',
                    kwargs={'slug': self.group_without_post.slug}))
        new_post = response.context['page']
        self.assertNotIn(self.post, new_post)

    def test_new_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post(self):
        """Создание нового поста"""
        posts_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст'
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'), data=form_data, follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=self.post.text).exists())

    def test_authorised_user_can_comment(self):
        """Только авторизированный пользователь может комментировать посты."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'username': self.post.author,
                            'post_id': self.post.id}),
            data=form_data,
            follow=True,

        )
        comments_count_after = Comment.objects.count()
        self.assertEqual(comments_count + 1, comments_count_after)

    def test_cache(self):
        """Тестируем кеширование"""
        post = Post.objects.create(
            text='Закешированная страница',
            author=self.user
        )
        response = self.authorized_client.get(reverse('posts:index'))
        cached_response_content = response.content

        Post.objects.filter(id=post.id).delete()

        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(cached_response_content, response.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Тестовый автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание тестовой группы'
        )
        posts = [
            Post(
                author=cls.user,
                group=cls.group,
                text=str(i)
            )
            for i in range(13)
        ]
        Post.objects.bulk_create(posts)

    def test_first_page_containse_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PageImgTest(TestCase):
    """Тесты с картинками"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create(username='leo')

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug-img',
            description='Описание тестовой группы'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()

    def test_index_with_img_show_context(self):
        """Шаблон index отображает картинки в контексте"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('posts')[0].image,
                         self.post.image)

    def test_profile_with_img_show_context(self):
        """Шаблон profile отображает картинки в контексте"""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_group_with_img_show_context(self):
        """Шаблон group отображает картинки в контексте"""
        response = self.guest_client.get(
            reverse('posts:group', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context.get('page')[0].image,
                         self.post.image)

    def test_post_with_img_show_context(self):
        """Шаблон post отображает картинки в контексте"""
        response = self.guest_client.get(
            reverse(
                'posts:post',
                kwargs={'username': self.post.author,
                        'post_id': self.post.id}))

        self.assertEqual(response.context.get('post').image, self.post.image)


class TestFollowUnfollow(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()

        self.user_follower = User.objects.create_user(
            username='follower',
            email='follower@follower.follower',
            password='str0ngPassw0rd'
        )
        self.user_following = User.objects.create_user(
            username='following',
            email='following@following.following',
            password='veryStr0ngPassw0rd'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_authorised_user_can_follow_unfollow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.
        """
        before = Follow.objects.all().count()
        self.client_auth_follower.get(
            reverse(
                'index:profile_follow',
                kwargs={'username': self.user_following.username}
            )
        )
        after = Follow.objects.all().count()
        self.assertEqual(before + 1, after)

    def test_authorised_user_can_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей.
        """
        followings = Follow.objects.filter(
            user=self.user_follower,
            author=self.user_following
        )
        self.client_auth_follower.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_following})
        )
        self.assertEqual(followings.count(), 1)

    def test_authorised_user_can_unfollow(self):
        """Авторизованный пользователь может удалять из подписок авторов."""
        followings = Follow.objects.filter(
            user=self.user_follower,
            author=self.user_following
        )
        self.client_auth_follower.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_following})
        )
        self.assertEqual(followings.count(), 0)


class TestFollowTape(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='author'
        )
        cls.author_second = User.objects.create(
            username='author_second'
        )
        cls.group1 = Group.objects.create(
            title='test_title1',
            slug='test_slug1',
            description='test_desc1'
        )

        cls.post = Post.objects.create(
            text='test_text',
            author=cls.author,
            group=cls.group1
        )

        cls.post_second = Post.objects.create(
            text='test_text',
            author=cls.author_second
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_new_post_exist_for_followers(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан.
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        cnt_posts = len(response.context['page'])
        self.assertEqual(cnt_posts, 0)

        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_second}))
        followings = Follow.objects.filter(
            user=self.author,
            author=self.author_second
        )
        self.assertEqual(followings.count(), 1)

        response = self.authorized_client.get(reverse('posts:follow_index'))
        cnt_posts = len(response.context['page'])
        self.assertEqual(cnt_posts, 1)

    def test_new_post_exist_for_followers_unfollow(self):
        """Новая запись пользователя не появляется в ленте тех, кто не
        подписан на него.
        """
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author_second})
        )
        followings = Follow.objects.filter(
            user=self.author,
            author=self.author_second
        )
        self.assertEqual(followings.count(), 0)

        response = self.authorized_client.get(reverse('posts:follow_index'))
        cnt_posts = len(response.context['page'])
        self.assertEqual(cnt_posts, 0)
