from django.db import models
from django.urls import reverse


class PublishedSpotManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status=Spot.PublicationStatus.PUBLISHED
        )


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
    area = models.CharField(max_length=120, verbose_name="Район")
    area_slug = models.SlugField(max_length=120, db_index=True)
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
