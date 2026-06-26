import os, logging, json, asyncio, datetime
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (Application, CommandHandler, MessageHandler, 
                          ChatMemberHandler, filters, ContextTypes)

logging.basicConfig(level=logging.INFO)

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 7771663458
PORT = int(os.environ.get("PORT", 8080))
TEACH_FILE = "teach_data.json"
GROUPS_FILE = "groups.json"

def get_time(): return datetime.datetime.now().strftime("📅 %Y-%m-%d | ⏰ %H:%M:%S")

def load_db(f): 
    try: 
        if os.path.exists(f):
            with open(f, 'r', encoding='utf-8') as file: return json.load(file)
    except: return {}
    return {}

def save_db(f, d): 
    with open(f, 'w', encoding='utf-8') as file: json.dump(d, file, indent=4, ensure_ascii=False)

teach_data = load_db(TEACH_FILE)
groups = load_db(GROUPS_FILE)

# 1. Start Command
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user = u.effective_user
    username = f"@{user.username}" if user.username else "[@Feel_Type_Bot](https://t.me/Feel_Type_Bot)"
    if u.effective_chat.type == 'private':
        text = f"🌸 ဟယ်လို {user.first_name} ရေ...\n🆔 ID: `{user.id}`\n🔗 {username}\n⏰ {get_time()}\n\n🥀 အလွမ်းဆိုတာ တိတ်တိတ်လေး ကျန်ခဲ့တဲ့ နှလုံးသားတစ်ခုပါပဲ။ 🕯️"
        photos = await c.bot.get_user_profile_photos(user.id)
        if photos.total_count > 0: await u.message.reply_photo(photos.photos[0][0].file_id, caption=text, parse_mode='Markdown')
        else: await u.message.reply_text(text, parse_mode='Markdown')
    else:
        groups[str(u.effective_chat.id)] = u.effective_chat.title
        save_db(GROUPS_FILE, groups)

# 2. Member Track
async def track_members(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat = u.effective_chat
    if u.chat_member.new_chat_members:
        await chat.send_message(f"✨ မင်္ဂလာပါ {u.chat_member.new_chat_members[0].first_name} ရေ... ကြိုဆိုပါတယ်လူထည်ခဲ့ အာဘွား။ 🥰")
    elif u.chat_member.old_chat_member.status == ChatMember.MEMBER and u.chat_member.new_chat_member.status == ChatMember.LEFT:
        await chat.send_message(f"🥀 {u.chat_member.old_chat_member.user.first_name} ရေ... ထွက်သွားတော့မလား... လွမ်းနေမယ်နော် အချိန်တိုင်းပြန်လာလို့ရတယ်သုမလိုပဲ ပုံပြင်မ‌ေပြာ‌ေကြး‌ေနာ်။ 🕯️")

# 3. Message Handler
async def msg_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message or not u.message.text: return
    text = u.message.text
    
    # စာသင်ထားတာဆိုရင် အဖြေသက်သက်ပဲ ပြန်မယ် (Typing effect ပါ)
    if text in teach_data:
        await c.bot.send_chat_action(chat_id=u.effective_chat.id, action="typing")
        await asyncio.sleep(3)
        await u.message.reply_text(teach_data[text])
        return
    
    # Forward လုပ်မယ်
    if u.effective_chat.type == 'private':
        user = u.effective_user
        username = f"@{user.username}" if user.username else "[@Feel_Type_Bot](https://t.me/Feel_Type_Bot)"
        info = f"📩 နာမည်: {user.first_name}\n🆔 `{user.id}`\n🔗 {username}\n⏰ {get_time()}\n\n💬 {text}"
        await c.bot.send_message(OWNER_ID, info, parse_mode='Markdown')
        await c.bot.forward_message(OWNER_ID, u.effective_chat.id, u.message.message_id)

# 4. Admin
async def teach(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID or not u.message.reply_to_message: return
    teach_data[u.message.reply_to_message.text] = u.message.text.replace("/teach", "").strip()
    save_db(TEACH_FILE, teach_data)
    await u.message.reply_text("✅ မှတ်သားပြီးပါပြီ။")

async def bcast(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    msg = u.message.text.replace("/bcast", "").strip()
    for g_id in groups.keys():
        try: await c.bot.send_message(g_id, f"📢 {msg}")
        except: continue
    await u.message.reply_text("✅ ပို့ပြီးပါပြီ။")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("teach", teach))
    app.add_handler(CommandHandler("bcast", bcast))
    app.add_handler(ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    runner = web.AppRunner(web.Application())
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    await asyncio.Event().wait()

if __name__ == "__main__": asyncio.run(main())
      
