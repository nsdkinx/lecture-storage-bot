# mappers.py

# Используем псевдонимы, чтобы избежать конфликтов имен и сделать код чище
from lecture_storage.core.lecture import Lecture as DomainLecture, Subject as DomainSubject, Attachment as DomainAttachment
from .models import Lecture as SqlAlchemyLecture, Subject as SqlAlchemySubject, Attachment as SqlAlchemyAttachment


def to_domain_model(lecture_sa: SqlAlchemyLecture) -> DomainLecture:
    """Преобразует SQLAlchemy модель Lecture в доменную модель."""

    # Конвертируем вложения
    domain_attachments = [
        DomainAttachment(
            attachment_type=att_sa.attachment_type,
            file_id=att_sa.file_id,
            ocr_text=att_sa.ocr_text
        ) for att_sa in lecture_sa.attachments
    ]

    return DomainLecture(
        date_=lecture_sa.date,
        subject=DomainSubject(
            subject_id=lecture_sa.subject.subject_id,
            name=lecture_sa.subject.name
        ),
        lecture_type=lecture_sa.lecture_type,
        class_id=lecture_sa.class_id,
        absolute_lecture_id=lecture_sa.absolute_lecture_id,
        relative_lecture_id=lecture_sa.relative_lecture_id,
        classroom=lecture_sa.classroom,
        content=lecture_sa.content,
        attachments=domain_attachments
    )


def to_sqlalchemy_model(lecture_domain: DomainLecture) -> SqlAlchemyLecture:
    """
    Преобразует доменную модель Lecture в SQLAlchemy модель.
    Примечание: вложения (attachments) и предмет (subject) не переносятся напрямую,
    так как репозиторий управляет их созданием и связыванием.
    """
    return SqlAlchemyLecture(
        date=lecture_domain.date_,
        lecture_type=lecture_domain.lecture_type,
        class_id=lecture_domain.class_id,
        absolute_lecture_id=lecture_domain.absolute_lecture_id,
        relative_lecture_id=lecture_domain.relative_lecture_id,
        classroom=lecture_domain.classroom,
        content=lecture_domain.content
    )
