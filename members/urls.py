from django.urls import path
from . import views
from . import business_card
from . import export

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('', views.MemberListView.as_view(), name='member_list'),
    path('add/', views.MemberCreateView.as_view(), name='member_add'),
    path('<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),
    path('<int:pk>/edit/', views.MemberUpdateView.as_view(), name='member_edit'),
    path('<int:pk>/delete/', views.MemberDeleteView.as_view(), name='member_delete'),
    path('<int:pk>/card/', business_card.business_card, name='business_card'),
    path('export/csv/', export.export_members_csv, name='member_export_csv'),
]
