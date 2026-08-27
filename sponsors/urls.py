from django.urls import path
from . import views

urlpatterns = [
    path('', views.SponsorListView.as_view(), name='sponsor_list'),
    path('add/', views.SponsorCreateView.as_view(), name='sponsor_add'),
    path('<int:pk>/', views.SponsorDetailView.as_view(), name='sponsor_detail'),
    path('<int:pk>/edit/', views.SponsorUpdateView.as_view(), name='sponsor_edit'),
    path('<int:pk>/delete/', views.SponsorDeleteView.as_view(), name='sponsor_delete'),
    path('<int:sponsor_pk>/contribute/', views.add_contribution, name='add_contribution'),
]
