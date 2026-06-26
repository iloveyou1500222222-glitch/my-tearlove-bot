import os, logging, json, asyncio
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

# 1. Start Command (Group ထည့်ရန် ခလုတ်ပါဝင်သည်)
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_chat.type == 'private':
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Group ထဲသို့ထည့်ရန်", url="https://t.me/Feel_Type_Bot?startgroup=true")]])
        await u.message.reply_text("🌸 ဟယ်လို! ညီမလေးကို Group ထဲ ခေါ်သွားပေးပါဦးရှင်။", reply_markup=kb)
    else:
        groups[str(u.effective_chat.id)] = u.effective_chat.title
        save_db(GROUPS_FILE, groups)
        await u.message.reply_text("✨ Group ID မှတ်သားပြီးပါပြီရှင်။")

# 2. Welcome & Goodbye (လူဝင်လူထွက် ကြိုဆို/နှုတ်ဆက်)
async def track_members(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat = u.effective_chat
    if u.chat_member.new_chat_members:
        user = u.chat_member.new_chat_members[0]
        text = f"🌸 {user.first_name} ရေ... နွေးထွေးစွာ ကြိုဆိုပါတယ်။ 🥰"
        await chat.send_message(text)
    elif u.chat_member.old_chat_member.status == ChatMember.MEMBER and u.chat_member.new_chat_member.status == ChatMember.LEFT:
        user = u.chat_member.old_chat_member.user
        await chat.send_message(f"🥀 {user.first_name} ရေ... ပင်ပန်းလာရင် ပြန်လာခဲ့ပါနော်... အချိန်တိုင်း စောင့်နေမယ်။ 🕯️")

# 3. Message Handler (Forward, Typing Effect, Teach)
async def msg_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message: return
    
    # Private chat ဆို Forward လုပ်
    if u.effective_chat.type == 'private':
        await c.bot.forward_message(OWNER_ID, u.effective_chat.id, u.message.message_id)
        
        # စာသင်ထားတာကို Reply ပေးရင် ပြန်ဖြေခြင်း
        if u.message.reply_to_message:
            q = u.message.reply_to_message.text
            if q in teach_data:
                await c.bot.send_chat_action(chat_id=u.effective_chat.id, action="typing")
                await asyncio.sleep(1)
                await u.message.reply_text(teach_data[q])

# 4. Admin (Teach & Bcast)
async def teach(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    if u.message.reply_to_message:
        q = u.message.reply_to_message.text
        a = u.message.text.replace("/teach", "").strip()
        teach_data[q] = a
        save_db(TEACH_FILE, teach_data)
        await u.message.reply_text("✅ မှတ်သားပြီးပါပြီ။")

async def bcast(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    msg = u.message.text.replace("/bcast", "").strip()
    s, f = 0, 0
    for g_id in groups.keys():
        try: await c.bot.send_message(g_id, msg); s+=1
        except: f+=1
    await u.message.reply_text(f"✅ ကြေညာချက်ပြီးပါပြီ။ (ရောက်: {s}, မရောက်: {f})")

# Main
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("teach", teach))
    app.add_handler(CommandHandler("bcast", bcast))
    app.add_handler(ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL, msg_handler))
    
    runner = web.AppRunner(web.Application())
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__": asyncio.run(main())
      
