from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestNoteList(TestCase):
    """Тесты списка заметок."""
    NUM_NOTE = 2
    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create(username='Username')
        cls.user2 = User.objects.create_user(username='AnotherUser')
        cls.note_us1_list = [
            Note(
                title=f'Test note {i}',
                text=f'Test text {i}',
                slug=f'slug{i}',
                author=cls.user1,
            )
            for i in range(cls.NUM_NOTE)
        ]
        Note.objects.bulk_create(cls.note_us1_list)
        cls.note_us_2 = Note.objects.create(
            title='Note 2', text='Text 2', author=cls.user2
        )

    def test_numb_note(self):
        """Проверка количества выводимых заметок."""
        self.client.force_login(self.user1)
        response = self.client.get(self.LIST_URL)
        notes_list = response.context['note_list']
        self.assertEqual(len(notes_list), self.NUM_NOTE)

    def test_note_order(self):
        """Проверка порядка вывода заметок."""
        self.client.force_login(self.user1)
        response = self.client.get(self.LIST_URL)
        notes_list = response.context['note_list']
        id_list = [note.id for note in notes_list]
        self.assertEqual(id_list, sorted(id_list))

    def test_access_to_notes(self):
        """Пользователь видит только свои заметки."""
        self.client.force_login(self.user2)
        response = self.client.get(self.LIST_URL)
        self.assertContains(response, self.note_us_2.title)
        for note in self.note_us1_list:
            self.assertNotContains(response, note.title)


class TestNoteDetail(TestCase):
    """Тесты страницы заметки."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Username')
        cls.note = Note.objects.create(
            title='Test note',
            text='Test text',
            slug='slug',
            author=cls.user,
        )

    def test_note_detail_content(self):
        """Проверка содержимого страницы заметки."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('notes:detail', args=(self.note.slug,))
        )
        content = response.context['note']
        fields = ('title', 'text', 'id')
        for field in fields:
            with self.subTest(field=field):
                self.assertTrue(hasattr(content, field))
                self.assertIsNotNone(getattr(content, field))
