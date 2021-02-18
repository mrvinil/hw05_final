from django.views.decorators.cache import cache_page
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post

User = get_user_model()


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


def index(request):
    """Главная страница со списком постов."""
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {
            'page': page,
            'posts': posts,
            'paginator': paginator
        }
    )


def group_posts(request, slug):
    """Страница с постами группы"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {
            'group': group,
            'page': page,
            'paginator': paginator
        }
    )


@login_required
def new_post(request):
    """Создаем новый пост."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/new.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:index')


@login_required
def post_edit(request, username, post_id):
    """Страница редактирования поста"""
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect('posts:post', post.author, post.id)

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if not form.is_valid():
        return render(
            request,
            'posts/new.html',
            {
                'form': form,
                'post': post,
                'is_edit': True
            }
        )
    form.save()
    return redirect('posts:post', post.author, post.id)


def profile(request, username):
    """Страница профиля пользователя."""
    author_posts = get_object_or_404(User, username=username)
    posts = author_posts.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'profile.html',
        {
            'page': page,
            'author_posts': author_posts,
            'paginator': paginator
        }
    )


def post_view(request, username, post_id):
    """Станица просмотра отдельного поста."""
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()
    return render(
        request,
        'posts/post.html',
        {
            'post': post,
            'author_posts': post.author,
            'comments': comments,
            'form': form,
            'display_add_comment': True
        }
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post', post.author, post.id)
