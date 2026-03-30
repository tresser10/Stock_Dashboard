import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

BOT_TOKEN = "8714847478:AAHVP_UwHGGUnkPnKCmjEgdBG-c0xB6cCr8"
BASE_URL = "http://127.0.0.1:5000"

alerts = []

# -------------------------------
# START MENU
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Top Gainers", callback_data="gainers")],
        [InlineKeyboardButton("📉 Top Losers", callback_data="losers")],
        [InlineKeyboardButton("📊 Market Summary", callback_data="summary")]
    ]

    await update.message.reply_text(
        "📊 NSE Stock Bot\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------------------------------
# BUTTON HANDLER
# -------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "gainers":
        res = requests.get(f"{BASE_URL}/api/quotes?gainers=true")
        data = res.json()[:5]

        msg = "🚀 Top Gainers:\n\n"
        for s in data:
            msg += f"{s['symbol']} → {s['pChange']}%\n"

        await query.edit_message_text(msg)

    elif query.data == "losers":
        res = requests.get(f"{BASE_URL}/api/quotes?losers=true")
        data = res.json()[:5]

        msg = "📉 Top Losers:\n\n"
        for s in data:
            msg += f"{s['symbol']} → {s['pChange']}%\n"

        await query.edit_message_text(msg)

    elif query.data == "summary":
        res = requests.get(f"{BASE_URL}/api/quotes")
        data = res.json()

        gainers = len([s for s in data if s["pChange"] > 0])
        losers = len([s for s in data if s["pChange"] < 0])

        msg = f"""
📊 Market Summary
Gainers: {gainers}
Losers: {losers}
"""
        await query.edit_message_text(msg)

# -------------------------------
# PRICE COMMAND
# -------------------------------
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price RELIANCE")
        return

    symbol = context.args[0].upper()

    res = requests.get(f"{BASE_URL}/api/quotes?search={symbol}")
    data = res.json()

    if not data:
        await update.message.reply_text("❌ Stock not found")
        return

    s = data[0]

    msg = f"""
📊 {s['symbol']}
Price: ₹{s['price']}
Change: {s['pChange']}%
"""

    await update.message.reply_text(msg)

# -------------------------------
# ALERT COMMAND
# -------------------------------
async def set_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper()
        target = float(context.args[1])

        alerts.append({
            "chat_id": update.effective_chat.id,
            "symbol": symbol,
            "target": target
        })

        await update.message.reply_text(
            f"✅ Alert set for {symbol} at ₹{target}"
        )

    except:
        await update.message.reply_text("Usage: /alert RELIANCE 3000")

# -------------------------------
# ALERT CHECKER
# -------------------------------
async def alert_checker(app):
    while True:
        for alert in alerts.copy():
            try:
                res = requests.get(f"{BASE_URL}/api/quotes?search={alert['symbol']}")
                data = res.json()

                if not data:
                    continue

                price = data[0]["price"]

                if price and price >= alert["target"]:
                    await app.bot.send_message(
                        chat_id=alert["chat_id"],
                        text=f"🚨 ALERT: {alert['symbol']} reached ₹{price}"
                    )
                    alerts.remove(alert)

            except Exception as e:
                print("Alert error:", e)

        await asyncio.sleep(10)

# -------------------------------
# BACKGROUND TASK
# -------------------------------
async def post_init(app):
    asyncio.create_task(alert_checker(app))

# -------------------------------
# MAIN
# -------------------------------
app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("price", price))
app.add_handler(CommandHandler("alert", set_alert))

app.add_handler(CallbackQueryHandler(button_handler))

print("🤖 Bot running...")
app.run_polling()