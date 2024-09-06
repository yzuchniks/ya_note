from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты путей."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Username')
        cls.note = Note.objects.create(
            title='Test note',
            text='Test text',
            slug='slug',
            author=cls.user,
        )
        cls.limited_access = (
            ('notes:add', None),
            ('notes:list', None),
            ('notes:edit', (cls.note.slug,)),
            ('notes:detail', (cls.note.slug,)),
            ('notes:delete', (cls.note.slug,)),
        )

    def test_pages_availability(self):
        """Проверка доступности адресов для анонимного пользователя."""
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_authorized_client(self):
        """Проверка доступности адресов для авторизованного пользователя."""
        self.client.force_login(self.user)
        for name, slug in self.limited_access:
            with self.subTest(name=name, slug=slug):
                url = reverse(name, args=slug)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """
        Проверка редиректа на страницу входа
        для неавторизованного пользователя.
        """
        login_url = reverse('users:login')
        for name, slug in self.limited_access:
            with self.subTest(name=name, slug=slug):
                url = reverse(name, args=slug)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
