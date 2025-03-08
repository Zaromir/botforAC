import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from langdetect import detect
from datetime import datetime

# Set up logging for error handling
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '7493606940:AAGRp7FGfVUDrhOZ9O4clIW52DH5wrFw0EE'
CHANNEL_ID = '@botforAC'

banned_words = ['хохол', 'хуй', 'пізда']
banned_symbols = ['Ъ', 'ъ', 'Ы', 'ы', 'Э', 'э', 'Ё', 'ё']
allowed_languages = ['uk', 'en']

total_message_count = 0
daily_message_count = 0
last_reset_date = datetime.now().date()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Error handler
@dp.errors_handler()
async def error_handler(update: types.Update, exception: Exception):
    logger.error(f"Update: {update} caused error: {exception}")
    if isinstance(exception, Exception):
        await bot.send_message(CHANNEL_ID, "⚠️ Бот зіткнувся з помилкою, але продовжує працювати.")
    return True

# Start command handler
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_name = message.from_user.first_name
    await message.reply(f"Вітаємо тебе, {user_name}, в боті команди Anime Classic! Напиши своє повідомлення або пропозицію команді!")

# Message forwarder
@dp.message_handler(lambda message: message.text)
async def forward_message(message: types.Message):
    global total_message_count, daily_message_count
    user_name = message.from_user.username
    user_profile_link = f"t.me/{user_name}" if user_name else None
    display_name = f"@{user_name}" if user_name else message.from_user.full_name

    # Check banned words/symbols
    if any(banned_word in message.text.lower() for banned_word in banned_words) or \
       any(banned_symbol in message.text for banned_symbol in banned_symbols):
        await message.reply("Твоє повідомлення містить заборонені слова або символи і не може бути надіслане.")
        return

    # Check language
    try:
        language = detect(message.text)
        if language not in allowed_languages:
            await message.reply("В команді ніхто не розуміє свинособачу. Йди рохкай деінде. Пішов нахуй москалику.")
            return
    except:
        await message.reply("Не вдалося визначити мову повідомлення.")
        return

    if message.text:
        text = f"{message.text}\n\n— [{display_name}]({user_profile_link})"
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode='Markdown')
        total_message_count += 1
        daily_message_count += 1

    # Reply with keyboard
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("Зв'язок", callback_data='contact')]
        ]
    )
    await message.answer("Натисніть кнопку 'Зв'язок' для відправки повідомлення, але майте на увазі, якщо у вас закритий профіль, ми не зможемо вам відповісти", reply_markup=keyboard)

# Callback query handler
@dp.callback_query_handler(lambda query: query.data in ['contact', 'cancel'])
async def handle_callback(query: types.CallbackQuery):
    try:
        if query.data == 'contact':
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton("Скасувати", callback_data='cancel')]
                ]
            )
            await query.message.edit_text("Надішліть нам ваше побажання/рекомендацію/подяку", reply_markup=keyboard)
        elif query.data == 'cancel':
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton("Зв'язок", callback_data='contact')]
                ]
            )
            await query.message.edit_text("Процес введення повідомлення був скасований. Ви можете почати заново, натиснувши кнопку 'Зв'язок'.", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Callback query error: {e}")

# Self-test function
async def self_test():
    global daily_message_count, total_message_count, last_reset_date
    custom_message = "Русня хуйня. Це автоматичне повідомлення від бота для тестування, якщо ви його побачили бот працює в штатному режимі."
    await bot.send_message(chat_id=CHANNEL_ID, text=f"Кількість отриманих повідомлень за сьогодні: {daily_message_count}\nЗагальна кількість отриманих повідомлень: {total_message_count}\n\n{custom_message}")

    if datetime.now().date() != last_reset_date:
        daily_message_count = 0
        last_reset_date = datetime.now().date()

    await bot.send_message(chat_id=CHANNEL_ID, text="Self-test completed successfully.")

# On startup
async def on_startup(_):
    await bot.send_message(chat_id=CHANNEL_ID, text="Бот отримав копняка і пішов працювати.")

# Scheduler for self-test
async def scheduler():
    while True:
        now = datetime.now().time()
        if now.hour in [10, 15, 22] and now.minute == 0:  # Test at specific times
            await self_test()
        await asyncio.sleep(60)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    executor.start_polling(dp, on_startup=on_startup)
