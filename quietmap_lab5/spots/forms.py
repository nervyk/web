from django import forms
from django.core.validators import FileExtensionValidator, MinLengthValidator, RegexValidator

from .models import Category, Spot, SpotDetail, Tag


PLACEHOLDER_TITLE_MARKERS = ("test", "тест", "demo", "пример")


def validate_meaningful_title(value: str) -> None:
    lowered = value.casefold()
    if any(marker in lowered for marker in PLACEHOLDER_TITLE_MARKERS):
        raise forms.ValidationError(
            "Название не должно содержать служебные слова test, тест, demo или пример."
        )


class SpotPlainForm(forms.Form):
    title = forms.CharField(
        label="Название места",
        max_length=255,
        validators=[MinLengthValidator(5), validate_meaningful_title],
        help_text="Обычная форма без привязки к модели. Запись будет создана вручную во view.",
    )
    slug = forms.SlugField(label="Slug", max_length=255)
    content = forms.CharField(
        label="Описание",
        widget=forms.Textarea(attrs={"rows": 5}),
        validators=[MinLengthValidator(20)],
    )
    area = forms.CharField(label="Район", max_length=120)
    area_slug = forms.SlugField(label="Slug района", max_length=120)
    category = forms.ModelChoiceField(label="Категория", queryset=Category.objects.none())
    noise_level = forms.TypedChoiceField(
        label="Уровень шума",
        choices=Spot.NoiseLevel.choices,
        coerce=int,
        initial=Spot.NoiseLevel.MEDIUM,
    )
    status = forms.TypedChoiceField(
        label="Статус публикации",
        choices=Spot.PublicationStatus.choices,
        coerce=int,
        initial=Spot.PublicationStatus.PUBLISHED,
    )
    tags = forms.ModelMultipleChoiceField(
        label="Теги",
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    seats = forms.IntegerField(label="Количество мест", min_value=1, max_value=200, initial=12)
    has_wifi = forms.BooleanField(label="Есть Wi-Fi", required=False, initial=True)
    avg_stay_minutes = forms.IntegerField(
        label="Средняя длительность посещения, мин",
        min_value=10,
        max_value=720,
        initial=90,
    )
    work_hours = forms.CharField(
        label="Режим работы",
        max_length=40,
        initial="08:00-22:00",
        validators=[
            RegexValidator(
                regex=r"^\d{2}:\d{2}-\d{2}:\d{2}$",
                message="Укажите режим работы в формате ЧЧ:ММ-ЧЧ:ММ.",
            )
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.all()
        self.fields["tags"].queryset = Tag.objects.all()

    def save(self) -> Spot:
        data = self.cleaned_data
        spot = Spot.objects.create(
            title=data["title"],
            slug=data["slug"],
            content=data["content"],
            area=data["area"],
            area_slug=data["area_slug"],
            category=data["category"],
            noise_level=data["noise_level"],
            status=data["status"],
        )
        spot.tags.set(data["tags"])
        SpotDetail.objects.create(
            spot=spot,
            seats=data["seats"],
            has_wifi=data["has_wifi"],
            avg_stay_minutes=data["avg_stay_minutes"],
            work_hours=data["work_hours"],
        )
        return spot


class SpotModelForm(forms.ModelForm):
    seats = forms.IntegerField(label="Количество мест", min_value=1, max_value=200, initial=12)
    has_wifi = forms.BooleanField(label="Есть Wi-Fi", required=False, initial=True)
    avg_stay_minutes = forms.IntegerField(
        label="Средняя длительность посещения, мин",
        min_value=10,
        max_value=720,
        initial=90,
    )
    work_hours = forms.CharField(
        label="Режим работы",
        max_length=40,
        initial="08:00-22:00",
        validators=[
            RegexValidator(
                regex=r"^\d{2}:\d{2}-\d{2}:\d{2}$",
                message="Укажите режим работы в формате ЧЧ:ММ-ЧЧ:ММ.",
            )
        ],
    )

    class Meta:
        model = Spot
        fields = (
            "title",
            "slug",
            "content",
            "photo",
            "area",
            "area_slug",
            "category",
            "noise_level",
            "status",
            "tags",
        )
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
            "tags": forms.CheckboxSelectMultiple(),
        }
        help_texts = {
            "photo": "Изображение будет сохранено в media со случайным именем файла.",
        }

    def clean_title(self) -> str:
        title = self.cleaned_data["title"].strip()
        words = [word for word in title.split() if word.strip()]
        if len(words) < 2:
            raise forms.ValidationError("Название должно содержать не менее двух слов.")
        return title

    def save(self, commit: bool = True) -> Spot:
        spot = super().save(commit=commit)
        detail_defaults = {
            "seats": self.cleaned_data["seats"],
            "has_wifi": self.cleaned_data["has_wifi"],
            "avg_stay_minutes": self.cleaned_data["avg_stay_minutes"],
            "work_hours": self.cleaned_data["work_hours"],
        }
        if commit:
            SpotDetail.objects.update_or_create(spot=spot, defaults=detail_defaults)
        else:
            self._detail_defaults = detail_defaults
        return spot


class UploadFileForm(forms.Form):
    description = forms.CharField(label="Комментарий", max_length=100, required=False)
    file = forms.FileField(
        label="Файл",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["txt", "pdf", "doc", "docx", "png", "jpg", "jpeg"]
            )
        ],
        help_text="Для ЛР10 можно загружать документы и изображения. При сохранении имя будет заменено на случайное.",
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if uploaded_file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Размер файла не должен превышать 5 МБ.")
        return uploaded_file
