from django.urls import path

from rest_framework.routers import SimpleRouter

from .views import BookViewSet

router = SimpleRouter()

router.register(r'book', BookViewSet)

urlpatterns = []

urlpatterns += router.urls

# urlpatterns = [
#     path('book/', BookViewSet.as_view({'get': 'list'}))
# ]
