from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):

    def test_serializer(self):
        user1 = User.objects.create(username='user1', first_name='Maksim', last_name='Tishchyk')
        user2 = User.objects.create(username='user2', first_name='Maks', last_name='Vitman')

        book_1 = Book.objects.create(name='Test Book 1', price=25,
                                     author_name='Author 1', owner=user2)
        book_2 = Book.objects.create(name='Test Book 2', price=50,
                                     author_name='Author 2', owner=user1)

        UserBookRelation.objects.create(user=user1, book=book_1, like=True, rating=5)
        UserBookRelation.objects.create(user=user2, book=book_1, like=True, rating=4)

        UserBookRelation.objects.create(user=user1, book=book_2, like=True, rating=4)
        UserBookRelation.objects.create(user=user2, book=book_2, like=True, rating=3)

        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rating')
        ).order_by('id')
        data = BooksSerializer(books, many=True).data
        expected_data = [
            {
                'id': book_1.id,
                'name': 'Test Book 1',
                'price': '25.00',
                'author_name': 'Author 1',
                'owner_name': 'user2',
                'annotated_likes': 2,
                'rating': '4.50',
                'readers_book': [
                    {
                        'first_name': 'Maksim',
                        'last_name': 'Tishchyk'
                    },
                    {
                        'first_name': 'Maks',
                        'last_name': 'Vitman'
                    }
                ]
            },
            {
                'id': book_2.id,
                'name': 'Test Book 2',
                'price': '50.00',
                'author_name': 'Author 2',
                'owner_name': 'user1',
                'annotated_likes': 2,
                'rating': '3.50',
                'readers_book': [
                    {
                        'first_name': 'Maksim',
                        'last_name': 'Tishchyk'
                    },
                    {
                        'first_name': 'Maks',
                        'last_name': 'Vitman'
                    }
                ]
            },
        ]
        self.assertEqual(data, expected_data)

