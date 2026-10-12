from django.db import models
from django.core.exceptions import ValidationError

from .validators import validate_repository_url, validate_technologies


class ContentLanguage(models.TextChoices):
    ENGLISH = "en", "English"
    SPANISH = "es", "Español"
    FRENCH = "fr", "Français"


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
    Language = ContentLanguage

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


class Experience(models.Model):
    """A portfolio-safe record of a professional experience."""

    company = models.CharField(max_length=120)
    company_url = models.URLField(max_length=300, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    technologies = models.JSONField(default=list, blank=True)
    logo = models.ImageField(upload_to="images/", blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "experience"
        ordering = ["display_order", "company"]
        verbose_name_plural = "experiences"

    def clean(self):
        super().clean()
        try:
            validate_technologies(self.technologies)
        except ValidationError as exc:
            raise ValidationError({"technologies": exc.messages}) from exc

    def __str__(self):
        return self.company


class ExperienceTranslation(models.Model):
    Language = ContentLanguage

    experience = models.ForeignKey(
        Experience, on_delete=models.CASCADE, related_name="translations"
    )
    language = models.CharField(max_length=2, choices=Language.choices)
    role = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    overview = models.TextField(blank=True)
    accomplishments = models.TextField(
        blank=True, help_text="Enter one accomplishment per line."
    )

    class Meta:
        db_table = "experience_translation"
        constraints = [
            models.UniqueConstraint(
                fields=["experience", "language"],
                name="unique_experience_translation_language",
            )
        ]

    def __str__(self):
        return f"{self.experience.company} ({self.language})"

    @property
    def accomplishment_list(self) -> list[str]:
        """Return non-empty accomplishment lines for templates and APIs."""
        return [line.strip() for line in self.accomplishments.splitlines() if line.strip()]
