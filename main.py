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

def get_time(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user = u.effective_user
    if u.effective_chat.type == 'private':
        username = f"@{user.username}" if user.username else "[No link](https://t.me/Feel_Type_Bot)"
        text = f"🌸 ဟယ်လို {user.first_name} ရေ...\n🆔 ID: `{user.id}`\n🔗 {username}\n⏰ အချိန်: {get_time()}"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Group ထဲသို့ထည့်ရန်", url="https://t.me/Feel_Type_Bot?startgroup=true")]])
        try:
            photos = await c.bot.get_user_profile_photos(user.id)
            if photos.total_count > 0: await u.message.reply_photo(photos.photos[0][0].file_id, caption=text, reply_markup=kb, parse_mode='Markdown')
            else: await u.message.reply_text(text, reply_markup=kb, parse_mode='Markdown')
        except: await u.message.reply_text(text, reply_markup=kb, parse_mode='Markdown')
    else:
        groups[str(u.effective_chat.id)] = u.effective_chat.title
        save_db(GROUPS_FILE, groups)
        await u.message.reply_text("✨ Group ID မှတ်သားပြီးပါပြီ။")

async def track_members(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat = u.effective_chat
    if u.chat_member.new_chat_members:
        user = u.chat_member.new_chat_members[0]
        await chat.send_message(f"🌸 မင်္ဂလာပါ {user.first_name} ရေ... နွေးထွေးစွာ ကြိုဆိုပါတယ် တစ်ခြားမှာမရခဲ့တာတွေတီမှာရစေရမယ်။ 🥰")
    elif u.chat_member.old_chat_member.status == ChatMember.MEMBER and u.chat_member.new_chat_member.status == ChatMember.LEFT:
        user = u.chat_member.old_chat_member.user
        await chat.send_message(f"🥀 {user.first_name} ရေ... ပင်ပန်းလာရင် ပြန်လာခဲ့ပါနော်... အချိန်တိုင်း စောင့်နေမယ် သစ်စာမဖောက်တက်ပဘူးနင်ပြန်တဲ့အချိန်ကို‌ေစာင့်‌ေနမာပ။ 🕯️")

async def msg_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message: return
    if u.effective_chat.type == 'private':
        info = f"👤 User: {u.effective_user.first_name}\n🆔 ID: `{u.effective_user.id}`\n⏰ အချိန်: {get_time()}"
        await c.bot.send_message(OWNER_ID, info, parse_mode='Markdown')
        await c.bot.forward_message(OWNER_ID, u.effective_chat.id, u.message.message_id)
        
        if u.message.text and u.message.text in teach_data:
            await c.bot.send_chat_action(chat_id=u.effective_chat.id, action="typing")
            await asyncio.sleep(5)
            await u.message.reply_text(teach_data[u.message.text])

async def teach(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID or not u.message.reply_to_message: return
    teach_data[u.message.reply_to_message.text] = u.message.text.replace("/teach", "").strip()
    save_db(TEACH_FILE, teach_data)
    await u.message.reply_text("✅ မှတ်သားပြီးပါပြီ။")

async def bcast(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    msg = u.message.text.replace("/bcast", "").strip()
    s, f = 0, 0
    for g_id in groups.keys():
        try: await c.bot.send_message(g_id, msg); s+=1
        except: f+=1
    await u.message.reply_text(f"✅ ကြေညာချက် (ရောက်: {s}, မရောက်: {f})")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("teach", teach))
    app.add_handler(CommandHandler("bcast", bcast))
    app.add_handler(ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL, msg_handler))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    runner = web.AppRunner(web.Application())
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    await asyncio.Event().wait()

if __name__ == "__main__": asyncio.run(main())
      
