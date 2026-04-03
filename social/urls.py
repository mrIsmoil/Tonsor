from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('upload/', views.upload_video, name='upload_video'),
    path('like/<int:video_id>/', views.toggle_like, name='toggle_like'),
    path('comment/<int:video_id>/', views.add_comment, name='add_comment'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('follow/<int:barber_id>/', views.toggle_follow, name='toggle_follow'),
    path('save-post/<int:video_id>/', views.toggle_save_post, name='toggle_save_post'),
    path('delete-post/<int:video_id>/', views.delete_video, name='delete_video'),
    path('interactions/<int:video_id>/', views.get_video_interactions, name='get_video_interactions'),
]
