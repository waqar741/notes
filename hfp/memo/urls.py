from django.urls import path
from . import views

app_name = 'memo'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path("logout/", views.logout_view, name="logout"),
    path('', views.memo_list, name="memo_list"),
    path('create/', views.memo_create, name="memo_create"),
    path('register/', views.register_view, name="register"),
    path('<int:pk>/edit/', views.memo_update, name="memo_update"),
    path('<int:pk>/delete/', views.memo_delete, name="memo_delete"),
]