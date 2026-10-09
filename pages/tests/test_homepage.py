import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from django.urls import include, path

from ..content import load_home_content
from ..views import homepage


urlpatterns = [
    path("", homepage, name="home"),
    path("", include("portfolio.tests.urls")),
]


PROFILE = {
    "full_name": "Example Person",
    "profession": "Example Profession",
    "email": "person@example.com",
    "github_url": "https://github.com/example",
    "linkedin_url": "https://www.linkedin.com/in/example/",
}

CONTENT = {
    "heading": "Example Profession",
    "location": "Example City",
    "description": "An example portfolio.",
    "headshot_path": "images/example.jpg",
    "paragraphs": ["An introduction.", "Some background."],
}


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    SITE_PROFILE=PROFILE,
    ROOT_URLCONF=__name__,
)
class HomepageTests(SimpleTestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "home.json"
        self.write_content(CONTENT)
        override = override_settings(HOME_CONTENT_FILE=self.path)
        override.enable()
        self.addCleanup(override.disable)

    def write_content(self, content):
        self.path.write_text(json.dumps(content), encoding="utf-8")

    def test_homepage_renders_configured_content(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example Person | Example Profession")
        self.assertContains(response, "Example City")
        self.assertContains(response, "An example portfolio.")
        self.assertContains(response, 'src="/media/images/example.jpg"')
        self.assertContains(response, 'alt="Example Person"')
        self.assertContains(response, "An introduction.")
        self.assertContains(response, "Some background.")
        self.assertNotContains(response, 'id="projects"')

    def test_homepage_escapes_configured_text(self):
        self.write_content({**CONTENT, "paragraphs": ['<script>alert("example")</script>']})
        response = self.client.get("/")

        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert")

    def test_empty_optional_photo_and_location_are_hidden(self):
        self.write_content({**CONTENT, "headshot_path": "", "location": ""})
        response = self.client.get("/")

        self.assertNotContains(response, 'class="home-intro__photo"')
        self.assertNotContains(response, 'class="home-intro__location"')

    def test_content_changes_are_read_without_a_server_restart(self):
        self.client.get("/")
        self.write_content({**CONTENT, "paragraphs": ["An updated introduction."]})
        self.assertContains(self.client.get("/"), "An updated introduction.")

    def test_language_switch_translates_homepage_and_keeps_shared_photo(self):
        translations = {
            "fr": {
                "heading": "Profession exemple",
                "location": "Ville exemple",
                "description": "Un portfolio exemple.",
                "paragraphs": ["Une introduction.", "Mon parcours."],
            },
            "es": {
                "heading": "Profesión de ejemplo",
                "location": "Ciudad de ejemplo",
                "description": "Un portafolio de ejemplo.",
                "paragraphs": ["Una introducción.", "Mi trayectoria."],
            },
        }
        self.write_content({**CONTENT, "translations": translations})
        for code, translated in translations.items():
            with self.subTest(language=code):
                self.client.post("/i18n/setlang/", {"language": code, "next": "/"})
                response = self.client.get("/")
                self.assertContains(response, f'<div id="intro" lang="{code}">')
                self.assertContains(response, f"Example Person | {translated['heading']}")
                self.assertContains(response, translated["location"])
                self.assertContains(response, translated["description"])
                for paragraph in translated["paragraphs"]:
                    self.assertContains(response, paragraph)
                self.assertContains(response, 'src="/media/images/example.jpg"')
                self.assertNotContains(response, "An introduction.")
        self.client.post("/i18n/setlang/", {"language": "en", "next": "/"})
        self.assertContains(self.client.get("/"), "An introduction.")

    def test_missing_translation_falls_back_to_english(self):
        response = self.client.get("/", HTTP_ACCEPT_LANGUAGE="fr")
        self.assertContains(response, '<html lang="fr"')
        self.assertContains(response, '<div id="intro" lang="en">')
        self.assertContains(response, "An introduction.")

    def test_translated_content_is_escaped(self):
        translated = {**CONTENT, "paragraphs": ["<script>example</script>"]}
        self.write_content({**CONTENT, "translations": {"es": translated}})
        response = self.client.get("/", HTTP_ACCEPT_LANGUAGE="es")
        self.assertContains(response, "&lt;script&gt;example&lt;/script&gt;")
        self.assertNotContains(response, "<script>example</script>")

    def test_invalid_translations_are_rejected(self):
        for translations in ([], {"invalid": CONTENT}, {"fr": {}}, {"es": {**CONTENT, "paragraphs": [123]}}):
            with self.subTest(translations=translations):
                self.write_content({**CONTENT, "translations": translations})
                with self.assertRaises(ImproperlyConfigured):
                    load_home_content()

    def test_missing_file_has_a_clear_configuration_error(self):
        with override_settings(HOME_CONTENT_FILE=self.path.parent / "missing.json"):
            with self.assertRaisesMessage(ImproperlyConfigured, "Cannot read homepage content"):
                load_home_content()

    def test_malformed_json_has_a_clear_configuration_error(self):
        self.path.write_text("{invalid", encoding="utf-8")
        with self.assertRaisesMessage(ImproperlyConfigured, "Cannot read homepage content"):
            load_home_content()

    def test_invalid_content_fields_are_rejected(self):
        for content in (
            [],
            {**CONTENT, "heading": None},
            {**CONTENT, "paragraphs": "Not a list"},
            {**CONTENT, "paragraphs": [123]},
            {**CONTENT, "headshot_path": "../outside.jpg"},
            {**CONTENT, "headshot_path": "/absolute.jpg"},
        ):
            with self.subTest(content=content):
                self.write_content(content)
                with self.assertRaises(ImproperlyConfigured):
                    load_home_content()

    def test_generic_example_can_render_without_personal_content(self):
        example = Path(__file__).resolve().parents[2] / "examples" / "home.json"
        with override_settings(HOME_CONTENT_FILE=example):
            response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Profession")
        self.assertNotContains(response, 'class="home-intro__photo"')
