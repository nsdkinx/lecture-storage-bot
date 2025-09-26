import asyncio
import logging
import sys
import io
import os

from PIL import Image
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReactionTypeEmoji

from lecture_storage.core.lecture import Lecture
from lecture_storage.database.repository import LectureRepository
from lecture_storage.database.engine import init_db, get_db

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

date_format = '%d.%m.%Y %H:%M:%S'
logging_format = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'

handlers = [
    logging.StreamHandler(sys.stdout)
]

logging.basicConfig(
    format=logging_format,
    datefmt=date_format,
    handlers=handlers,
    level=logging.DEBUG
)

async def process_text_message(text: str):
    async with get_db() as session:
        repository = LectureRepository(session)
        lecture = Lecture.from_text(text)
        await repository.add_lecture(lecture)

        all_lectures = await repository.get_all_lectures()
    print(all_lectures)


async def process_image(image: Image.Image, subtitle: str):
    print("Получено изображение с подписью:", subtitle)

channel_router = Router()

channel_router.channel_post.filter(F.chat.id == CHANNEL_ID)       # <--- ИЗМЕНЕНО
channel_router.edited_channel_post.filter(F.chat.id == CHANNEL_ID) # <--- ИЗМЕНЕНО


@channel_router.channel_post(F.text) # <--- ИЗМЕНЕНО
async def handle_text_only_message(channel_post: Message): # <--- ИЗМЕНЕНО (имя переменной для ясности)
    """
    Этот хэндлер ловит новые текстовые ПОСТЫ в канале.
    """
    try:
        await process_text_message(channel_post.html_text)
    except ValueError:
        await channel_post.react(
            reaction=[ReactionTypeEmoji(emoji="👎")]
        )
        raise

    await channel_post.react(
        reaction=[ReactionTypeEmoji(emoji="👀")]
    )


@channel_router.edited_channel_post(F.text) # <--- ИЗМЕНЕНО
async def handle_edited_text_message(edited_channel_post: Message): # <--- ИЗМЕНЕНО
    """
    Этот хэндлер ловит редактирование текстовых ПОСТОВ в канале.
    """
    await process_text_message(edited_channel_post.html_text)


@channel_router.channel_post(F.photo) # <--- ИЗМЕНЕНО
async def handle_photo_with_caption(channel_post: Message, bot: Bot): # <--- ИЗМЕНЕНО
    """
    Этот хэндлер ловит новые посты с фото.
    """
    if channel_post.caption:
        photo_bytes = await bot.download(channel_post.photo[-1])
        image = Image.open(io.BytesIO(photo_bytes.read()))
        await process_image(image, channel_post.caption)


@channel_router.edited_channel_post(F.photo) # <--- ИЗМЕНЕНО
async def handle_edited_photo_message(edited_channel_post: Message, bot: Bot): # <--- ИЗМЕНЕНО
    """
    Этот хэндлер ловит редактирование поста с фото.
    """
    if edited_channel_post.caption:
        photo_bytes = await bot.download(edited_channel_post.photo[-1])
        image = Image.open(io.BytesIO(photo_bytes.read()))
        await process_image(image, edited_channel_post.caption)


async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(channel_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["channel_post", "edited_channel_post"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
