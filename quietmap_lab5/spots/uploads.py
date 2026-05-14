from pathlib import Path
import uuid

from django.conf import settings


def build_random_media_path(prefix: str, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    random_name = f"{uuid.uuid4().hex}{extension}"
    clean_prefix = prefix.strip("/ ")
    return f"{clean_prefix}/{random_name}"


def spot_photo_upload_to(instance, filename: str) -> str:
    return build_random_media_path("spots/photos", filename)


def save_uploaded_file(uploaded_file, prefix: str = "uploads/raw") -> str:
    relative_path = build_random_media_path(prefix, uploaded_file.name)
    destination = Path(settings.MEDIA_ROOT) / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb+") as target:
        for chunk in uploaded_file.chunks():
            target.write(chunk)

    return relative_path
