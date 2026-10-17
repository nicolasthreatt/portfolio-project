from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from ..admin import ExperienceTranslationInline
from ..models import Experience, ExperienceTranslation
from ..templatetags.experience_links import highlight_links


class HighlightLinkTests(SimpleTestCase):
    def test_render_links(self):
        result = highlight_links('<script> [<b>Metrics</b>](https://example.com/metrics) and [Video](https://example.com/video)')
        self.assertIn("&lt;script&gt;", result)
        self.assertIn("&lt;b&gt;Metrics&lt;/b&gt;", result)
        self.assertIn('href="https://example.com/metrics"', result)
        self.assertIn('href="https://example.com/video"', result)
        self.assertIn('rel="noopener noreferrer"', result)
        self.assertNotIn("<script>", result)


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SITE_PROFILE={"full_name": "Example Person", "github_url": "https://github.com/example"},
)
class ExperienceTests(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            company="Example Company", slug="example-company", company_url="https://example.com/",
            technologies=["Python", "Django"], is_published=True,
        )
        self.english = ExperienceTranslation.objects.create(
            experience=self.experience, language="en", role="Software Engineer",
            location="Example City", overview="Built a useful product.",
            accomplishments="Designed the system.\n\n Tested it. \n",
        )

    def test_accomplishment_list_ignores_blank_lines(self):
        self.assertEqual(self.english.accomplishment_list, ["Designed the system.", "Tested it."])

    def test_highlights_render_inline_links(self):
        self.english.accomplishments = "Built [analytics](https://example.com/analytics) & reports."
        self.english.save()
        response = self.client.get(reverse("experience-detail", args=[self.experience.slug]))
        self.assertContains(response, '<a href="https://example.com/analytics" target="_blank" rel="noopener noreferrer">analytics</a>', html=True)
        self.assertNotContains(response, "[analytics](")

    def test_detail_renders_text_technologies_and_company_link(self):
        response = self.client.get(reverse("experience-detail", args=[self.experience.slug]))
        self.assertEqual(response.status_code, 200)
        for text in ("Example Company", "Software Engineer", "Designed the system.", "Python, Django"):
            self.assertContains(response, text)
        self.assertContains(response, 'href="https://example.com/"')
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertContains(response, "site-footer__social-link")
        self.assertContains(response, "Example Person")

    def test_list_respects_display_order(self):
        first = Experience.objects.create(company="Other Company", slug="other-company", display_order=0, is_published=True)
        ExperienceTranslation.objects.create(experience=first, language="en")
        self.experience.display_order = 1
        self.experience.save()
        response = self.client.get(reverse("experience-list"))
        self.assertEqual([item["id"] for item in response.context["experiences"]], [first.pk, self.experience.pk])

    def test_drafts_and_missing_english_are_hidden(self):
        draft = Experience.objects.create(company="Draft", slug="draft")
        ExperienceTranslation.objects.create(experience=draft, language="en")
        missing = Experience.objects.create(company="Missing English", slug="missing-english", is_published=True)
        ExperienceTranslation.objects.create(experience=missing, language="fr", role="Ingénieur")
        response = self.client.get(reverse("experience-list"))
        self.assertNotContains(response, "Draft")
        self.assertNotContains(response, "Missing English")
        for record in (draft, missing):
            self.assertEqual(self.client.get(reverse("experience-detail", args=[record.slug])).status_code, 404)

    def test_missing_record_is_404(self):
        self.assertEqual(self.client.get(reverse("experience-detail", args=["missing"])).status_code, 404)

    def test_list_links_use_slugs_in_every_language(self):
        for language in ("en", "es", "fr"):
            with self.subTest(language=language):
                response = self.client.get(reverse("experience-list"), HTTP_ACCEPT_LANGUAGE=language)
                self.assertContains(response, 'href="/experience/example-company/"')

    def test_active_translation_on_list_and_detail(self):
        for language, role in (("es", "Ingeniero de software"), ("fr", "Ingénieur logiciel")):
            ExperienceTranslation.objects.create(experience=self.experience, language=language, role=role)
            for url in (reverse("experience-list"), reverse("experience-detail", args=[self.experience.slug])):
                with self.subTest(language=language, url=url):
                    response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=language)
                    self.assertContains(response, role)
                    self.assertContains(response, f'lang="{language}"')
                    self.assertContains(response, "Example Company")
                    self.assertNotContains(response, "Software Engineer")

    def test_missing_translation_falls_back_to_english(self):
        response = self.client.get(reverse("experience-detail", args=[self.experience.slug]), HTTP_ACCEPT_LANGUAGE="fr")
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, '<article class="experience-detail" lang="en">')

    def test_content_is_escaped(self):
        self.english.overview = '<script>alert("test")</script>'
        self.english.save()
        response = self.client.get(reverse("experience-detail", args=[self.experience.slug]))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert")

    def test_list_uses_two_queries(self):
        with self.assertNumQueries(2):
            self.client.get(reverse("experience-list"))

    def test_list_keeps_only_an_accessible_page_heading(self):
        response = self.client.get(reverse("experience-list"))
        self.assertContains(response, '<h1 class="visually-hidden">Experience</h1>', html=True)
        self.assertNotContains(response, "experience-list__header")

    def test_admin_uses_translation_inline_without_legacy_fields(self):
        model_admin = admin.site._registry[Experience]
        self.assertIn(ExperienceTranslationInline, model_admin.inlines)
        fields = [field for _, options in model_admin.fieldsets for field in options["fields"]]
        self.assertIn("company_url", fields)
        self.assertNotIn("legacy_summary", fields)
        self.assertNotIn("role", fields)


class ExperienceModelTests(TestCase):
    def test_slugs_are_unique(self):
        Experience.objects.create(company="First", slug="example")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Experience.objects.create(company="Second", slug="example")

    def test_defaults_and_independent_technology_lists(self):
        first = Experience(company="First")
        second = Experience(company="Second")
        first.technologies.append("Python")
        self.assertEqual(second.technologies, [])
        self.assertFalse(first.is_published)
        self.assertEqual(str(first), "First")

    def test_invalid_technology_shapes_are_rejected(self):
        for value in ({}, None, "Python", [""], [42]):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Experience(company="Example", slug="example", technologies=value).full_clean()
        Experience(company="Example", slug="example", technologies=[]).full_clean()

    def test_unique_translation_language(self):
        record = Experience.objects.create(company="Example", slug="example")
        ExperienceTranslation.objects.create(experience=record, language="en")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ExperienceTranslation.objects.create(experience=record, language="en")

    def test_supported_language_validation(self):
        record = Experience.objects.create(company="Example", slug="example")
        with self.assertRaises(ValidationError):
            ExperienceTranslation(experience=record, language="de").full_clean()

    def test_delete_cascades_to_translations(self):
        record = Experience.objects.create(company="Example", slug="example")
        ExperienceTranslation.objects.create(experience=record, language="en")
        record.delete()
        self.assertFalse(ExperienceTranslation.objects.exists())
