from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import VideoPost, Like, Comment, Follower, SavedPost
from shops.models import BarberProfile

@login_required
def toggle_save_post(request, video_id):
    video = get_object_or_404(VideoPost, id=video_id)
    save_qs = SavedPost.objects.filter(user=request.user, video=video)
    
    if save_qs.exists():
        save_qs.delete()
        saved = False
    else:
        SavedPost.objects.create(user=request.user, video=video)
        saved = True
        
    return JsonResponse({
        'status': 'success',
        'saved': saved
    })

@login_required
def upload_video(request):
    if not request.user.is_barber:
        return redirect('accounts:home')
        
    if request.method == 'POST':
        video = request.FILES.get('video_file')
        caption = request.POST.get('caption', '')
        if video:
            VideoPost.objects.create(
                barber=request.user.barber_profile,
                video_file=video,
                caption=caption
            )
            return redirect('shops:dashboard')
            
    return render(request, 'social/upload_video.html')

@login_required
def toggle_like(request, video_id):
    video = get_object_or_404(VideoPost, id=video_id)
    like_qs = Like.objects.filter(user=request.user, video=video)
    
    if like_qs.exists():
        like_qs.delete()
        liked = False
    else:
        Like.objects.create(user=request.user, video=video)
        liked = True
        
    return JsonResponse({
        'liked': liked,
        'count': video.likes.count()
    })

@login_required
def add_comment(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(VideoPost, id=video_id)
        text = request.POST.get('text', '')
        if text:
            comment = Comment.objects.create(
                user=request.user,
                video=video,
                text=text
            )
            return JsonResponse({
                'status': 'success',
                'id': comment.id,
                'user': request.user.email.split('@')[0], # Simplified username
                'text': comment.text,
                'created_at': 'Just now'
            })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def edit_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
        text = request.POST.get('text', '')
        if text:
            comment.text = text
            comment.save()
            return JsonResponse({'status': 'success', 'text': comment.text})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
        comment.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_video(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(VideoPost, id=video_id)
        
        # Security check: Only the owner (barber) of the post can delete it
        if not hasattr(request.user, 'barber_profile') or video.barber != request.user.barber_profile:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
            
        # Delete original video file from storage
        if video.video_file:
            video.video_file.delete(save=False)
            
        video.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def toggle_follow(request, barber_id):
    barber = get_object_or_404(BarberProfile, id=barber_id)
    if barber.user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot follow yourself'}, status=400)
        
    follow_qs = Follower.objects.filter(client=request.user, barber=barber)
    
    if follow_qs.exists():
        follow_qs.delete()
        following = False
    else:
        Follower.objects.create(client=request.user, barber=barber)
        following = True
        
    return JsonResponse({
        'status': 'success',
        'following': following,
        'count': barber.followers.count()
    })

def get_video_interactions(request, video_id):
    video = get_object_or_404(VideoPost, id=video_id)
    
    likes = video.likes.all().select_related('user')
    comments = video.comments.all().select_related('user').order_by('-created_at')
    
    likes_data = []
    for like in likes:
        likes_data.append({
            'user': like.user.get_full_name() or like.user.username,
            'photo': like.user.profile_photo.url if like.user.profile_photo else None
        })
        
    comments_data = []
    for comment in comments:
        comments_data.append({
            'user': comment.user.get_full_name() or comment.user.username,
            'photo': comment.user.profile_photo.url if comment.user.profile_photo else None,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        })
        
    return JsonResponse({
        'status': 'success',
        'likes': likes_data,
        'comments': comments_data,
        'like_count': video.likes.count(),
        'comment_count': video.comments.count(),
        'caption': video.caption
    })
