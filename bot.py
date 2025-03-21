import json
import requests
from balethon.objects import InlineKeyboard, InlineKeyboardButton
from balethon import Client

# اطلاعات ربات
bot_token = "2071296181:C1ouATv8fb7OjzcR5y8aqlwtEnxlkPrMFCtNzqGz"
TIPAX_API = "https://open.wiki-api.ir/apis-1/TipaxInfo?code="
ADMIN_ID = 2143480267  # آیدی ادمین

# راه‌اندازی بات
bot = Client(bot_token)

# دیتابیس سبک
DB_FILE = "users.json"

# تلاش برای بارگذاری کاربران از فایل JSON
try:
    with open(DB_FILE, "r", encoding="utf-8") as f:
        file_content = f.read().strip()  # حذف فضای خالی و کاراکترهای اضافی
        users = json.loads(file_content) if file_content else {}  # بررسی اگر فایل خالی بود
except (FileNotFoundError, json.JSONDecodeError):
    users = {}  # اگر فایل وجود نداشت یا JSON نامعتبر بود، مقدار پیش‌فرض را تنظیم کن

# ذخیره کاربران در فایل
def save_users():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
# دکمه‌های منو اصلی
main_menu_buttons = InlineKeyboard([
    [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")],
    [InlineKeyboardButton("بازوی صراط", url="https://ble.ir/seratbot")],
    [InlineKeyboardButton("کانال ما", url="https://ble.ir/shafag_tm")]
])

@bot.on_message()
async def handle_message(message):
    chat_id = message.chat.id

    # ثبت کاربر جدید
    if str(chat_id) not in users:
        users[str(chat_id)] = {"joined_at": message.date, "waiting_for_feedback": False}
        save_users()

    tracking_code = message.text.strip()

    if tracking_code == "/start":
        await bot.send_message(chat_id, "**سلام! 👋**\nبرای پیگیری مرسوله تیپاکس، کد رهگیری را وارد کنید.", reply_markup=main_menu_buttons)
        return
    
    if tracking_code == "/admin" and chat_id == ADMIN_ID:
        user_count = len(users)
        buttons = InlineKeyboard([
            [InlineKeyboardButton(f"👥 تعداد کاربران: {user_count}", callback_data="show_user_count")]
        ])
        await bot.send_message(chat_id, "🔧 **پنل مدیریت**\nلطفاً یک گزینه را انتخاب کنید:", reply_markup=buttons)
        return

    if not tracking_code.isdigit() or len(tracking_code) != 21:
        await bot.send_message(chat_id, "❌ **کد رهگیری باید ۲۱ رقمی و عددی باشد.**")
        return

    please_wait = await bot.send_message(chat_id, "⏳ **در حال بررسی...**")

    try:
        response = requests.get(f"{TIPAX_API}{tracking_code}")

        if response.status_code != 200:
            await bot.edit_message_text(chat_id, please_wait.message_id, "❌ **خطا در اتصال به سرور. لطفاً دوباره تلاش کنید.**")
            return

        data = response.json()

        if "status" not in data or "results" not in data:
            await bot.edit_message_text(chat_id, please_wait.message_id, "🔮 **اطلاعات مرسوله پیدا نشد.**")
            return

        results = data["results"]
        sender = results.get("sender", {})
        receiver = results.get("receiver", {})
        status_info = results.get("status_info", [])

        parcel_info = f"""📦 **اطلاعات مرسوله:**
📤 **فرستنده:** {sender.get("name", "نامشخص")} از {sender.get("city", "نامشخص")}
📥 **گیرنده:** {receiver.get("name", "نامشخص")} در {receiver.get("city", "نامشخص")}
🚚 **وزن:** {results.get("weight", "نامشخص")} کیلوگرم
📦 **نوع بسته:** {results.get("COD", "نامشخص")}
💸 **هزینه کل:** {results.get("total_cost", "نامشخص")} تومان
🔄 **وضعیت پرداخت:** {results.get("pay_type", "نامشخص")}
🌍 **مسافت:** {results.get("city_distance", "نامشخص")} کیلومتر
📍 **محدوده:** {results.get("distance_zone", "نامشخص")}
"""

        if status_info:
            parcel_info += "\n📝 **وضعیت مرسوله:**\n"
            for status in status_info:
                parcel_info += f"""📅 **تاریخ:** {status.get("date", "نامشخص")}
🔹 **وضعیت:** {status.get("status", "نامشخص")}
📍 **محل:** {status.get("representation", "نامشخص")}\n\n"""

        await bot.edit_message_text(chat_id, please_wait.message_id, parcel_info, reply_markup=InlineKeyboard([
            [InlineKeyboardButton("🔙 بازگشت به منو اصلی", callback_data="main_menu")],
            [InlineKeyboardButton("ارتباط با سازنده بازو", url="https://ble.ir/devehsan")]
        ]))

    except Exception as e:
        print(f"خطا: {e}")
        await bot.edit_message_text(chat_id, please_wait.message_id, "❌ **خطا در دریافت اطلاعات. لطفاً بعداً تلاش کنید.**")

@bot.on_callback_query()
async def on_callback(callback_query):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    data = callback_query.data

    if data == "show_user_count":
        user_list = "\n".join([f"Chat ID: {chat}" for chat in users])
        text = f"👥 **لیست کاربران:**\n\n{user_list}" if user_list else "❌ هیچ کاربری ثبت نشده است."
        await bot.send_message(chat_id, text)

    elif data == "help":
        help_text = """
📌 **راهنمای استفاده از ربات:**
1️⃣ **کد رهگیری تیپاکس** خود را ارسال کنید.
2️⃣ اطلاعات مرسوله برای شما نمایش داده می‌شود. 📦
        """
        await bot.edit_message_text(chat_id, message_id, help_text, reply_markup=InlineKeyboard([
            [InlineKeyboardButton("🔙 بازگشت به منو اصلی", callback_data="main_menu")]
        ]))

    elif data == "main_menu":
        await bot.edit_message_text(chat_id, message_id, "**کد رهگیری خود را ارسال کنید**", reply_markup=main_menu_buttons)

# اجرای ربات
bot.run()
