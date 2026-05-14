from datetime import timedelta
from io import StringIO
from pathlib import Path
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .forms import SpotModelForm, SpotPlainForm
from .models import Category, Spot, SpotDetail, Tag


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"], DEBUG=False)
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


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class SpotsAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )
        cls.category = Category.objects.create(name="Центр", slug="center-admin")
        cls.tag = Tag.objects.create(name="Коворкинг", slug="coworking-admin")
        cls.spot = Spot.objects.create(
            title="Админ тест",
            slug="admin-test",
            content="Запись для проверки админ-панели.",
            area="Центр",
            area_slug="center",
            category=cls.category,
            noise_level=Spot.NoiseLevel.MEDIUM,
            status=Spot.PublicationStatus.DRAFT,
        )
        cls.spot.tags.add(cls.tag)
        SpotDetail.objects.create(spot=cls.spot, seats=8, has_wifi=True)

    def setUp(self):
        self.client.force_login(self.user)

    def test_spot_admin_changelist_has_custom_columns_and_filters(self):
        response = self.client.get(reverse("admin:spots_spot_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Краткое описание")
        self.assertContains(response, "Теги")
        self.assertContains(response, "Детали места")
        self.assertContains(response, "Комфорт по шуму")
        self.assertContains(response, "Опубликовать выбранные места")

    def test_spot_admin_custom_action_publishes_and_shows_message(self):
        response = self.client.post(
            reverse("admin:spots_spot_changelist"),
            {
                "action": "set_published",
                "_selected_action": [str(self.spot.pk)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.spot.refresh_from_db()
        self.assertEqual(self.spot.status, Spot.PublicationStatus.PUBLISHED)
        self.assertContains(response, "Опубликовано записей: 1.")


class DemoLab8QueriesCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category, _ = Category.objects.get_or_create(
            slug="study",
            defaults={"name": "Для учебы"},
        )
        cls.tag_quiet, _ = Tag.objects.get_or_create(
            slug="noise-low",
            defaults={"name": "Низкий шум"},
        )
        cls.tag_coworking, _ = Tag.objects.get_or_create(
            slug="coworking",
            defaults={"name": "Коворкинг"},
        )

        cls.spot_1 = Spot.objects.create(
            title="Читальный зал у воды",
            slug="lab8-spot-1",
            content="Тихое место для чтения и работы.",
            area="Набережная",
            area_slug="naberezhnaya",
            category=cls.category,
            noise_level=Spot.NoiseLevel.LOW,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        cls.spot_1.tags.add(cls.tag_quiet)
        SpotDetail.objects.create(
            spot=cls.spot_1,
            seats=16,
            has_wifi=True,
            avg_stay_minutes=100,
            work_hours="08:00-22:00",
        )

        cls.spot_2 = Spot.objects.create(
            title="Коворкинг на Красном",
            slug="lab8-spot-2",
            content="Подходит для коротких задач и встреч.",
            area="Центр",
            area_slug="center",
            category=cls.category,
            noise_level=Spot.NoiseLevel.HIGH,
            status=Spot.PublicationStatus.PUBLISHED,
        )
        cls.spot_2.tags.add(cls.tag_coworking)
        SpotDetail.objects.create(
            spot=cls.spot_2,
            seats=8,
            has_wifi=True,
            avg_stay_minutes=55,
            work_hours="09:00-21:00",
        )

        now = timezone.now()
        Spot.objects.filter(pk=cls.spot_1.pk).update(time_update=now - timedelta(days=2))
        Spot.objects.filter(pk=cls.spot_2.pk).update(time_update=now - timedelta(days=1))

    def test_demo_lab8_queries_outputs_selection_methods_and_orm_blocks(self):
        out = StringIO()
        call_command("demo_lab8_queries", stdout=out)
        output = out.getvalue()

        self.assertIn("== SELECTION METHODS ==", output)
        self.assertIn("get(slug='", output)
        self.assertIn("order_by('pk').first()", output)
        self.assertIn("order_by('pk').last()", output)
        self.assertIn("earliest('time_update')", output)
        self.assertIn("latest('time_update')", output)
        self.assertIn("== Q FILTER ==", output)
        self.assertIn("== F FILTER ==", output)
        self.assertIn("== VALUE + ANNOTATE ==", output)
        self.assertIn("== CALCULATED FIELDS + DB FUNCTION ==", output)
        self.assertIn("== AGGREGATE ==", output)
        self.assertIn("== GROUP BY CATEGORY ==", output)
        self.assertIn("== VALUES FROM RELATED TABLES ==", output)
        self.assertIn("== EXISTS / COUNT ==", output)


class SpotsFormsAndUploadsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Для работы", slug="work-form")
        cls.tag_focus = Tag.objects.create(name="Фокус", slug="focus-form")
        cls.tag_wifi = Tag.objects.create(name="Wi-Fi", slug="wifi-form")

    def make_image_file(self, name="spot.png", size=(60, 40), color=(32, 120, 96)):
        # PIL requires binary stream, so create a BytesIO locally.
        from io import BytesIO

        data = BytesIO()
        image = Image.new("RGB", size, color)
        image.save(data, format="PNG")
        return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")

    def plain_form_payload(self, **overrides):
        payload = {
            "title": "Новая тихая локация",
            "slug": "novaya-tihaya-lokaciya",
            "content": "Подробное описание тихого места для лабораторной работы 10.",
            "area": "Академгородок",
            "area_slug": "akademgorodok",
            "category": str(self.category.pk),
            "noise_level": str(Spot.NoiseLevel.LOW),
            "status": str(Spot.PublicationStatus.PUBLISHED),
            "tags": [str(self.tag_focus.pk), str(self.tag_wifi.pk)],
            "seats": "18",
            "has_wifi": "on",
            "avg_stay_minutes": "110",
            "work_hours": "09:00-21:00",
        }
        payload.update(overrides)
        return payload

    def model_form_payload(self, **overrides):
        payload = {
            "title": "Форма модели тихого места",
            "slug": "forma-modeli-tihogo-mesta",
            "content": "Детальное описание места, созданного через ModelForm в лабораторной работе 10.",
            "area": "Левый берег",
            "area_slug": "leviy-bereg",
            "category": str(self.category.pk),
            "noise_level": str(Spot.NoiseLevel.MEDIUM),
            "status": str(Spot.PublicationStatus.PUBLISHED),
            "tags": [str(self.tag_focus.pk)],
            "seats": "14",
            "has_wifi": "on",
            "avg_stay_minutes": "85",
            "work_hours": "08:30-20:00",
        }
        payload.update(overrides)
        return payload

    def test_plain_form_custom_validator_rejects_placeholder_title(self):
        form = SpotPlainForm(data=self.plain_form_payload(title="Тестовое место"))
        self.assertFalse(form.is_valid())
        self.assertIn("служебные слова", form.errors["title"][0])

    def test_plain_form_valid_post_creates_spot_and_detail(self):
        response = self.client.post(reverse("plain_spot_add"), data=self.plain_form_payload())
        self.assertEqual(response.status_code, 302)
        spot = Spot.objects.get(slug="novaya-tihaya-lokaciya")
        self.assertEqual(spot.category, self.category)
        self.assertEqual(spot.tags.count(), 2)
        self.assertTrue(SpotDetail.objects.filter(spot=spot, seats=18, has_wifi=True).exists())

    def test_upload_file_view_saves_same_original_name_as_different_random_files(self):
        with tempfile.TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/"):
                response_1 = self.client.post(
                    reverse("upload_file"),
                    data={
                        "description": "Первый файл",
                        "file": SimpleUploadedFile("notes.txt", b"first", content_type="text/plain"),
                    },
                )
                response_2 = self.client.post(
                    reverse("upload_file"),
                    data={
                        "description": "Второй файл",
                        "file": SimpleUploadedFile("notes.txt", b"second", content_type="text/plain"),
                    },
                )

                upload_dir = Path(media_root) / "uploads" / "raw"
                files = sorted(upload_dir.glob("*"))
                self.assertEqual(response_1.status_code, 200)
                self.assertEqual(response_2.status_code, 200)
                self.assertEqual(len(files), 2)
                self.assertNotEqual(files[0].name, files[1].name)

    def test_model_form_custom_validator_rejects_one_word_title(self):
        form = SpotModelForm(data=self.model_form_payload(title="Одиночка"))
        self.assertFalse(form.is_valid())
        self.assertIn("не менее двух слов", form.errors["title"][0])

    def test_model_form_valid_post_creates_spot_with_photo_and_renders_it(self):
        with tempfile.TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/"):
                response = self.client.post(
                    reverse("model_spot_add"),
                    data={
                        **self.model_form_payload(),
                        "photo": self.make_image_file(),
                    },
                )

                self.assertEqual(response.status_code, 302)
                spot = Spot.objects.get(slug="forma-modeli-tihogo-mesta")
                self.assertTrue(spot.photo.name.startswith("spots/photos/"))
                self.assertTrue((Path(media_root) / spot.photo.name).exists())
                detail_response = self.client.get(reverse("spot_detail", args=(spot.slug,)))
                self.assertEqual(detail_response.status_code, 200)
                self.assertContains(detail_response, spot.photo.url)
