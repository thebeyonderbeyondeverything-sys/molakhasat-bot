"""Molakhasat Bot - a small Telegram shop for selling study summaries.

Buyers pick a product, pay by Vodafone Cash / InstaPay, send a receipt
photo, and the admin approves with one tap. The bot then delivers the PDF.
"""
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user) and user.id == config.ADMIN_ID and config.ADMIN_ID != 0


def products_keyboard() -> InlineKeyboardMarkup | None:
    products = db.list_products()
    if not products:
        return None
    buttons = [
        [InlineKeyboardButton(f"{p['name']} - {p['price']} {config.CURRENCY}", callback_data=f"buy_{p['id']}")]
        for p in products
    ]
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = products_keyboard()
    if keyboard is None:
        await update.message.reply_text(
            "أهلاً بيك! 👋\nلسه مفيش ملخصات متاحة. جرّب تاني قريب."
        )
        return
    await update.message.reply_text(
        "أهلاً بيك! 👋\nدي الملخصات المتاحة دلوقتي. اختار اللي عايزه:",
        reply_markup=keyboard,
    )


async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    product = db.get_product(product_id)
    if not product or not product["active"]:
        await query.edit_message_text("المنتج ده مش متاح دلوقتي.")
        return
    db.set_selection(query.from_user.id, product_id)
    await query.edit_message_text(
        f"اخترت: {product['name']}\n"
        f"السعر: {product['price']} {config.CURRENCY}\n\n"
        f"حوّل المبلغ على:\n{config.PAYMENT_DETAILS}\n\n"
        "بعد التحويل، ابعت صورة الإيصال هنا في الشات وهيجيلك الملف فور المراجعة. ✅"
    )


async def receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_admin(update):
        return
    product_id = db.get_selection(user.id)
    if product_id is None:
        await update.message.reply_text(
            "اختار الملخص الأول من /start وبعدين ابعت صورة الإيصال."
        )
        return
    product = db.get_product(product_id)
    if not product:
        await update.message.reply_text("حصل خطأ. ابعت /start وحاول تاني.")
        return
    photo_file_id = update.message.photo[-1].file_id
    order_id = db.create_order(user.id, user.username or "", product_id, photo_file_id)
    db.clear_selection(user.id)
    await update.message.reply_text(
        f"وصلت صورة الإيصال ✅\nرقم طلبك: {order_id}\nهنراجع التحويل ونجيلك بالملف."
    )
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ قبول", callback_data=f"approve_{order_id}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_{order_id}"),
            ]
        ]
    )
    username = f"@{user.username}" if user.username else user.full_name
    await context.bot.send_photo(
        chat_id=config.ADMIN_ID,
        photo=photo_file_id,
        caption=(
            f"طلب جديد رقم {order_id}\n"
            f"المشتري: {username}\n"
            f"المنتج: {product['name']} - {product['price']} {config.CURRENCY}"
        ),
        reply_markup=keyboard,
    )


async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not is_admin(update):
        await query.edit_message_caption("الأمر ده للأدمن بس.")
        return
    action, order_id_str = query.data.split("_")
    order_id = int(order_id_str)
    order = db.get_order(order_id)
    if not order or order["status"] != "pending":
        await query.edit_message_caption("الطلب ده اتعامل فيه قبل كده.")
        return
    product = db.get_product(order["product_id"])
    if action == "approve":
        db.set_order_status(order_id, "approved")
        await context.bot.send_document(
            chat_id=order["user_id"],
            document=product["file_id"],
            caption=f"تمام! ✅ دي نسختك من: {product['name']}\nبالتوفيق في المذاكرة 📚",
        )
        await query.edit_message_caption(f"طلب رقم {order_id}: اتقبل ✅ واتبعت الملف.")
    else:
        db.set_order_status(order_id, "rejected")
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                "للأسف التحويل مش واضح أو مش موجود. ❌\n"
                "لو حوّلت فعلاً، ابعت صورة أوضح للإيصال أو كلم صاحب البوت."
            ),
        )
        await query.edit_message_caption(f"طلب رقم {order_id}: اترفض ❌.")


