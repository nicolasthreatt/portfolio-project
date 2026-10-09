from django.test import Client, SimpleTestCase, override_settings
from django.utils import translation


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    ROOT_URLCONF="portfolio.tests.urls",
    SITE_PROFILE={"full_name": "Example Person", "email": "person@example.com"},
)
class LanguageTests(SimpleTestCase):
    def setUp(self):
        self.addCleanup(translation.deactivate_all)

    def test_selector_languages_are_alphabetical(self):
        for code in ("en", "es", "fr"):
            with self.subTest(language=code):
                response = self.client.get("/", HTTP_ACCEPT_LANGUAGE=code)
                html = response.content.decode().split('class="site-language__panel"', 1)[1]
                self.assertLess(html.index('lang="en"'), html.index('lang="es"'))
                self.assertLess(html.index('lang="es"'), html.index('lang="fr"'))

    def test_navigation_in_each_language_and_unchanged_footer(self):
        for code, label in [
            ("en", "Projects"),
            ("fr", "Projets"),
            ("es", "Proyectos"),
        ]:
            with self.subTest(language=code):
                response = self.client.get("/projects/", HTTP_ACCEPT_LANGUAGE=code)
                self.assertContains(response, f'<html lang="{code}"')
                self.assertContains(response, f'aria-current="page">{label}</a>')
                self.assertContains(response, 'aria-label="Email Example Person"')
                self.assertContains(response, 'action="/i18n/setlang/"')
                self.assertNotContains(response, "disabled")

    def test_switch_preserves_page_and_query_and_sets_cookie(self):
        response = self.client.post(
            "/i18n/setlang/", {"language": "fr", "next": "/projects/?q=Kafka"}
        )
        self.assertRedirects(response, "/projects/?q=Kafka", fetch_redirect_response=False)
        self.assertEqual(response.cookies["django_language"].value, "fr")
        # An explicit choice takes precedence over the browser preference.
        page_response = self.client.get("/projects/", HTTP_ACCEPT_LANGUAGE="es")
        self.assertContains(page_response, '<html lang="fr"')
        self.assertContains(page_response, "Projets")

    def test_unsupported_language_does_not_set_cookie(self):
        response = self.client.post(
            "/i18n/setlang/", {"language": "invalid", "next": "/"}
        )
        self.assertNotIn("django_language", response.cookies)

    def test_switch_rejects_external_redirect(self):
        response = self.client.post(
            "/i18n/setlang/", {"language": "es", "next": "https://example.com/"}
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_switch_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        page_response = client.get("/")
        self.assertEqual(
            client.post("/i18n/setlang/", {"language": "fr"}).status_code, 403
        )
        response = client.post(
            "/i18n/setlang/",
            {
                "language": "fr",
                "next": "/",
                "csrfmiddlewaretoken": page_response.cookies["csrftoken"].value,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.cookies["django_language"].value, "fr")
