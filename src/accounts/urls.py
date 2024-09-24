from django.urls import path, include
from .api import router as api_router

urlpatterns = [
    # Include the API URLs under 'api/'
    path('api/', include((api_router.api_urlpatterns, 'accounts_api'), namespace='accounts_api')),
]