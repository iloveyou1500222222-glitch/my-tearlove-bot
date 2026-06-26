import json
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (Application, CommandHandler, MessageHandler, 
                          ChatMemberHandler, filters, ContextTypes)

logging.basicConfig(level=logging.INFO)

# Render Environment Variables မှ Token ယူခြင်း
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 7771663458
TEACH_FILE = "teach_data.json"

# Database Loading
def load_db(f): 
    try: 
        if os.path.exists(f):
            with open(f, 'r', encoding='utf-8') as file: return json.load(file)
    except: pass
    return {}

def save_db(f, d): 
    with open(f, 'w', encoding='utf-8') as file: json.dump(d, file, indent=4, ensure_ascii=False)

teach_data = load_db(TEACH_FILE)

# Start Command
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user = u.effective_user
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Group ထဲသို့ထည့်ရန်", url="https://t.me/Makima_wecome_bot?startgroup=true")]
    ])
    username = f"@{user.username}" if user.username else "No link"
    text = (f"ဟယ်လို သဲသဲရေ! 👋\n\n👤 နာမည်: {user.first_name}\n🆔 ID: `{user.id}`\n🔗 Username: {username}\n"
            f"⏰ အချိန်: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        photos = await c.bot.get_user_profile_photos(user.id)
        if photos.total_count > 0:
            await u.message.reply_photo(photos.photos[0][0].file_id, caption=text, reply_markup=kb, parse_mode='Markdown')
        else:
            await u.message.reply_text(text, reply_markup=kb, parse_mode='Markdown')
    except:
        await u.message.reply_text(text, reply_markup=kb, parse_mode='Markdown')

# Welcome & Goodbye
async def track_members(u: Update, c: ContextTypes.DEFAULT_TYPE):
    try:
        chat = u.effective_chat
        if u.chat_member.new_chat_members:
            new_user = u.chat_member.new_chat_members[0]
            username = f"@{new_user.username}" if new_user.username else "No link"
            text = (f"🌸 **မင်္ဂလာပါရှင်...** 🌸\n\n{chat.title} လေးထဲကို ကြွလှမ်းလာတဲ့ {new_user.first_name} ကို ကြိုဆိုပါတယ်ရှင်။\n\n"
                    f"🆔 ID: `{new_user.id}`\n🔗 Username: {username}\n⏰ အချိန်: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"ပျော်ရွှင်စရာတွေ ဖန်တီးနိုင်ပါစေရှင်။ 🥰")
            await chat.send_message(text, parse_mode='Markdown')
        
        elif u.chat_member.old_chat_member.status == ChatMember.MEMBER and u.chat_member.new_chat_member.status == ChatMember.LEFT:
            left_user = u.chat_member.old_chat_member.user
            text = f"🥀 **နှုတ်ဆက်ပါတယ်ရှင်...** 🥀\n\n{left_user.first_name} ရေ... ထွက်သွားတော့မှာလား။ အတူရှိခဲ့တဲ့ အချိန်လေးတွေက အမှတ်တရပါရှင်။ အမြဲတမ်း ပျော်ရွှင်ပါစေနော်... 🕯️"
            await chat.send_message(text, parse_mode='Markdown')
    except: pass

# Handler
async def msg_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message or not u.message.text: return
    if u.effective_chat.type == 'private' and not u.message.text.startswith('/'):
        try: await c.bot.forward_message(OWNER_ID, u.effective_chat.id, u.message.message_id)
        except: pass
    if u.message.text in teach_data:
        await u.message.reply_text(teach_data[u.message.text])

async def teach(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    args = u.message.text.split(":", 1)
    if len(args) == 2:
        teach_data[args[0].strip()] = args[1].strip()
        save_db(TEACH_FILE, teach_data)
        await u.message.reply_text("✅ မှတ်သားပြီးပါပြီရှင်။")

if __name__ == "__main__":
    if not BOT_TOKEN: print("❌ BOT_TOKEN missing!")
    else:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("teach", teach))
        app.add_handler(ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER))
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, msg_handler))
        app.run_polling()
                                   
