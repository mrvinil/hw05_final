from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

        user = get_user_model()
        cls.user = user.objects.create(username='leo')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_wrong_url_return_404(self):
        """Если страница не найдена, вернем 404."""
        response = self.guest_client.get('/something_page_404_not_found/')
        self.assertEqual(response.status_code, 404)

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_slug_url_exists_at_desired_location(self):
        """Страница /group/<slug>/ доступна любому пользователю."""
        response = self.guest_client.get(f'/group/{self.group.slug}/')
        self.assertEqual(response.status_code, 200)

    def test_separate_post(self):
        """Доступность URL отдельного поста /<username>/<post_id>/"""
        response = self.guest_client.get(f'/{self.post.author}/{self.post.id}/')
        self.assertEqual(response.status_code, 200)

    def test_page_profile(self):
        """Страница /profile/ доступна для просмотра."""
        response = self.guest_client.get(f'/{self.post.author}/')
        self.assertEqual(response.status_code, 200)

    def test_new_url_exists_at_desired_location_authorization(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_follow_url_exists_at_desired_location_authorization(self):
        """Страница /follow/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/follow/')
        self.assertEqual(response.status_code, 200)

    def test_new_url_redirect_anonymous(self):
        """Страница /new/ перенаправляет анонимного пользователя на
        страницу логина, а после успешного входа, возвращает обратно на /new/.
        """
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_post_edit_anonymous(self):
        """Страница /<username>/<post_id>/edit/ перенаправляет анонимного
        пользователя на страницу логина, а после успешного входа, вернет
        обратно на /<username>/<post_id>/edit/.
        """
        response = self.guest_client.get(
            f'/{self.post.author}/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/{self.post.author}/{self.post.id}/edit/')

    def test_urls_uses_correct_template(self):
        """URLs используют соответствующие шаблоны."""
        templates_url_names = {
            'index.html': '/',
            'group.html': f'/group/{self.group.slug}/',
            'posts/new.html': '/new/',
            'posts/post.html': f'/{self.post.author}/{self.post.id}/'
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_only_author_and_not_author_redirect_post(self):
        """Страница /username/post_id/edit доступна только автору поста.
        Авторизированного пользователя, но не автора поста, перенаправит на
        страницу просмотра этой записи
        """
        url = f'/{self.post.author}/{self.post.id}/edit/'
        user_not_author = User.objects.create_user(username='not_author')
        self.client.force_login(user_not_author)

        response = self.client.get(url)
        self.assertRedirects(response, f'/{self.post.author}/{self.post.id}/')
