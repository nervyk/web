from django.db import models
from django.urls import reverse

from .uploads import spot_photo_upload_to


class PublishedSpotManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status=Spot.PublicationStatus.PUBLISHED
        )


class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name="Категория")
    slug = models.SlugField(max_length=120, unique=True, db_index=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category", kwargs={"category_slug": self.slug})


class Tag(models.Model):
    name = models.CharField(max_length=80, db_index=True, verbose_name="Тег")
    slug = models.SlugField(max_length=120, unique=True, db_index=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("tag", kwargs={"tag_slug": self.slug})


class Spot(models.Model):
    class NoiseLevel(models.IntegerChoices):
        LOW = 1, "Низкий"
        MEDIUM = 2, "Средний"
        HIGH = 3, "Высокий"

    class PublicationStatus(models.IntegerChoices):
        DRAFT = 0, "Черновик"
        PUBLISHED = 1, "Опубликовано"

    title = models.CharField(max_length=255, verbose_name="Название места")
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    content = models.TextField(blank=True, verbose_name="Описание")
    photo = models.ImageField(
        upload_to=spot_photo_upload_to,
        blank=True,
        null=True,
        verbose_name="Фотография",
    )
    area = models.CharField(max_length=120, verbose_name="Район")
    area_slug = models.SlugField(max_length=120, db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="spots",
        verbose_name="Категория",
    )
    noise_level = models.PositiveSmallIntegerField(
        choices=NoiseLevel.choices,
        default=NoiseLevel.MEDIUM,
        verbose_name="Уровень шума",
    )
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    status = models.PositiveSmallIntegerField(
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED,
        db_index=True,
        verbose_name="Статус публикации",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="spots",
        verbose_name="Теги",
    )

    objects = models.Manager()
    published = PublishedSpotManager()

    class Meta:
        verbose_name = "Тихое место"
        verbose_name_plural = "Тихие места"
        ordering = ["-time_create"]
        indexes = [
            models.Index(fields=["-time_create"]),
            models.Index(fields=["status"]),
            models.Index(fields=["area_slug"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("spot_detail", kwargs={"spot_slug": self.slug})


class SpotDetail(models.Model):
    spot = models.OneToOneField(
        Spot,
        on_delete=models.CASCADE,
        related_name="detail",
        verbose_name="Место",
    )
    seats = models.PositiveSmallIntegerField(default=12, verbose_name="Количество мест")
    has_wifi = models.BooleanField(default=True, verbose_name="Есть Wi-Fi")
    avg_stay_minutes = models.PositiveIntegerField(
        default=90,
        verbose_name="Средняя длительность посещения, мин",
    )
    work_hours = models.CharField(
        max_length=40,
        default="08:00-22:00",
        verbose_name="Режим работы",
    )

    class Meta:
        verbose_name = "Детали места"
        verbose_name_plural = "Детали мест"

    def __str__(self):
        return f"Детали: {self.spot.title}"
