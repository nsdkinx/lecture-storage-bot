from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Enum,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

from lecture_storage.core.lecture_type import LectureType
from lecture_storage.core.attachment_type import AttachmentType

Base = declarative_base()


class Subject(Base):
    __tablename__ = "subjects"

    subject_id = Column(String, unique=True, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    lectures = relationship("Lecture", back_populates="subject")

    def __repr__(self):
        return f"<Subject(subject_id={self.subject_id}, name='{self.name}')>"


class Lecture(Base):
    __tablename__ = "lectures"

    lecture_unique_id = Column(String, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    lecture_type = Column(Enum(LectureType), nullable=False)
    class_id = Column(Integer, index=True)
    absolute_lecture_id = Column(Integer, nullable=False)
    relative_lecture_id = Column(Integer)
    classroom = Column(String)
    content = Column(Text)

    subject_id = Column(String, ForeignKey("subjects.subject_id"), nullable=False)
    subject = relationship("Subject", back_populates="lectures")

    attachments = relationship(
        "Attachment",
        back_populates="lecture",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Lecture(lecture_unique_id={self.lecture_unique_id}, date='{self.date}', subject='{self.subject.name}')>"


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    attachment_type = Column(Enum(AttachmentType), nullable=False)
    file_id = Column(String, nullable=False)
    ocr_text = Column(Text, nullable=True)
    lecture_id = Column(Integer, ForeignKey("lectures.lecture_unique_id"), nullable=False)
    lecture = relationship("Lecture", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment(id={self.id}, type='{self.attachment_type}')>"
