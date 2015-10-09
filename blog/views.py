# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.http import HttpResponseForbidden, HttpResponse
from blog.models import Post, Tag
from django.shortcuts import get_object_or_404
import json


def feed(request):
    posts = Post.objects.filter(hidden=False).all()
    updated = Post.objects.latest('pub_date').pub_date
    return render_to_response('feed.xml', {'posts': posts, 'updated': updated})


def archive(request):
    posts = Post.objects.filter(hidden=False).all()
    return render_to_response('archive.html', {'posts': posts, 'title': 'Archive'})


def editor(request, slug=None):
    if slug:
        post = get_object_or_404(Post, slug=slug)
    else:
        post = Post()
    if request.method == 'GET':
        if request.user.is_authenticated():
            return render_to_response('editor.html', {'post': post, 'user': request.user})
        else:
            return HttpResponseForbidden('Authenticated only')
    if request.is_ajax():
        if request.method == 'POST':
            data = json.loads(request.body.decode('utf-8'))
            post.title = data['title']
            post.content_raw = data['content']
            post.author = request.user
            post.slug = data['slug']
            tags = data['tags']
            post.save()
            for tag in tags:
                if tag:
                    t, created = Tag.objects.get_or_create(name=tag.strip())
                    post.tag.add(t)
            post.save()
            return HttpResponse(
                json.dumps(
                    {'slug': post.slug}
                )
            )


class IndexView(ListView):
    model = Post
    template_name = 'index.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self, **kwargs):
        return Post.objects.filter(hidden=False).all()

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        title = ''
        context['title'] = title
        return context


class TagView(ListView):
    model = Post
    template_name = 'tag.html'
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self, **kwargs):
        t = Tag.objects.get(name=self.kwargs.get('slug'))
        return Post.objects.filter(tag=t, hidden=False).all()

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        title = self.kwargs.get('slug')
        context['tag'] = Tag.objects.get(name=title)
        context['title'] = title
        return context


class PostView(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        current = self.object
        current.increase_click()

        try:
            next_post = current.get_next_by_pub_date()
        except:
            next_post = None

        try:
            previous_post = current.get_previous_by_pub_date()
        except:
            previous_post = None

        context['next'] = next_post
        context['previous'] = previous_post
        context['title'] = current.title

        return context
