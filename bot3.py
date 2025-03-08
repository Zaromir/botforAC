import os
import schedule
import time
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.error import NetworkError, RetryAfter, TimedOut, BadRequest
from langdetect import detect
from datetime import datetime
import asyncio

# Set timezone to GMT+2
os.environ['TZ'] = 'Europe/Kiev'
time.tzset()

TOKEN = ''
CHANNEL_ID = ''

banned_words = ['хохол', 'хуй', 'пізда']
banned_symbols = ['Ъ', 'ъ', 'Ы', 'ы', 'Э', 'э', 'Ё', 'ё']
allowed_languages = ['uk', 'en']

total_message_count = 0
daily_message_count = 0
last_reset_date = datetime.now().date()

async def start(update, context):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"Вітаємо тебе, {user_name}, в боті команди Anime Classic! Напиши своє повідомлення або пропозицію команді!")

async def forward_message(update, context):
    global total_message_count, daily_message_count
    message = update.message
    user_name = message.from_user.username
    user_profile_link = f"t.me/{user_name}" if user_name else None
    display_name = f"@{user_name}" if user_name else message.from_user.full_name

    if any(banned_word in message.text.lower() for banned_word in banned_words) or \
       any(banned_symbol in message.text for banned_symbol in banned_symbols):
        await update.message.reply_text("Твоє повідомлення містить заборонені слова або символи і не може бути надіслане.")
        return
    try:
        language = detect(message.text)
        if language not in allowed_languages:
            await update.message.reply_text("В команді ніхто не розуміє свинособачу. Йди рохкай деінде. Пішов нахуй москалику.")
            return
    except:
        await update.message.reply_text("Не вдалося визначити мову повідомлення.")
        return

    if message.text:
        text = f"{message.text}\n\n— [{display_name}]({user_profile_link})"
        await send_with_retry(context.bot.send_message, chat_id=CHANNEL_ID, text=text, parse_mode='Markdown')
        total_message_count += 1
        daily_message_count += 1

    keyboard = [[InlineKeyboardButton("Зв'язок", callback_data='contact')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.message.chat_id, text="Натисніть кнопку 'Зв'язок' для відправки повідомлення, але майте на увазі, якщо у вас закритий профіль, ми не зможемо вам відповісти", reply_markup=reply_markup)

async def button(update, context):
    query = update.callback_query
    try:
        if query.data == 'contact':
            await query.answer()
            keyboard = [[InlineKeyboardButton("Скасувати", callback_data='cancel')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="Надішліть нам ваше побажання/рекомендацію/подяку", reply_markup=reply_markup)
        elif query.data == 'cancel':
            await query.answer()
            keyboard = [[InlineKeyboardButton("Зв'язок", callback_data='contact')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="Процес введення повідомлення був скасований. Ви можете почати заново, натиснувши кнопку 'Зв'язок'.", reply_markup=reply_markup)
    except BadRequest as e:
        if "query is too old" in str(e):
            print("Callback query is too old or invalid.")
        else:
            print(f"Error: {e}")

async def send_with_retry(func, *args, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except (NetworkError, RetryAfter, TimedOut) as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            await asyncio.sleep(5)
    print("Max retries reached, message sending failed.")

async def self_test(context):
    global daily_message_count, total_message_count, last_reset_date
    custom_message = "Русня хуйня. Це автоматичне повідомлення від бота для тестування, якщо ви його побачили бот працює в штатному режимі."
    await context.bot.send_message(chat_id=CHANNEL_ID, text=f"Кількість отриманих повідомлень за сьогодні: {daily_message_count}\nЗагальна кількість отриманих повідомлень: {total_message_count}\n\n{custom_message}")

    if datetime.now().date() != last_reset_date:
        daily_message_count = 0
        last_reset_date = datetime.now().date()

    # Send a message to the channel after the self-test
    await context.bot.send_message(chat_id=CHANNEL_ID, text="Self-test completed successfully.")

async def on_startup(application):
    await application.bot.send_message(chat_id=CHANNEL_ID, text="Бот отримав копняка і пішов працювати.")

def main():
    print("Бот працює...")
    application = Application.builder().token(TOKEN).build()

    async def run():
        await application.initialize()
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
        application.add_handler(CallbackQueryHandler(button))

        # Add the startup handler
        await on_startup(application)

        await application.start()
        await application.updater.start_polling()

        schedule.every().day.at("10:00").do(lambda: asyncio.create_task(self_test(application)))
        schedule.every().day.at("15:00").do(lambda: asyncio.create_task(self_test(application)))
        schedule.every().day.at("22:00").do(lambda: asyncio.create_task(self_test(application)))

        while True:
            schedule.run_pending()
            await asyncio.sleep(1)

    # Create a new event loop and set it as the current event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run())
    except asyncio.CancelledError:
        print("Operation was cancelled")
    finally:
        loop.close()

if __name__ == '__main__':
    main()
