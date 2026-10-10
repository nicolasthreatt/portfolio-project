"""Project page and model tests use fictional content."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import include, path

from ..models import Project, ProjectTranslation
from ..views import projects


urlpatterns = [
    path("projects/", projects, name="project-list"),
    path("", include("portfolio.tests.urls")),
]

PROJECT = {
    "title": "Example Project",
    "category": "Data engineering",
    "description": "Processes example data.",
    "repository_url": "https://github.com/example/project",
    "technologies": ["Python", "SQL"],
}
PROFILE = {
    "full_name": "Example Person",
    "profession": "Engineer",
    "email": "",
    "github_url": "https://github.com/example",
    "linkedin_url": "",
}


def create_project(data=None, published=True):
    data = {**PROJECT, **(data or {})}
    project = Project.objects.create(
        title=data["title"],
        repository_url=data["repository_url"],
        technologies=data["technologies"],
        is_published=published,
    )
    ProjectTranslation.objects.create(
        project=project, language="en",
        category=data["category"], description=data["description"],
    )
    return project


@override_settings(
    ALLOWED_HOSTS=["testserver"], SITE_PROFILE=PROFILE, ROOT_URLCONF=__name__
)
class ProjectsTests(TestCase):
    def setUp(self):
        self.project = create_project()

    def add_translations(self):
        for language, category, description in (
            ("es", "Ingeniería de datos", "Procesa datos de ejemplo."),
            ("fr", "Ingénierie des données", "Traite des données exemples."),
        ):
            ProjectTranslation.objects.create(
                project=self.project, language=language,
                category=category, description=description,
            )

    def test_page_renders_content_and_shared_profile(self):
        response = self.client.get("/projects/")
        self.assertContains(response, "Projects | Example Person")
        self.assertContains(response, PROJECT["repository_url"])
        self.assertContains(response, 'class="project-card__link"', count=1)
        self.assertContains(response, 'href="https://github.com/example"')
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertNotContains(response, "View repository")
        self.assertNotContains(response, 'class="projects-page__intro"')
        self.assertNotContains(response, 'class="projects-search__count"')
        self.assertNotContains(response, 'class="projects-page__github"')
        self.assertContains(response, 'class="projects-page__scroll-hint" hidden')

    def test_projects_are_sorted_alphabetically_ignoring_case(self):
        self.project.delete()
        for index, title in enumerate(("Zebra", "beta", "Alpha")):
            create_project({"title": title, "repository_url": f"https://github.com/example/project-{index}"})
        response = self.client.get("/projects/")
        self.assertEqual([card["title"] for card in response.context["projects"]], ["Alpha", "beta", "Zebra"])

    def test_text_is_escaped(self):
        text = self.project.translations.get(language="en")
        text.description = "<script>example</script>"
        text.save()
        response = self.client.get("/projects/")
        self.assertContains(response, "&lt;script&gt;example&lt;/script&gt;")
        self.assertNotContains(response, "<script>example</script>")

    def test_empty_content_has_no_empty_scroll_region_or_hint(self):
        self.project.delete()
        response = self.client.get("/projects/")
        self.assertContains(response, "Projects coming soon.")
        self.assertNotContains(response, 'class="projects-rail"')
        self.assertNotContains(response, 'class="projects-page__scroll-hint"')

    def test_database_changes_appear_without_restart(self):
        self.client.get("/projects/")
        self.project.title = "Updated Project"
        self.project.save()
        self.assertContains(self.client.get("/projects/"), "Updated Project")

    def test_project_title_stays_english_in_each_language(self):
        self.add_translations()
        for language in ("en", "es", "fr"):
            with self.subTest(language=language):
                response = self.client.get("/projects/", HTTP_ACCEPT_LANGUAGE=language)
                self.assertContains(response, f'<html lang="{language}"')
                self.assertContains(response, f'>{PROJECT["title"]}</a>')

    def test_search_matches_names_descriptions_categories_and_technologies(self):
        for term in ("eXaMpLe PrOjEcT", "processes", "DATA ENGINEERING", "sql"):
            with self.subTest(term=term):
                response = self.client.get("/projects/", {"q": term})
                self.assertContains(response, 'class="project-card__link"', count=1)
                self.assertContains(response, 'class="projects-search__count">1 of 1')
                self.assertContains(response, 'class="projects-search__clear"')

    def test_filtered_projects_keep_alphabetical_order(self):
        self.project.title = "Zebra"
        self.project.save()
        create_project({"title": "Alpha", "repository_url": "https://github.com/example/alpha"})
        create_project({"title": "Excluded", "repository_url": "https://github.com/example/excluded", "technologies": ["Java"]})
        response = self.client.get("/projects/", {"q": "SQL"})
        self.assertEqual([card["title"] for card in response.context["projects"]], ["Alpha", "Zebra"])
        self.assertContains(response, 'class="projects-search__count">2 of 3')

    def test_no_matches_show_a_clear_message_and_no_scroll_region(self):
        response = self.client.get("/projects/", {"q": "Kafka"})
        self.assertContains(response, "No projects match")
        self.assertContains(response, 'class="projects-search__count">0 of 1')
        self.assertNotContains(response, 'class="projects-rail"')
        self.assertNotContains(response, "Projects coming soon.")
        self.assertNotContains(response, 'class="projects-page__scroll-hint"')

    def test_blank_search_shows_all_projects(self):
        response = self.client.get("/projects/", {"q": "   "})
        self.assertContains(response, 'class="project-card__link"', count=1)
        self.assertNotContains(response, 'class="projects-search__clear"')
        self.assertNotContains(response, 'class="projects-search__count"')

    def test_search_query_is_escaped(self):
        response = self.client.get("/projects/", {"q": '<script>alert("test")</script>'})
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("test")</script>')

    def test_drafts_and_projects_without_english_text_are_hidden(self):
        create_project({"title": "Draft", "repository_url": "https://github.com/example/draft"}, published=False)
        untranslated = create_project({"title": "Incomplete", "repository_url": "https://github.com/example/incomplete"})
        untranslated.translations.all().delete()
        response = self.client.get("/projects/")
        self.assertEqual(response.context["project_total"], 1)
        self.assertNotContains(response, ">Draft</a>")
        self.assertNotContains(response, ">Incomplete</a>")

    def test_missing_translation_falls_back_to_english(self):
        response = self.client.get("/projects/", HTTP_ACCEPT_LANGUAGE="fr")
        self.assertContains(response, '<html lang="fr"')
        self.assertContains(response, 'project-card" lang="en"')
        self.assertContains(response, PROJECT["description"])

    def test_category_description_and_controls_use_selected_language(self):
        self.add_translations()
        for language, category, description, search in (
            ("es", "Ingeniería de datos", "Procesa datos de ejemplo.", "Buscar"),
            ("fr", "Ingénierie des données", "Traite des données exemples.", "Rechercher"),
        ):
            with self.subTest(language=language):
                response = self.client.get("/projects/", HTTP_ACCEPT_LANGUAGE=language)
                self.assertContains(response, category)
                self.assertContains(response, description)
                self.assertContains(response, f'>{search}</button>')
                self.assertContains(response, f'project-card" lang="{language}"')
                self.assertNotContains(response, PROJECT["description"])

    def test_search_uses_selected_language_and_ignores_case_and_accents(self):
        self.add_translations()
        for language, term in (("es", "INGENIERIA"), ("fr", "ingenierie"), ("es", "procesa"), ("fr", "donnees")):
            with self.subTest(language=language, term=term):
                response = self.client.get("/projects/", {"q": term}, HTTP_ACCEPT_LANGUAGE=language)
                self.assertEqual(response.context["project_count"], 1)
        response = self.client.get("/projects/", {"q": "procesa"}, HTTP_ACCEPT_LANGUAGE="fr")
        self.assertEqual(response.context["project_count"], 0)

    def test_translated_search_still_matches_shared_title_and_technologies(self):
        self.add_translations()
        for language in ("es", "fr"):
            for term in ("example project", "SQL"):
                with self.subTest(language=language, term=term):
                    response = self.client.get("/projects/", {"q": term}, HTTP_ACCEPT_LANGUAGE=language)
                    self.assertEqual(response.context["project_count"], 1)

    def test_translation_fetching_uses_two_queries_for_multiple_cards(self):
        create_project({"repository_url": "https://github.com/example/another"})
        with self.assertNumQueries(2):
            self.client.get("/projects/")


@override_settings(ALLOWED_HOSTS=["testserver"], SITE_PROFILE=PROFILE)
class ProjectsRouteTests(TestCase):
    def test_projects_route_renders_database_records(self):
        create_project()
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/projects.html")
        self.assertEqual(response.context["projects"][0]["title"], PROJECT["title"])


class ProjectModelTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title=PROJECT["title"],
            repository_url=PROJECT["repository_url"],
            technologies=PROJECT["technologies"].copy(),
        )

    def add_translation(self, language="en"):
        return ProjectTranslation.objects.create(
            project=self.project,
            language=language,
            category=PROJECT["category"],
            description=PROJECT["description"],
        )

    def test_projects_are_drafts_by_default(self):
        self.assertFalse(self.project.is_published)

    def test_default_technology_lists_are_independent(self):
        first = Project()
        second = Project()
        first.technologies.append("Python")
        self.assertEqual(second.technologies, [])

    def test_valid_project_passes_validation(self):
        self.project.full_clean()

    def test_invalid_repository_links_are_rejected(self):
        for url in (
            "https://example.com/example/project",
            "http://github.com/example/project",
            "https://github.com/example",
            "https://github.com/example/project/tree/main",
            "https://user:password@github.com/example/project",
        ):
            with self.subTest(url=url):
                self.project.repository_url = url
                with self.assertRaises(ValidationError):
                    self.project.full_clean()

    def test_invalid_technologies_are_rejected(self):
        for technologies in ("Python", [123], [" "], {}, None, {"name": "Python"}):
            with self.subTest(technologies=technologies):
                self.project.technologies = technologies
                with self.assertRaises(ValidationError):
                    self.project.full_clean()

    def test_one_translation_per_language_is_enforced_by_database(self):
        self.add_translation("en")
        self.add_translation("fr")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.add_translation("en")

    def test_translation_requires_supported_language(self):
        translation = self.add_translation()
        translation.language = "de"
        with self.assertRaises(ValidationError):
            translation.full_clean()

    def test_project_label_uses_shared_english_title(self):
        self.assertEqual(str(self.project), PROJECT["title"])
        translation = self.add_translation("fr")
        self.assertEqual(str(translation), f'{PROJECT["title"]} (fr)')

    def test_deleting_project_deletes_its_translations(self):
        translation = self.add_translation()
        self.project.delete()
        self.assertFalse(ProjectTranslation.objects.filter(pk=translation.pk).exists())

    def test_deleting_translation_keeps_project(self):
        self.add_translation().delete()
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
