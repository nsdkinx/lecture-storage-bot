from __future__ import annotations

import locale
from dataclasses import dataclass, field
from datetime import datetime, date

from lecture_storage.core.attachment import Attachment
from lecture_storage.core.lecture_type import LectureType
from lecture_storage.core.subject import Subject


def parse_russian_date(date_string: str) -> date:
    original_locale = locale.getlocale(locale.LC_TIME)

    try:
        try:
            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        except locale.Error:
            locale.setlocale(locale.LC_TIME, 'ru_RU')

        date_format = "%a, %d %B %Y"
        dt_object = datetime.strptime(date_string, date_format)
        return dt_object.date()

    except (ValueError, locale.Error) as e:
        print(f"Ошибка при обработке даты '{date_string}': {e}")
        raise e

    finally:
        locale.setlocale(locale.LC_TIME, original_locale)


def parse_lecture_ids_simple(text: str) -> tuple[int, int]:
    try:
        clean_text = text.strip()

        if ' ' in clean_text:
            absolute_str, relative_str_with_parens = clean_text.split(' ', 1)
            relative_str = relative_str_with_parens.strip('()')

            absolute_id = int(absolute_str)
            relative_id = int(relative_str)
        else:
            absolute_id = int(clean_text)
            relative_id = absolute_id  # relative равен absolute

        return absolute_id, relative_id
    except (ValueError, IndexError):
        raise


@dataclass
class Lecture:
    date_: date
    subject: Subject
    lecture_type: LectureType
    class_id: int  # порядковый номер лекции или практики (по всему предмету)
    # А сейчас будет лютая хуйня...
    # Занятия могут начинаться не с первой пары по расписанию звонков
    # Например, учёба может начаться с 10:15 (2 пара) или 12:30 (3 пара)
    # Таким образом, по факту пара будет первой, но по расписанию она будет второй или третьей
    # А теперь...
    absolute_lecture_id: int  # номер занятия по расписанию звонков
    relative_lecture_id: int  # порядковый номер занятия по факту посещения
    classroom: str
    content: str
    attachments: list[Attachment] = field(default_factory=list)

    def get_unique_id(self) -> str:
        return f'#{self.subject.subject_id} {self.lecture_type}.{self.class_id}'

    @classmethod
    def from_text(cls, text: str) -> Lecture:
        text_lines = text.splitlines()
        first_four_lines = text_lines[:4]
        content = '\n'.join(text_lines[5:])

        subject_name = first_four_lines[0].removeprefix('<b>').removesuffix('</b>')
        subject_id, lecture_meta = first_four_lines[1].removeprefix('#').split()

        lecture_type, class_id = lecture_meta.split('.')
        lecture_type = LectureType(lecture_type)
        class_id = int(class_id)

        date_ = parse_russian_date(first_four_lines[2])

        lecture_ids, classroom = first_four_lines[3].split(' пара ')
        absolute_lecture_id, relative_lecture_id = parse_lecture_ids_simple(lecture_ids)

        subject = Subject(
            name=subject_name,
            subject_id=subject_id
        )

        return Lecture(
            date_=date_,
            subject=subject,
            lecture_type=lecture_type,
            class_id=class_id,
            absolute_lecture_id=absolute_lecture_id,
            relative_lecture_id=relative_lecture_id,
            classroom=classroom,
            content=content
        )
