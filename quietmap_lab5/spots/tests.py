from datetime import timedelta

from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Category, Spot, SpotDetail, Tag


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class SpotsViewsAndTemplatesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat_focus = Category.objects.create(name="Для учебы", slug="for-study")
        cls.cat_outdoor = Category.objects.create(name="На улице", slug="outdoor")

        cls.tag_quiet, _ = Tag.objects.get_or_create(
            slug="noise-low",
            defaults={"name": "Низкий шум"},
        )
        cls.tag_reading, _ = Tag.objects.get_or_create(
            slug="reading",
            defaults={"name": "Чтение"},
        )
        cls.tag_park, _ = Tag.objects.get_or_create(
            slug="park",
            defaults={"name": "Парк"},
        )

        cls.spot_1 = Spot.objects.create(
            title="Читальный зал у воды",
            slug="test-chitalny-zal-u-vody",
            content="Тихая зона с видом на реку и стабильным Wi-Fi.",
            area="Набережная",
            area_slug="naberezhnaya",
            category=cls.cat_focus,
            noise_level=Spot.NoiseLevel.LOW,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        cls.spot_1.tags.add(cls.tag_quiet, cls.tag_reading)
        SpotDetail.objects.create(
            spot=cls.spot_1,
            seats=20,
            has_wifi=True,
            avg_stay_minutes=110,
            work_hours="08:00-22:00",
        )

        cls.spot_2 = Spot.objects.create(
            title="Сквер сосновый",
            slug="test-skver-sosnovyy",
            content="Мало людей утром, есть скамейки и тень от деревьев.",
            area="Заельцовский",
            area_slug="zaeltsovskiy",
            category=cls.cat_outdoor,
            noise_level=Spot.NoiseLevel.MEDIUM,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        cls.spot_2.tags.add(cls.tag_park)
        SpotDetail.objects.create(
            spot=cls.spot_2,
            seats=10,
            has_wifi=False,
            avg_stay_minutes=70,
            work_hours="07:00-23:00",
        )

        cls.spot_draft = Spot.objects.create(
            title="Черновик локации",
            slug="chernovik-lokatsii",
            content="Эта запись не должна отображаться на страницах.",
            area="Центр",
            area_slug="center",
            category=cls.cat_focus,
            noise_level=Spot.NoiseLevel.HIGH,
            status=Spot.PublicationStatus.DRAFT,
        )
        SpotDetail.objects.create(
            spot=cls.spot_draft,
            seats=5,
            has_wifi=True,
            avg_stay_minutes=35,
            work_hours="10:00-20:00",
        )

    def test_published_manager_enum_and_relations(self):
        self.assertEqual(Spot.PublicationStatus.PUBLISHED, 1)
        self.assertEqual(Spot.NoiseLevel.LOW.label, "Низкий")
        published_slugs = list(Spot.published.values_list("slug", flat=True))
        self.assertIn(self.spot_1.slug, published_slugs)
        self.assertNotIn(self.spot_draft.slug, published_slugs)
        self.assertEqual(self.spot_1.category.slug, "for-study")
        self.assertTrue(self.spot_1.tags.exists())
        self.assertEqual(self.spot_1.detail.seats, 20)

    def test_home_page_renders_template_and_data_from_db(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/index.html")
        self.assertContains(response, "spots/css/style.css")
        self.assertContains(response, "Последние добавленные места")
        self.assertContains(response, self.spot_1.title)
        self.assertContains(response, self.tag_reading.name)
        self.assertNotContains(response, self.spot_draft.title)

    def test_about_page_mentions_relations(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/about.html")
        self.assertContains(response, "ForeignKey")
        self.assertContains(response, "ManyToManyField")
        self.assertContains(response, "OneToOneField")

    def test_spot_detail_existing_and_missing(self):
        ok = self.client.get(reverse("spot_detail", args=(self.spot_1.slug,)))
        self.assertEqual(ok.status_code, 200)
        self.assertTemplateUsed(ok, "spots/spot_detail.html")
        self.assertContains(ok, self.spot_1.category.name)
        self.assertContains(ok, self.tag_reading.name)
        self.assertContains(ok, "Средняя длительность посещения")

        missing = self.client.get(reverse("spot_detail", args=("missing-slug",)))
        self.assertEqual(missing.status_code, 404)
        self.assertTemplateUsed(missing, "spots/404.html")

    def test_area_page_with_filter_controls(self):
        response = self.client.get(reverse("area", args=("zaeltsovskiy",)), {"noise": "medium"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spots/area.html")
        self.assertContains(response, "Активный фильтр шума")
        self.assertContains(response, self.spot_2.title.title())
        self.assertContains(response, 'name="sort"')
        self.assertContains(response, 'name="tag"')

    def test_area_page_sorting_and_filtering_via_web(self):
        test_category = Category.objects.create(name="Тест", slug="test-cat")
        test_tag, _ = Tag.objects.get_or_create(
            slug="noise-high",
            defaults={"name": "Высокий шум"},
        )

        older = Spot.objects.create(
            title="Тестовая старая точка",
            slug="test-old-spot",
            content="Старая запись для проверки сортировки.",
            area="Тестовый район",
            area_slug="test-zone",
            category=test_category,
            noise_level=Spot.NoiseLevel.MEDIUM,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        newer = Spot.objects.create(
            title="Тестовая новая точка",
            slug="test-new-spot",
            content="Новая запись для проверки сортировки.",
            area="Тестовый район",
            area_slug="test-zone",
            category=test_category,
            noise_level=Spot.NoiseLevel.HIGH,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        newer.tags.add(test_tag)

        SpotDetail.objects.create(spot=older)
        SpotDetail.objects.create(spot=newer)

        now = timezone.now()
        Spot.objects.filter(pk=older.pk).update(time_create=now - timedelta(days=2))
        Spot.objects.filter(pk=newer.pk).update(time_create=now - timedelta(days=1))

        old_sorted = self.client.get(reverse("area", args=("test-zone",)), {"sort": "old"})
        self.assertEqual(old_sorted.status_code, 200)
        old_slugs = list(old_sorted.context["spots"].values_list("slug", flat=True))
        self.assertEqual(old_slugs, ["test-old-spot", "test-new-spot"])

        new_sorted = self.client.get(reverse("area", args=("test-zone",)), {"sort": "new"})
        self.assertEqual(new_sorted.status_code, 200)
        new_slugs = list(new_sorted.context["spots"].values_list("slug", flat=True))
        self.assertEqual(new_slugs, ["test-new-spot", "test-old-spot"])

        only_high = self.client.get(
            reverse("area", args=("test-zone",)),
            {"noise": "high", "sort": "new"},
        )
        self.assertEqual(only_high.status_code, 200)
        high_slugs = list(only_high.context["spots"].values_list("slug", flat=True))
        self.assertEqual(high_slugs, ["test-new-spot"])

        high_by_tag = self.client.get(
            reverse("area", args=("test-zone",)),
            {"tag": "noise-high", "sort": "new"},
        )
        self.assertEqual(high_by_tag.status_code, 200)
        tag_slugs = list(high_by_tag.context["spots"].values_list("slug", flat=True))
        self.assertEqual(tag_slugs, ["test-new-spot"])

    def test_tag_and_category_pages(self):
        tag_response = self.client.get(reverse("tag", args=(self.tag_reading.slug,)))
        self.assertEqual(tag_response.status_code, 200)
        self.assertTemplateUsed(tag_response, "spots/tag.html")
        self.assertContains(tag_response, self.spot_1.title.title())

        tags_index = self.client.get(reverse("tags_index"))
        self.assertEqual(tags_index.status_code, 200)
        self.assertTemplateUsed(tags_index, "spots/tags_index.html")
        self.assertContains(tags_index, self.tag_reading.name)

        category_response = self.client.get(reverse("category", args=(self.cat_focus.slug,)))
        self.assertEqual(category_response.status_code, 200)
        self.assertTemplateUsed(category_response, "spots/category.html")
        self.assertContains(category_response, self.spot_1.title.title())

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
