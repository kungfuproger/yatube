from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def get_paginator(request, queryset=None):
    if queryset is None:
        queryset = Post.objects.select_related('group', 'author')
    paginator = Paginator(queryset, settings.PAGINATOR_CONST)
    page_namber = request.GET.get('page')
    page_obj = paginator.get_page(page_namber)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    context = {
        'page_obj': get_paginator(request),
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    queryset = group.posts.select_related('author')
    context = {
        'group': group,
        'page_obj': get_paginator(request, queryset),
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    queryset = author.posts.select_related('group')
    context = {
        'author': author,
        'page_obj': get_paginator(request, queryset),
    }
    if request.user.is_authenticated and Follow.objects.filter(
            user__exact=request.user,
            author__exact=author
    ).exists():
        context['following'] = True
    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('author')
    comment_form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': comment_form,
    }
    template = 'posts/post_detail.html'
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    context = {
        'form': form,
    }
    template = 'posts/create_post.html'
    if request.method != 'POST':
        return render(request, template, context)
    if not form.is_valid():
        return render(request, template, context)
    form.instance.author = request.user
    form.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_id = post.author.id
    if request.user.id != author_id:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid:
        form.instance.author = request.user
        form.instance.post = post
        form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    queryset = Post.objects.filter(author__following__user__exact=request.user)
    context = {
        'page_obj': get_paginator(request, queryset),
    }
    template = 'posts/follow.html'
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)
    ).delete()
    return redirect('posts:follow_index')
