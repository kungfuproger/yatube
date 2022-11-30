from django.contrib import admin

from .models import Group, Post, Comment, Follow


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'description', 'created', 'slug',)
    list_display_links = ('pk', 'title', 'created',)
    search_fields = ('title', 'description',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


class CommentInLine(admin.TabularInline):
    model = Comment


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'created', 'author', 'group',)
    list_display_links = ('pk', 'text', 'created')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'
    inlines = [CommentInLine]


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'created', 'author', 'post')
    list_display_links = ('pk', 'text', 'created')
    search_fields = ('text',)
    list_filter = ('created',)


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author',)
    list_editable = ('user', 'author',)
    list_filter = ('created',)


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
