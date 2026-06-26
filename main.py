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

# --- Utilities ---
def get_time(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 1. Start Command (User Profile & Link)
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user = u.effective_user
    if u.effective_chat.type == 'private':
        username = f"@{user.username}" if user.username else "No link"
        text = (f"🌸 ဟယ်လို {user.first_name} ရေ...\n"
                f"🆔 ID: `{user.id}`\n🔗 Username: {username}\n⏰ အချိန်: {get_time()}\n\n"
                f"စုံစမ်းရန်: @Feel_Type_Bot")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Group ထဲထည့်ရန်", url="https://t.me/Makima_wecome_bot?startgroup=true")]])
        
        try:
            photos = await c.bot.get_user_profile_photos(user.id)
            if photos.total_count > 0: await u.message.reply_photo(photos.photos[0][0].file_id, caption=text, reply_markup=kb, parse_mode='Markdown')
            else: await u.message.reply_text(text, reply_markup=kb, parse_mode='Markdown')
        except: await u.message.reply_text(text, reply_markup=kb, parse_mode='Markdown')
    else:
        groups[str(u.effective_chat.id)] = u.effective_chat.title
        save_db(GROUPS_FILE, groups)
        await u.message.reply_text("✨ Group ID ကို ကဗျာဆန်ဆန် မှတ်သားပြီးပါပြီရှင်။")

# 2. Welcome & Goodbye
async def track_members(u: Update, c: ContextTypes.DEFAULT_TYPE):
    try:
        chat = u.effective_chat
        if u.chat_member.new_chat_members:
            user = u.chat_member.new_chat_members[0]
            username = f"@{user.username}" if user.username else "No link"
            text = f"🌸 မင်္ဂလာပါ {user.first_name} ရေ...\nဒီနေရာလေးက သင့်အတွက်နွေးထွေးမှုတွေပေးဖို့ အသင့်ပါ။\n🆔 `{user.id}` | {username}"
            await chat.send_message(text, parse_mode='Markdown')
        elif u.chat_member.old_chat_member.status == ChatMember.MEMBER and u.chat_member.new_chat_member.status == ChatMember.LEFT:
            user = u.chat_member.old_chat_member.user
            await chat.send_message(f"🥀 {user.first_name} ရေ... ခွဲခွာရတော့မှာလား။ ပင်ပန်းလာရင် ပြန်လာခဲ့ပါနော်... အမြဲစောင့်နေမယ်။ 🕯️", parse_mode='Markdown')
    except: pass

# 3. Message Handler (Forward & Teach Reply)
async def msg_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message or u.effective_chat.type != 'private': return
    
    # Typing Effect
    await c.bot.send_chat_action(chat_id=u.effective_chat.id, action="typing")
    
    # Forward to Owner
    try:
        user = u.effective_user
        info = f"👤 User: {user.first_name}\n🆔 ID: `{user.id}`\n🔗 @{user.username or 'No Link'}\n⏰ {get_time()}"
        await c.bot.send_message(OWNER_ID, f"📩 **New Message:**\n{info}")
        await c.bot.forward_message(OWNER_ID, u.effective_chat.id, u.message.message_id)
    except: pass
    
    # Reply logic
    if u.message.reply_to_message and u.message.reply_to_message.text in teach_data:
        await u.message.reply_text(teach_data[u.message.reply_to_message.text])

# 4. Admin Commands
async def teach(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    args = u.message.text.split(":", 1)
    if len(args) == 2:
        teach_data[args[0].strip()] = args[1].strip()
        save_db(TEACH_FILE, teach_data)
        await u.message.reply_text("✅ မှတ်သားပြီးပါပြီရှင်။")

async def bcast(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    msg = u.message.text.replace("/bcast", "").strip()
    success, fail = 0, 0
    for g_id in groups.keys():
        try:
            await c.bot.send_message(g_id, f"📢 {msg}")
            success += 1
        except: fail += 1
    await u.message.reply_text(f"✅ ပို့ပြီးပါပြီ။\nရောက်: {success} | မရောက်: {fail}")

# 5. Keep Alive (5 မိနစ်တစ်ခါနိုး)
async def keep_alive():
    while True:
        logging.info("Bot is active!")
        await asyncio.sleep(300)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("teach", teach))
    app.add_handler(CommandHandler("bcast", bcast))
    app.add_handler(ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, msg_handler))
    
    runner = web.AppRunner(web.Application())
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.gather(keep_alive())

if __name__ == "__main__": asyncio.run(main())
      
