from django.contrib import admin

from .models import Project, ProjectTranslation


class ProjectTranslationInline(admin.StackedInline):
    model = ProjectTranslation
    extra = 1
    max_num = 3


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "repository_url", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "translations__category", "translations__description")
    ordering = ("title",)
    inlines = (ProjectTranslationInline,)
