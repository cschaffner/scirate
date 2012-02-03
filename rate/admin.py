from rate.models import Article, UserProfile, Comment, DownloadAction
from django.contrib import admin

admin.site.register(Article)
admin.site.register(UserProfile)
admin.site.register(Comment)

class DownloadActionAdmin(admin.ModelAdmin):
    list_display = ('download_time', 'num_new_articles', 'num_updated_articles')

admin.site.register(DownloadAction, DownloadActionAdmin)



