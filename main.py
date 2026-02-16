import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ChatMemberHandler, CallbackQueryHandler, ContextTypes
from telegram import ChatPermissions

BOT_TOKEN = os.getenv("BOT_TOKEN")
VERIFY_TIMEOUT = 60
pending = {}

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        user = member.user
        chat_id = update.effective_chat.id

        await context.bot.restrict_chat_member(
            chat_id,
            user.id,
            ChatPermissions(can_send_messages=False)
        )

        keyboard = [[InlineKeyboardButton("Verify ✅", callback_data=f"verify_{user.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id,
            f"Welcome {user.first_name}\nVerify within 60 seconds.",
            reply_markup=reply_markup
        )

        pending[user.id] = True

        await asyncio.sleep(VERIFY_TIMEOUT)

        if user.id in pending:
            await context.bot.ban_chat_member(chat_id, user.id)
            await context.bot.unban_chat_member(chat_id, user.id)
            del pending[user.id]

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.data.split("_")[1])
    chat_id = query.message.chat.id

    if query.from_user.id != user_id:
        await query.answer("Not your button.", show_alert=True)
        return

    await context.bot.restrict_chat_member(
        chat_id,
        user_id,
        ChatPermissions(can_send_messages=True)
    )

    await query.message.delete()
    await query.answer("Verified!")

    if user_id in pending:
        del pending[user_id]

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(ChatMemberHandler(new_member, ChatMemberHandler.CHAT_MEMBER))
app.add_handler(CallbackQueryHandler(verify))

app.run_polling()
