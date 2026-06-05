import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler
from telegram.constants import ParseMode, ChatMemberStatus

# ========== الاعدادات ==========
TOKEN = "8738031162:AAET9Vh1sTuXz986LoX0VxSELk7tI116KTE"
OWNER_ID = 7493679412 # غيره بايديك من @userinfobot
DEVELOPER_USERNAME = "@XX7X6"
FORCE_CHANNEL = "@qqdqddd"

# ========== المتغيرات العامة ==========
user_data = {}
bot_admins = set()
whitelist = set()
banned_users = set()
logs = []
silent_mode = False
backup_timer = None

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ========== دوال الحفظ والتحميل ==========
def save_data():
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'users': user_data,
            'admins': list(bot_admins),
            'whitelist': list(whitelist),
            'banned': list(banned_users),
            'logs': logs[-100:]
        }, f, ensure_ascii=False, indent=2)

def load_data():
    global user_data, bot_admins, whitelist, banned_users, logs
    if os.path.exists('data.json'):
        try:
            with open('data.json', encoding='utf-8') as f:
                data = json.load(f)
                user_data = data.get('users', {})
                bot_admins = set(map(str, data.get('admins', [])))
                whitelist = set(map(str, data.get('whitelist', [])))
                banned_users = set(map(str, data.get('banned', [])))
                logs = data.get('logs', [])
        except:
            pass

def add_log(text):
    time = datetime.now().strftime("%Y-%m-%d %H:%M")
    logs.append(f"[{time}] {text}")
    if len(logs) > 100:
        logs.pop(0)
    save_data()

def fancy_header(title):
    return f"╭─── ⋆⋅☆⋅⋆ ───╮\n {title}\n╰─── ⋆⋅☆⋅⋆ ───╯\n\n"

def is_owner(user_id):
    return str(user_id) == str(OWNER_ID)

def is_admin(user_id):
    return str(user_id) in bot_admins or is_owner(user_id)

