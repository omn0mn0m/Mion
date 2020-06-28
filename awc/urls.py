from django.urls import path

from . import views

app_name = 'awc'

urlpatterns = [
    path('', views.index, name='index'),
    path('edit/<str:challenge_name>/', views.edit, name='edit'),
    #path('create-submission/<str:challenge_name>/', views.create_submission, name='create-submission'),
    path('add-challenge/', views.add_challenge, name='add-challenge'),
    path('add-existing-submission/', views.add_existing_submission, name='add-existing-submission'),

    # Functions
    path('authenticate', views.authenticate, name='authenticate'),
    path('logout', views.logout, name='logout'),
    path('submit-post/<str:challenge_name>/<int:thread_id>/<int:comment_id>/', views.submit_post, name='submit-post'),
    path('delete-post/<int:comment_id>/', views.delete_post, name='delete-post'),
]
