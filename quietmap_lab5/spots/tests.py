from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Spot


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class SpotsViewsAndTemplatesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.spot_1 = Spot.objects.create(
            title="Читальный зал у воды",
            slug="test-chitalny-zal-u-vody",
            content="Тихая зона с видом на реку и стабильным Wi-Fi.",
            area="Набережная",
            area_slug="naberezhnaya",
            noise_level=Spot.NoiseLevel.LOW,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        cls.spot_2 = Spot.objects.create(
            title="Сквер сосновый",
            slug="test-skver-sosnovyy",
            content="Мало людей утром, есть скамейки и тень от деревьев.",
            area="Заельцовский",
            area_slug="zaeltsovskiy",
            noise_level=Spot.NoiseLevel.MEDIUM,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        cls.spot_draft = Spot.objects.create(
            title="Черновик локации",
            slug="chernovik-lokatsii",
            content="Эта запись не должна отображаться на страницах.",
            area="Центр",
            area_slug="center",
            noise_level=Spot.NoiseLevel.HIGH,
            status=Spot.PublicationStatus.DRAFT,
        )

    def test_published_manager_and_enum(self):
        self.assertEqual(Spot.PublicationStatus.PUBLISHED, 1)
        self.assertEqual(Spot.NoiseLevel.LOW.label, "Низкий")
        published_slugs = list(Spot.published.values_list("slug", flat=True))
        self.assertIn(self.spot_1.slug, published_slugs)
        self.assertNotIn(self.spot_draft.slug, published_slugs)

    def test_home_page_renders_template_and_static_css(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/index.html")
        self.assertContains(response, "spots/css/style.css")
        self.assertContains(response, "Последние добавленные места")
        self.assertContains(response, self.spot_1.title)
        self.assertNotContains(response, self.spot_draft.title)

    def test_about_page_uses_template_and_inclusion_tag(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/about.html")
        self.assertContains(response, "Учебный Django-проект")
        self.assertContains(response, "Последние добавленные места")

    def test_spot_detail_existing_and_missing(self):
        ok = self.client.get(reverse("spot_detail", args=(self.spot_1.slug,)))
        self.assertEqual(ok.status_code, 200)
        self.assertTemplateUsed(ok, "spots/spot_detail.html")

        missing = self.client.get(reverse("spot_detail", args=("missing-slug",)))
        self.assertEqual(missing.status_code, 404)
        self.assertTemplateUsed(missing, "spots/404.html")

    def test_area_page_with_filter(self):
        response = self.client.get(reverse("area", args=("zaeltsovskiy",)), {"noise": "medium"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/area.html")
        self.assertContains(response, "Активный фильтр шума")
        self.assertContains(response, self.spot_2.title)

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
            "{{ level|noise_class }}|{% noise_badge level %}"
        )
        rendered = tpl.render(Context({"level": Spot.NoiseLevel.HIGH}))
        self.assertEqual(rendered, "noise-high|высокий")
