from django.urls import path

from rest_framework.routers import SimpleRouter

from .views import BookViewSet, auth, UserBooksRelationView

router = SimpleRouter()

router.register(r'book', BookViewSet)
router.register(r'book-relation', UserBooksRelationView)

urlpatterns = []

urlpatterns += router.urls

# urlpatterns = [
#     path('book/', BookViewSet.as_view({'get': 'list'}))
# ]
