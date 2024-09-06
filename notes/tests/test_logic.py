from http import HTTPStatus
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


class TestNoteEditDelete(TestCase):
    """Тесты редактирования и удаления заметки."""
    NOTE_TEXT = 'Текст заметки'
    NOTE_TITLE = 'Заголовок заметки'
    NEW_NOTE_TEXT = 'Новый текст заметки'
    NEW_NOTE_TITLE = 'Новый заголовок заметки'
    DONE_URL = reverse('notes:success')

    @classmethod
    def setUpTestData(cls):
        cls.good_user = User.objects.create(username='GoodUser')
        cls.bad_user = User.objects.create(username='BadUser')
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            author=cls.good_user,
        )
        arg_slug = (cls.note.slug,)
        cls.edit_url = reverse('notes:edit', args=arg_slug)
        cls.delete_url = reverse('notes:delete', args=arg_slug)
        cls.good_client = Client()
        cls.good_client.force_login(cls.good_user)
        cls.bad_client = Client()
        cls.bad_client.force_login(cls.bad_user)
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE, 'text': cls.NEW_NOTE_TEXT
        }

    def test_author_can_delete_note(self):
        """Автор заметки может удалить заметку."""
        response = self.good_client.post(self.delete_url)
        self.assertRedirects(response, self.DONE_URL)
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Другой пользователь не может удалить заметку."""
        self.bad_client.post(self.delete_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_anonymous_cant_delete_note(self):
        """Анонимный пользователь не может удалить заметку."""
        self.client.post(self.delete_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        """Автор заметки может редактировать заметку."""
        response = self.good_client.post(self.edit_url, self.form_data)
        self.assertRedirects(response, self.DONE_URL)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_other_user_cant_edit_note(self):
        """Другой пользователь не может редактировать заметку."""
        response = self.bad_client.post(self.edit_url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_anonymous_cant_edit_note(self):
        """Анонимный пользователь не может редактировать заметку."""
        self.client.post(self.edit_url, self.form_data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)
