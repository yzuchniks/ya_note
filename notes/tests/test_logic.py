from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreate(TestCase):
    """Тесты создания заметки."""
    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Заголовок заметки'
    CREATE_URL = reverse('notes:add')
    DONE_URL = reverse('notes:success')

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Username')
        cls.form_data = {'text': cls.NOTE_TEXT, 'title': cls.NOTE_TITLE}
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        self.client.post(self.CREATE_URL, self.form_data)
        self.assertEqual(Note.objects.count(), 0)

    def test_authuser_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        response = self.auth_client.post(self.CREATE_URL, self.form_data)
        self.assertRedirects(response, self.DONE_URL)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.last()
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.user)

    def test_slug_generated(self):
        """Проверка генерации slug из заголовка заметки."""
        self.auth_client.post(self.CREATE_URL, self.form_data)
        note = Note.objects.last()
        expected_slug = slugify(self.NOTE_TITLE)[:100]
        self.assertEqual(note.slug, expected_slug)

    def test_slug_uniqueness(self):
        """Проверка уникальности slug при создании заметки."""
        self.auth_client.post(self.CREATE_URL, self.form_data)
        slug = Note.objects.last().slug
        response = self.auth_client.post(self.CREATE_URL, self.form_data)
        self.assertFormError(response, 'form', 'slug', slug + WARNING)
        self.assertEqual(Note.objects.count(), 1)
