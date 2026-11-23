from datetime import date

from app.core.storage import file_url
from app.models import Child
from app.schemas.family import ChildRead


def age_in_months(dob: date, today: date | None = None) -> int:
    today = today or date.today()
    months = (today.year - dob.year) * 12 + (today.month - dob.month)
    if today.day < dob.day:
        months -= 1
    return max(months, 0)


def to_child_read(child: Child) -> ChildRead:
    data = ChildRead.model_validate(
        {
            **{c: getattr(child, c) for c in ChildRead.model_fields if hasattr(child, c)},
            "age_months": age_in_months(child.date_of_birth),
            "photo_url": file_url(child.photo_key, "private"),
        }
    )
    return data
