"""
URL mapping for the user API
"""

from django.urls import path
from . import views


app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),  # new URL for token authentication  # noqa: E501
    path('me/', views.ManageUserView.as_view(), name='me'),  # new URL for authenticated user management  # noqa: E501
]