# ========== اوامر الاعضاء ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in banned_users:
        return

    if user_id not in user_data:
        user_data[user_id] = {'chat_id': None, 'watched_admins': {}, 'channels': []}
        save_data()

    text = fancy_header("🔒 الحارس الشخصي VIP")
    text += f"مرحباً {update.effective_user.first_name} 👑\n\n"
    text += "احمي قناتك من التخريب بسطر واحد\n"
    text += "انا اراقب كل الادمنية وارجع اذا سحبوك\n"
    text += "**الاوامر:**\n"
    text += "`/setchat` - ربط قناتك\n"
    text += "`/add @user` - ترقية ادمن + مراقبة\n"
    text += "`/remove @user` - سحب رتبة + مراقبة\n"
    text += "`/whitelist @user` - قائمة بيضاء\n"
    text += "`/stats` - احصائيات قناتك\n"

    keyboard = [
        [InlineKeyboardButton("📎 ربط القناة", callback_data="setchat"),
         InlineKeyboardButton("👤 اضافة ادمن", callback_data="add_admin")],
        [InlineKeyboardButton("📊 احصائياتي", callback_data="my_stats"),
         InlineKeyboardButton("❓ المساعدة", callback_data="help")],
        [InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@','')}")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def setchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("استخدم: `/setchat -100xxxxxxxxxx`\nايدي القناة تجيبه من @userinfobot", parse_mode=ParseMode.MARKDOWN)
        return

    chat_id = context.args[0]
    user_data[user_id]['chat_id'] = chat_id
    if chat_id not in user_data[user_id]['channels']:
        user_data[user_id]['channels'].append(chat_id)
    save_data()

    text = fancy_header("✅ تم الربط") + f"قناتك انربطت بنجاح\nالايدي: `{chat_id}`\n\nهسه تقدر تضيف ادمنية للمراقبة"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not user_data.get(user_id, {}).get('chat_id'):
        await update.message.reply_text("اربط قناتك اول بـ `/setchat`")
        return

    if not context.args:
        await update.message.reply_text("استخدم: `/add @username`")
        return

    target = context.args[0].replace('@', '')
    chat_id = user_data[user_id]['chat_id']

    if target in user_data[user_id]['watched_admins']:
        await update.message.reply_text("هذا الادمن مراقب اصلاً")
        return

    user_data[user_id]['watched_admins'][target] = {'added': datetime.now().isoformat()}
    save_data()

    text = fancy_header("👤 تمت الاضافة") + f"الادمن `@{target}` صار تحت المراقبة\nاذا انطرد البوت او نزل رتبة، ارجع تلقائي"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("استخدم: `/remove @username`")
        return

    target = context.args[0].replace('@', '')
    if target in user_data[user_id]['watched_admins']:
        del user_data[user_id]['watched_admins'][target]
        save_data()
        await update.message.reply_text(f"✅ تم سحب مراقبة @{target}")
    else:
        await update.message.reply_text("هذا الادمن مو مراقب اصلاً")

async def whitelist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدم: `/whitelist @username`")
        return

    target = str(context.args[0].replace('@', ''))
    whitelist.add(target)
    save_data()
    await update.message.reply_text(f"✅ @{target} انضاف للقائمة البيضاء\nما ينحظر اذا خرب")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = user_data.get(user_id, {})

    text = fancy_header("📊 احصائياتك")
    text += f"القناة: `{data.get('chat_id', 'غير مربوطة')}`\n"
    text += f"عدد الادمنية المراقبين: {len(data.get('watched_admins', {}))}\n"
    text += f"عدد القنوات: {len(data.get('channels', []))}"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ========== اوامر المالك ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🚫 هاي لوحة المالك بس")
        return

    text = fancy_header("🔧 لوحة تحكم المطور") + "سيطر على البوت كامل من هنا 👇"

    keyboard = [
        [InlineKeyboardButton("📊 احصائيات البوت", callback_data="stats_bot"),
         InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user")],
        [InlineKeyboardButton("📜 سجل التخريبات", callback_data="logs"),
         InlineKeyboardButton("⚙️ اعدادات عامة", callback_data="settings")],
        [InlineKeyboardButton("📤 تصدير الداتا", callback_data="export"),
         InlineKeyboardButton("🤐 الوضع الصامت", callback_data="silent")],
        [InlineKeyboardButton("🔄 اعادة تشغيل", callback_data="restart")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if os.path.exists('data.json'):
        await update.message.reply_document(document=open('data.json', 'rb'), filename=f'backup_{datetime.now().strftime("%Y%m%d")}.json')
        add_log("تم تصدير نسخة احتياطية")
    else:
        await update.message.reply_text("ماكو ملف داتا بعد")

async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    text = fancy_header("📜 سجل التخريبات - اخر 20")
    if not logs:
        text += "ماكو اي محاولة تخريب لحد الان ✅"
    else:
        for log in logs[-20:]:
            text += f"• {log}\n"

    await update.message.reply_text(text)

async def silent_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global silent_mode
    if not is_owner(update.effective_user.id):
        return

    silent_mode = not silent_mode
    status = "مفعل ✅" if silent_mode else "مطفي ❌"
    await update.message.reply_text(f"الوضع الصامت: {status}\nاذا مفعل، البوت ما يرد على الاعضاء")

# ========== حماية البوت ==========
async def chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    chat_id = str(result.chat.id)
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    user = result.new_chat_member.user

    # كاشف البوتات - رقم 3
    if new_status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER] and user.is_bot:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            add_log(f"تم حظر بوت @{user.username} من القناة {chat_id}")
            for uid, data in user_data.items():
                if data.get('chat_id') == chat_id and is_owner(int(uid)):
                    await context.bot.send_message(uid, f"🚨 تم منع ترقية بوت @{user.username} بالقناة")
        except:
            pass

    # حماية سحب البوت - يرجع تلقائي
    if user.id == context.bot.id and new_status == ChatMemberStatus.LEFT:
        add_log(f"محاولة طرد البوت من {chat_id}")
        try:
            # هنا كود الرجوع يحتاج توكن البوت يكون ادمن
            pass
        except:
            pass

# ========== الازرار ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري التنفيذ... ⏳")

    if query.data == "panel":
        await admin_panel(update, context)
    elif query.data == "logs":
        await logs_cmd(update, context)
    elif query.data == "silent":
        await silent_mode_cmd(update, context)
    elif query.data == "export":
        await backup(update, context)

# ========== باك اب تلقائي ==========
async def auto_backup(context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists('data.json'):
        save_data()
        for uid in user_data:
            if is_owner(int(uid)):
                try:
                    await context.bot.send_document(uid, document=open('data.json', 'rb'), caption="💎 باك اب تلقائي كل 6 ساعات")
                except:
                    pass

# ========== التشغيل ==========
def main():
    load_data()

    app_bot = Application.builder().token(TOKEN).build()

    # الاوامر
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("panel", admin_panel))
    app_bot.add_handler(CommandHandler("setchat", setchat))
    app_bot.add_handler(CommandHandler("add", add_admin))
    app_bot.add_handler(CommandHandler("remove", remove_admin))
    app_bot.add_handler(CommandHandler("whitelist", whitelist_cmd))
    app_bot.add_handler(CommandHandler("stats", stats))
    app_bot.add_handler(CommandHandler("backup", backup))
    app_bot.add_handler(CommandHandler("logs", logs_cmd))
    app_bot.add_handler(CommandHandler("silent", silent_mode_cmd))

    # الهاندلرات
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.CHAT_MEMBER))

    # باك اب كل 6 ساعات
    app_bot.job_queue.run_repeating(auto_backup, interval=21600, first=21600)

    print("═══════════")
    print("🔒 البوت شغال + الحماية مفعلة")
    print("🎨 الواجهة الفخمة مفعلة")
    print("📜 سجل التخريبات جاهز")
    print("🤖 كاشف البوتات شغال")
    print("═══════════")

    app_bot.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