async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin adds a product by sending a PDF with caption: الاسم | السعر"""
    if not is_admin(update):
        return
    document = update.message.document
    if not document:
        return
    caption = (update.message.caption or "").strip()
    if "|" not in caption:
        await update.message.reply_text(
            "عشان تضيف ملخص: ابعت ملف الـPDF وفي الوصف اكتب:\nاسم الملخص | السعر\nمثال: مراجعة علم النفس العام | 25"
        )
        return
    name, _, price_text = caption.partition("|")
    try:
        price = int(price_text.strip())
    except ValueError:
        await update.message.reply_text("السعر لازم يكون رقم. مثال: مراجعة علم النفس العام | 25")
        return
    product_id = db.add_product(name.strip(), price, document.file_id)
    await update.message.reply_text(
        f"اتضاف ✅\nرقم المنتج: {product_id}\nالاسم: {name.strip()}\nالسعر: {price} {config.CURRENCY}"
    )


async def list_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    products = db.list_products(active_only=False)
    if not products:
        await update.message.reply_text("مفيش منتجات لسه.")
        return
    lines = []
    for p in products:
        state = "" if p["active"] else " (موقوف)"
        lines.append(f"{p['id']}. {p['name']} - {p['price']} {config.CURRENCY}{state}")
    lines.append("\nعشان توقف منتج: /remove رقم_المنتج")
    await update.message.reply_text("\n".join(lines))


async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    if not context.args:
        await update.message.reply_text("اكتب: /remove رقم_المنتج")
        return
    try:
        product_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("رقم المنتج لازم يكون رقم صحيح.")
        return
    if db.deactivate_product(product_id):
        await update.message.reply_text(f"اتوقف المنتج رقم {product_id} ✅")
    else:
        await update.message.reply_text("مفيش منتج بالرقم ده.")


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    orders = db.pending_orders()
    if not orders:
        await update.message.reply_text("مفيش طلبات مستنية ✅")
        return
    lines = []
    for o in orders:
        product = db.get_product(o["product_id"])
        name = product["name"] if product else "؟"
        username = f"@{o['username']}" if o["username"] else str(o["user_id"])
        lines.append(f"طلب {o['id']}: {name} - {username}")
    await update.message.reply_text("طلبات مستنية:\n" + "\n".join(lines))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    s = db.stats()
    await update.message.reply_text(
        f"📊 الإحصائيات:\n"
        f"إجمالي الطلبات: {s['total']}\n"
        f"مقبولة: {s['approved']}\n"
        f"مستنية: {s['pending']}\n"
        f"إجمالي المبيعات: {s['revenue']} {config.CURRENCY}"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if is_admin(update):
        await update.message.reply_text(
            "أوامر الأدمن:\n"
            "- ابعت PDF وفي الوصف: الاسم | السعر → يضيف منتج\n"
            "- /list → كل المنتجات\n"
            "- /remove رقم → يوقف منتج\n"
            "- /orders → الطلبات المستنية\n"
            "- /stats → إحصائيات المبيعات"
        )
    else:
        await update.message.reply_text(
            "طريقة الشراء:\n"
            "1. ابعت /start واختار الملخص.\n"
            "2. حوّل المبلغ على الرقم اللي هيظهرلك.\n"
            "3. ابعت صورة الإيصال.\n"
            "4. هيجيلك الملف بعد مراجعة التحويل ✅"
        )


def main() -> None:
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is missing. Copy .env.example to .env and fill it in.")
    if config.ADMIN_ID == 0:
        raise SystemExit("ADMIN_ID is missing. Set your Telegram user id in .env.")
    db.init_db()
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list", list_admin))
    app.add_handler(CommandHandler("remove", remove_product))
    app.add_handler(CommandHandler("orders", orders_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern=r"^buy_\d+$"))
    app.add_handler(CallbackQueryHandler(admin_decision, pattern=r"^(approve|reject)_\d+$"))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.StatusUpdate.ALL, receipt_photo))
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.StatusUpdate.ALL, add_product))
    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
