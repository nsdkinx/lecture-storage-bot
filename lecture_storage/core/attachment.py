from dataclasses import dataclass

from lecture_storage.core.attachment_type import AttachmentType


@dataclass
class Attachment:
    attachment_type: AttachmentType
    file_id: str
    ocr_text: str | None = None