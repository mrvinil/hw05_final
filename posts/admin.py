from django.contrib import admin

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "slug")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    empty_value_display = "-пусто-"


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'text', 'post', 'created')
    list_filter = ('created', )
    search_fields = ('author', 'text')


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user', 'author')


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
