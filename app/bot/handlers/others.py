from aiogram import F, Router
from aiogram.types import Message

router = Router()

@router.message()
async def send_echo(message: Message):
    if message.animation:
        await message.answer_animation(message.animation.file_id)
    elif message.video:
        await message.reply_video(message.video.file_id)
    elif message.voice:
        await message.reply_voice(message.voice.file_id)
    elif message.sticker:
        await message.reply_sticker(message.sticker.file_id)
    elif message.photo:
        await message.reply_photo(message.photo[0].file_id)
    else:
        await message.answer(message.text)