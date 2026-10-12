from django.contrib import admin

from .models import Experience, ExperienceTranslation, Project, ProjectTranslation


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


class ExperienceTranslationInline(admin.StackedInline):
    model = ExperienceTranslation
    extra = 1
    max_num = 3


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("company", "start_date", "end_date", "display_order", "is_published")
    list_editable = ("display_order",)
    list_filter = ("is_published", "end_date")
    search_fields = ("company", "translations__role", "translations__overview")
    inlines = (ExperienceTranslationInline,)
    ordering = ("display_order", "company")
    fieldsets = (
        ("Identity", {"fields": ("company", "company_url", "logo", "display_order", "is_published")}),
        ("Dates", {"fields": ("start_date", "end_date")}),
        ("Technologies", {"fields": ("technologies",)}),
    )
