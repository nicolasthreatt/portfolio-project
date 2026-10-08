"""Checks for public profile configuration in shared templates."""

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings


PROFILE = {
    "full_name": "Example Person",
    "profession": "Example Profession",
    "email": "person@example.com",
    "github_url": "https://github.com/example",
    "linkedin_url": "https://www.linkedin.com/in/example/",
}


@override_settings(SITE_PROFILE=PROFILE)
class SharedProfileTests(SimpleTestCase):
    def render_base(self):
        return render_to_string("base.html", request=RequestFactory().get("/"))

    def test_configured_profile_is_rendered(self):
        html = self.render_base()
        self.assertIn("<title>Example Person</title>", html)
        self.assertIn("Portfolio of Example Person, Example Profession.", html)
        self.assertIn('href="mailto:person@example.com"', html)
        self.assertIn('href="https://github.com/example"', html)
        self.assertIn('href="https://www.linkedin.com/in/example/"', html)
        self.assertIn('aria-label="Email Example Person"', html)
        self.assertIn('class="site-header__brand" href="/">Example Person</a>', html)
        self.assertIn('class="site-footer__copyright"', html)

    @override_settings(
        SITE_PROFILE={**PROFILE, "email": "", "github_url": "", "linkedin_url": ""}
    )
    def test_missing_contact_values_do_not_create_empty_links(self):
        html = self.render_base()
        self.assertNotIn('class="site-footer__social-links"', html)
        self.assertNotIn('href="mailto:"', html)

    def test_footer_icons_do_not_require_an_icon_font(self):
        html = self.render_base()
        self.assertEqual(html.count('class="site-footer__icon"'), 3)
        self.assertEqual(html.count('focusable="false"'), 3)
        self.assertNotIn("fontawesome/css/", html)

    @override_settings(
        SITE_PROFILE={**PROFILE, "full_name": 'Example "Person" <Test>'}
    )
    def test_profile_content_is_html_escaped(self):
        html = self.render_base()
        self.assertIn("Example &quot;Person&quot; &lt;Test&gt;", html)
        self.assertNotIn('Example "Person" <Test>', html)
