import os, logging, json, asyncio
from aiohttp import web
from telegram import Update, ChatMember
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

# 1. Start (Profile နှင့် အချက်အလက်များ)
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    chat = u.effective_chat
    user = u.effective_user
    if chat.type in ['group', 'supergroup']:
        groups[str(chat.id)] = chat.title
        save_db(GROUPS_FILE, groups)
        await u.message.reply_text(f"🌸 {chat.title} အဖွဲ့ထဲသို့ ဝင်ရောက်လာခြင်းအတွက် ကျေးဇူးတင်ပါတယ်။ သဲသဲတို့ Group လေးကို စောင့်ရှောက်ဖို့ ID ကို မှတ်သားလိုက်ပါပြီရှင်။ 🥰")
    else:
        username = f"@{user.username}" if user.username else "No link"
        text = (f"🌸 ဟယ်လို {user.first_name} ရေ...\n\n"
                f"👤 နာမည်: {user.first_name}\n"
                f"🆔 ID: `{user.id}`\n"
                f"🔗 Username: {username}\n\n"
                f"ညီမလေးကို Group လေးထဲ ခေါ်သွားပေးပါဦးရှင်။ Group ထဲမှာ ပျော်ရွှင်စရာတွေ ဖန်တီးပေးဖို့ အသင့်ရှိနေပါတယ်ရှင်။ 🥰")
        try:
            photos = await c.bot.get_user_profile_photos(user.id)
            if photos.total_count > 0: await u.message.reply_photo(photos.photos[0][0].file_id, caption=text, parse_mode='Markdown')
            else: await u.message.reply_text(text, parse_mode='Markdown')
        except: await u.message.reply_text(text, parse_mode='Markdown')

# 2. လူဝင်လူထွက်စနစ် (ကဗျာဆန်ဆန်)
async def track_members(u: Update, c: ContextTypes.DEFAULT_TYPE):
    try:
        chat = u.effective_chat
        if u.chat_member.new_chat_members:
            user = u.chat_member.new_chat_members[0]
            await chat.send_message(f"🌸 မင်္ဂလာပါ {user.first_name} ရေ... {chat.title} လေးထဲကို နွေးထွေးစွာ ကြိုဆိုပါတယ်။ အတူတူ ပျော်ရွှင်ကြမယ်နော်။ ✨", parse_mode='Markdown')
        elif u.chat_member.old_chat_member.status == ChatMember.MEMBER and u.chat_member.new_chat_member.status == ChatMember.LEFT:
            await chat.send_message(f"🥀 {u.chat_member.old_chat_member.user.first_name} ရေ... ခွဲခွာရတော့မှာလား။ အတူရှိခဲ့တဲ့ အချိန်လေးတွေက အမှတ်တရပါရှင်။ အမြဲပျော်ရွှင်ပါစေနော်... 🕯️")
    except: pass

# 3. Admin ခေါ်ခြင်း (@mention)
async def admin_call(u: Update, c: ContextTypes.DEFAULT_TYPE):
    admins = await u.effective_chat.get_administrators()
    mentions = [f"@{a.user.username}" for a in admins if not a.user.is_bot and a.user.username]
    if mentions: await u.message.reply_text(f"🔊 *Admin များရှင်... အရေးကြီးကိစ္စရှိလို့ ခေါ်နေပါတယ်နော်!* 🔊\n\n🚩 *Admins:* {' '.join(mentions)}", parse_mode='Markdown')

# 4. စာသင်ခြင်း & Forward (အကုန်လုံးပို့မည်)
async def msg_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not u.message: return
    if u.effective_chat.type == 'private':
        # Owner ဆီသို့ အကုန်ပို့ခြင်း
        try: await c.bot.forward_message(OWNER_ID, u.effective_chat.id, u.message.message_id)
        except: pass
        if u.message.text and u.message.text in teach_data:
            await u.message.reply_text(teach_data[u.message.text])

# 5. ကြေညာချက် (Owner Only)
async def bcast(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID: return
    msg = u.message.text.replace("/bcast", "").strip()
    for g_id in groups.keys():
        try: await c.bot.send_message(g_id, f"📢 *ကြေညာချက်:* {msg}", parse_mode='Markdown')
        except: continue

# --- Main App ---
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("teach", teach))
    app.add_handler(CommandHandler("bcast", bcast))
    app.add_handler(CommandHandler("admin", admin_call))
    app.add_handler(ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL, msg_handler))
    
    # Port ဖွင့်ခြင်း
    runner = web.AppRunner(web.Application())
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT).start()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__": asyncio.run(main())
      
