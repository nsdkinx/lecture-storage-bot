from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from . import mappers

from lecture_storage.core.lecture import Lecture
from lecture_storage.core.attachment import Attachment

from .models import Lecture as LectureDAO
from .models import Subject as SubjectDAO
from .models import Attachment as AttachmentDAO


class LectureRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_lecture(self, lecture: Lecture) -> Lecture:
        new_lecture_sa = mappers.to_sqlalchemy_model(lecture)

        # 1. Найти или создать связанный предмет (Subject)
        stmt = select(SubjectDAO).where(
            SubjectDAO.subject_id == lecture.subject.subject_id
        )
        subject_sa = await self.session.scalar(stmt)

        if not subject_sa:
            subject_sa = SubjectDAO(
                subject_id=lecture.subject.subject_id,
                name=lecture.subject.name
            )
            self.session.add(subject_sa)

        new_lecture_sa.subject = subject_sa
        new_lecture_sa.lecture_unique_id = lecture.get_unique_id()

        # 2. Добавить вложения, если они есть
        for att_domain in lecture.attachments:
            new_lecture_sa.attachments.append(AttachmentDAO(
                attachment_type=att_domain.attachment_type,
                file_id=att_domain.file_id,
                ocr_text=att_domain.ocr_text
            ))

        self.session.add(new_lecture_sa)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ValueError(f"Лекция с ID '{new_lecture_sa.lecture_unique_id}' уже существует.")

        return lecture

    async def get_lecture_by_unique_id(self, unique_id: str) -> Optional[Lecture]:
        """
        Находит лекцию по ID и возвращает ее в виде доменной модели.
        """
        stmt = (
            select(LectureDAO)
            .options(
                selectinload(LectureDAO.subject),
                selectinload(LectureDAO.attachments)
            )
            .where(LectureDAO.lecture_unique_id == unique_id)
        )
        lecture_sa = await self.session.scalar(stmt)

        return mappers.to_domain_model(lecture_sa) if lecture_sa else None

    async def list_lectures_by_subject(self, subject_id: str) -> List[Lecture]:
        """
        Возвращает список всех лекций по предмету в виде доменных моделей.
        """
        stmt = (
            select(LectureDAO)
            .join(SubjectDAO)
            .options(
                selectinload(LectureDAO.subject),
                selectinload(LectureDAO.attachments)
            )
            .where(SubjectDAO.subject_id == subject_id)
            .order_by(LectureDAO.date)
        )
        result = await self.session.execute(stmt)
        lectures_sa = result.scalars().all()

        return [mappers.to_domain_model(lec) for lec in lectures_sa]

    async def update_lecture_content(self, unique_id: str, new_content: str) -> Optional[Lecture]:
        """
        Обновляет контент лекции и возвращает обновленную доменную модель.
        """
        stmt = select(LectureDAO).where(LectureDAO.lecture_unique_id == unique_id)
        lecture_sa = await self.session.scalar(stmt)

        if lecture_sa:
            lecture_sa.content = new_content
            await self.session.commit()
            # Обновляем связи, чтобы маппер получил актуальные данные
            await self.session.refresh(lecture_sa, attribute_names=['subject', 'attachments'])
            return mappers.to_domain_model(lecture_sa)
        return None

    async def add_attachments_to_lecture(self, unique_id: str, attachments_domain: List[Attachment]) -> Optional[
        Lecture]:
        """
        Добавляет вложения к существующей лекции.
        """
        stmt = (
            select(LectureDAO)
            .options(selectinload(LectureDAO.attachments))
            .where(LectureDAO.lecture_unique_id == unique_id)
        )
        lecture_sa = await self.session.scalar(stmt)

        if lecture_sa:
            for att_domain in attachments_domain:
                lecture_sa.attachments.append(AttachmentDAO(
                    attachment_type=att_domain.attachment_type,
                    file_id=att_domain.file_id,
                    ocr_text=att_domain.ocr_text
                ))
            await self.session.commit()
            await self.session.refresh(lecture_sa, attribute_names=['subject', 'attachments'])
            return mappers.to_domain_model(lecture_sa)
        return None

    async def delete_lecture(self, unique_id: str) -> bool:
        """
        Удаляет лекцию по ее уникальному ID.
        """
        stmt = select(LectureDAO).where(LectureDAO.lecture_unique_id == unique_id)
        lecture_sa = await self.session.scalar(stmt)

        if lecture_sa:
            await self.session.delete(lecture_sa)
            await self.session.commit()
            return True
        return False

    async def get_all_lectures(self) -> List[Lecture]:
        stmt = (
            select(LectureDAO)
            .options(
                selectinload(LectureDAO.subject),
                selectinload(LectureDAO.attachments)
            )
            .order_by(LectureDAO.date)  # Сортировка для предсказуемого порядка
        )
        result = await self.session.execute(stmt)
        lectures_sa = result.scalars().all()

        # Преобразуем каждую SQLAlchemy модель в доменную
        return [mappers.to_domain_model(lecture_dao) for lecture_dao in lectures_sa]
