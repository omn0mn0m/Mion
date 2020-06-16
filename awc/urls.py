from django.urls import path

from . import views

app_name = 'awc'

urlpatterns = [
    path('', views.index, name='index'),
    path('edit/<str:challenge_name>/', views.edit, {'edit': True}, name='edit'),
    path('edit/<str:challenge_name>/new', views.edit, {'edit': False}, name='edit-new'),
    #path('create-submission/<str:challenge_name>/', views.create_submission, name='create-submission'),
    path('add-challenge/', views.add_challenge, name='add-challenge'),
    path('add-existing-submission/', views.add_existing_submission, name='add-existing-submission'),

    # Functions
    path('authenticate', views.authenticate, name='authenticate'),
    path('logout', views.logout, name='logout'),
    path('delete-submission/<int:comment_id>/', views.delete_submission, name='delete-submission'),
]
