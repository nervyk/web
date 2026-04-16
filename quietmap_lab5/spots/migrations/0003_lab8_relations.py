from django.db import migrations, models
import django.db.models.deletion


def seed_lab8_relations(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    Spot = apps.get_model("spots", "Spot")
    Category = apps.get_model("spots", "Category")
    Tag = apps.get_model("spots", "Tag")
    SpotDetail = apps.get_model("spots", "SpotDetail")
    SpotTagThrough = Spot.tags.through

    tag_specs = {
        1: ("noise-low", "Низкий шум"),
        2: ("noise-medium", "Средний шум"),
        3: ("noise-high", "Высокий шум"),
        "coworking": ("coworking", "Коворкинг"),
        "park": ("park", "Парк"),
        "reading": ("reading", "Чтение"),
    }

    tags = {}
    for key, (slug, name) in tag_specs.items():
        tag, _ = Tag.objects.using(db_alias).get_or_create(slug=slug, defaults={"name": name})
        tags[key] = tag

    for spot in Spot.objects.using(db_alias).all():
        area_slug = spot.area_slug or f"area-{spot.pk}"
        area_name = spot.area or f"Район {spot.pk}"

        category, _ = Category.objects.using(db_alias).get_or_create(
            slug=area_slug,
            defaults={"name": area_name},
        )

        spot.category_id = category.id
        spot.save(update_fields=["category"])

        attach_slugs = [spot.noise_level]
        title = (spot.title or "").lower()
        if "коворкинг" in title:
            attach_slugs.append("coworking")
        if "сквер" in title or "парк" in title:
            attach_slugs.append("park")
        if "зал" in title or "чит" in title:
            attach_slugs.append("reading")

        for slug_key in set(attach_slugs):
            SpotTagThrough.objects.using(db_alias).get_or_create(
                spot_id=spot.id,
                tag_id=tags[slug_key].id,
            )

        seats = 16 if spot.noise_level == 1 else 12 if spot.noise_level == 2 else 8
        avg_stay = 120 if spot.noise_level == 1 else 90 if spot.noise_level == 2 else 60

        SpotDetail.objects.using(db_alias).get_or_create(
            spot_id=spot.id,
            defaults={
                "seats": seats,
                "has_wifi": True,
                "avg_stay_minutes": avg_stay,
                "work_hours": "08:00-22:00",
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("spots", "0002_seed_spots"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=100, verbose_name="Категория")),
                ("slug", models.SlugField(db_index=True, max_length=120, unique=True)),
            ],
            options={
                "verbose_name": "Категория",
                "verbose_name_plural": "Категории",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=80, verbose_name="Тег")),
                ("slug", models.SlugField(db_index=True, max_length=120, unique=True)),
            ],
            options={
                "verbose_name": "Тег",
                "verbose_name_plural": "Теги",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="spot",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="spots",
                to="spots.category",
                verbose_name="Категория",
            ),
        ),
        migrations.AddField(
            model_name="spot",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="spots", to="spots.tag", verbose_name="Теги"),
        ),
        migrations.CreateModel(
            name="SpotDetail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("seats", models.PositiveSmallIntegerField(default=12, verbose_name="Количество мест")),
                ("has_wifi", models.BooleanField(default=True, verbose_name="Есть Wi-Fi")),
                (
                    "avg_stay_minutes",
                    models.PositiveIntegerField(default=90, verbose_name="Средняя длительность посещения, мин"),
                ),
                ("work_hours", models.CharField(default="08:00-22:00", max_length=40, verbose_name="Режим работы")),
                (
                    "spot",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="detail",
                        to="spots.spot",
                        verbose_name="Место",
                    ),
                ),
            ],
            options={
                "verbose_name": "Детали места",
                "verbose_name_plural": "Детали мест",
            },
        ),
        migrations.RunPython(seed_lab8_relations, noop_reverse),
        migrations.AlterField(
            model_name="spot",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="spots",
                to="spots.category",
                verbose_name="Категория",
            ),
        ),
    ]
