from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class SpotsViewsAndTemplatesTests(TestCase):
    def test_home_page_renders_template_and_static_css(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/index.html")
        self.assertContains(response, "spots/css/style.css")
        self.assertContains(response, "Последние добавленные места")

    def test_about_page_uses_template_and_inclusion_tag(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/about.html")
        self.assertContains(response, "Учебный Django-проект")
        self.assertContains(response, "Последние добавленные места")

    def test_spot_detail_existing_and_missing(self):
        ok = self.client.get(reverse("spot_detail", args=(1,)))
        self.assertEqual(ok.status_code, 200)
        self.assertTemplateUsed(ok, "spots/spot_detail.html")

        missing = self.client.get(reverse("spot_detail", args=(999,)))
        self.assertEqual(missing.status_code, 404)
        self.assertTemplateUsed(missing, "spots/404.html")

    def test_area_page_with_filter(self):
        response = self.client.get(reverse("area", args=("center",)), {"noise": "high"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/area.html")
        self.assertContains(response, "Активный фильтр шума")

    def test_archive_redirect_and_archive_404(self):
        redirect_response = self.client.get(reverse("archive", args=(2099,)))
        self.assertEqual(redirect_response.status_code, 302)
        self.assertEqual(redirect_response.url, reverse("home"))

        response_404 = self.client.get(reverse("archive404", args=(2099,)))
        self.assertEqual(response_404.status_code, 404)
        self.assertTemplateUsed(response_404, "spots/404.html")

    def test_custom_tags_filter_and_simple_tag(self):
        tpl = Template(
            "{% load spots_tags %}"
            "{{ 'high'|noise_class }}|{% noise_badge 'medium' %}"
        )
        rendered = tpl.render(Context())
        self.assertEqual(rendered, "noise-high|средний")
