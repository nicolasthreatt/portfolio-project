"""Checks for viewing and downloading the resume from Experience."""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse


class ResumeFile:
    def setUp(self):
        super().setUp()
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.resume = Path(folder.name) / "example.pdf"
        self.document = b"%PDF-1.4\nExample resume\n%%EOF\n"
        self.resume.write_bytes(self.document)
        settings = override_settings(RESUME_FILE=self.resume, ALLOWED_HOSTS=["testserver"])
        settings.enable()
        self.addCleanup(settings.disable)


@override_settings(SITE_PROFILE={"full_name": "Example Person"})
class ResumeTests(ResumeFile, SimpleTestCase):
    def test_view_and_download_use_same_document_with_different_headers(self):
        for route, disposition in (("resume-view", "inline"), ("resume-download", "attachment")):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "application/pdf")
                self.assertEqual(response["Content-Disposition"], f'{disposition}; filename="Example Person Resume.pdf"')
                self.assertEqual(b"".join(response.streaming_content), self.document)
                response.close()

    def test_missing_pdf_returns_404(self):
        self.resume.unlink()
        for route in ("resume-view", "resume-download"):
            self.assertEqual(self.client.get(reverse(route)).status_code, 404)

    @override_settings(SITE_PROFILE={"full_name": "  "})
    def test_empty_name_uses_generic_filename(self):
        response = self.client.get(reverse("resume-download"))
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="Resume.pdf"')
        response.close()

    @override_settings(SITE_PROFILE={"full_name": "Élodie Martin"})
    def test_unicode_name_is_encoded_in_download_header(self):
        response = self.client.get(reverse("resume-download"))
        self.assertEqual(response["Content-Disposition"], "attachment; filename*=utf-8''%C3%89lodie%20Martin%20Resume.pdf")
        response.close()

    def test_post_is_not_allowed(self):
        for route in ("resume-view", "resume-download"):
            self.assertEqual(self.client.post(reverse(route)).status_code, 405)

    def test_head_returns_headers_without_document_body(self):
        response = self.client.head(reverse("resume-view"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(b"".join(response.streaming_content), b"")
        response.close()

    def test_query_cannot_select_another_file(self):
        response = self.client.get(reverse("resume-view"), {"file": "../../.env"})
        self.assertEqual(b"".join(response.streaming_content), self.document)
        response.close()

    def test_old_resume_page_is_removed(self):
        self.assertEqual(self.client.get("/resume/").status_code, 404)


@override_settings(SITE_PROFILE={"full_name": "Example Person"})
class ResumeLinksTests(ResumeFile, TestCase):
    def test_experience_shows_resume_actions_but_no_resume_tab(self):
        response = self.client.get(reverse("experience-list"))
        self.assertContains(response, f'href="{reverse("resume-view")}"')
        self.assertContains(response, f'href="{reverse("resume-download")}"')
        self.assertNotContains(response, 'href="/resume/"')

    def test_actions_hidden_when_pdf_is_missing(self):
        self.resume.unlink()
        response = self.client.get(reverse("experience-list"))
        self.assertNotContains(response, f'href="{reverse("resume-view")}"')
        self.assertNotContains(response, f'href="{reverse("resume-download")}"')

    def test_action_labels_follow_language_choice(self):
        for language, label in (("es", "Ver currículum"), ("fr", "Voir le CV")):
            with self.subTest(language=language):
                response = self.client.get(reverse("experience-list"), HTTP_ACCEPT_LANGUAGE=language)
                self.assertContains(response, label)
