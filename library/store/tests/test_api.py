import json

from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BooksApiTestCase(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='test_username')
        self.book_1 = Book.objects.create(name='Test Book 1', price=50,
                                          author_name='Author 1', owner=self.user)
        self.book_2 = Book.objects.create(name='Test Book 2', price=25,
                                          author_name='Author 2', owner=self.user)
        self.book_3 = Book.objects.create(name='Test Book Author 1', price=75,
                                          author_name='Author 2', owner=self.user)

        UserBookRelation.objects.create(user=self.user, book=self.book_1, like=True, rating=5)

    def test_get(self):
        url = reverse('book-list')
        response = self.client.get(url)
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rating')
        ).order_by('id')

        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[0]['rating'], '5.00')
        self.assertEqual(serializer_data[0]['annotated_likes'], 1)

    def test_get_filter(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'price': 50})
        books = Book.objects.filter(id__in=[self.book_1.id, ]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rating')
        ).order_by('id')

        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})
        books = Book.objects.filter(id__in=[self.book_1.id, self.book_3.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rating')
        ).order_by('id')

        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_ordering(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': 'price'})
        books = Book.objects.filter(id__in=[self.book_2.id, self.book_1.id,
                                    self.book_3.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            rating=Avg('userbookrelation__rating')
        ).order_by('price')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_create(self):
        self.assertEqual(Book.objects.all().count(), 3)
        url = reverse('book-list')
        data = {
            "name": "PostmanCreate",
            "price": 777.77,
            "author_name": "Somebody from Postman"
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.post(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(Book.objects.all().count(), 4)
        self.assertEqual(Book.objects.last().owner, self.user)

    def test_update(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 666,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(666, self.book_1.price)

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username='test_username2')
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 666,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual({'detail': ErrorDetail(
            string='У вас недостаточно прав для выполнения данного действия.',
            code='permission_denied')}, response.data)
        self.book_1.refresh_from_db()
        self.assertEqual(50, self.book_1.price)

    def test_delete(self):
        self.assertEqual(Book.objects.all().count(), 3)
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(Book.objects.all().count(), 2)

    def test_delete_not_owner(self):
        self.user2 = User.objects.create(username='test_username2')
        self.assertEqual(Book.objects.all().count(), 3)
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user2)
        response = self.client.delete(url)
        self.assertEqual({'detail': ErrorDetail(
            string='У вас недостаточно прав для выполнения данного действия.',
            code='permission_denied')}, response.data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(Book.objects.all().count(), 3)

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_username2', is_staff=True)
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "price": 666,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(666, self.book_1.price)

    def test_delete_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_username2', is_staff=True)
        self.assertEqual(Book.objects.all().count(), 3)
        url = reverse('book-detail', args=(self.book_1.id,))
        self.client.force_login(self.user2)
        response = self.client.delete(url)
        self.assertEqual(None, response.data)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(Book.objects.all().count(), 2)


class BooksRelationTestCase(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username2')
        self.book_1 = Book.objects.create(name='Test Book 1', price=50,
                                          author_name='Author 1', owner=self.user)
        self.book_2 = Book.objects.create(name='Test Book 2', price=25,
                                          author_name='Author 2', owner=self.user)

    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            'like': True,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertTrue(relation.like)

        data2 = {
            'in_bookmarks': True,
        }
        json_data2 = json.dumps(data2)
        response = self.client.patch(url, data=json_data2, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation2 = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertTrue(relation2.in_bookmarks)

    def test_rating(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            'rating': 4,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertTrue(4, relation.rating)

    def test_rating_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))

        data = {
            'rating': 13,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)


