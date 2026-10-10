from django.db import models
from django.core.exceptions import ValidationError

from .validators import validate_repository_url, validate_technologies


class Project(models.Model):
    title = models.CharField(max_length=140)
    repository_url = models.URLField(
        max_length=300, unique=True, validators=[validate_repository_url]
    )
    technologies = models.JSONField(default=list, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "project"

    def clean(self):
        super().clean()
        try:
            validate_technologies(self.technologies)
        except ValidationError as exc:
            raise ValidationError({"technologies": exc.messages}) from exc

    def __str__(self):
        return self.title


class ProjectTranslation(models.Model):
    class Language(models.TextChoices):
        ENGLISH = "en", "English"
        SPANISH = "es", "Español"
        FRENCH = "fr", "Français"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="translations"
    )
    language = models.CharField(max_length=2, choices=Language.choices)
    category = models.CharField(max_length=180)
    description = models.TextField()

    class Meta:
        db_table = "project_translation"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "language"],
                name="unique_project_translation_language",
            )
        ]

    def __str__(self):
        return f"{self.project.title} ({self.language})"
