from django.contrib import admin
from .models import VideoPost, Like, Comment, Follower

admin.site.register(VideoPost)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Follower)
