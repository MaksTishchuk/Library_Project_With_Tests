from django.urls import path

from rest_framework.routers import SimpleRouter

from .views import BookViewSet, auth

router = SimpleRouter()

router.register(r'book', BookViewSet)

urlpatterns = [
    path('auth/', auth)
]

urlpatterns += router.urls

# urlpatterns = [
#     path('book/', BookViewSet.as_view({'get': 'list'}))
# ]
