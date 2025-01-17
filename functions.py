from pyrogram.errors import SessionPasswordNeeded

async def verify_code(message, user_id, code, user_data):
    client = user_data[user_id]["client"]
    phone_number = user_data[user_id]["phone"]
    phone_code_hash = user_data[user_id].get("phone_code_hash")
    try:
        await client.sign_in(
            phone_number=phone_number,
            phone_code=code,
            phone_code_hash=phone_code_hash
        )
        try:
            user = await client.get_me()
            await message.answer("Успешно авторизован!")
            await parse_chats(client, user_id, user_data)
        except Exception as e:
            await message.answer(f"Ошибка авторизации: {str(e)}")
    except SessionPasswordNeeded:
        await message.answer("Включена двухфакторная аутентификация. Укажите пароль:")
    except Exception as e:
        await message.answer(f"Ошибка авторизации: {str(e)}")

async def parse_chats(client, user_id, user_data):
    chats_info = []
    async for dialog in client.get_dialogs():            chat = dialog.chat
        chat_info = {
            "id": chat.id,
            "title": chat.title if chat.title else (
                f"{chat.first_name or ''} {chat.last_name or ''}".strip() or "Unknown"
            ),
            "type": chat.type.name
        }
        chats_info.append(chat_info)
    
    file_path = f"user_{user_id}_chats.txt"
    with open(file_path, 'w', encoding='utf-8') as file:
        for chat_info in chats_info:
            file.write(f"ID: {chat_info['id']}, Title: {chat_info['title']}, Type: {chat_info['type']}\n")
            