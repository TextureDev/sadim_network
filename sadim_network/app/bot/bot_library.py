import os
import telebot
from telebot import types
from time import time
from models.library_mdl import Library
from config.settings import TOKEN, ADMIN_ID
from app.db.sadim_db import get_db_connection

# ══════════════════════════════════════════
#                الإعدادات والمتغيرات
# ════════════════════════════════════════

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=15)

# التخزين المؤقت وحالات المستخدمين
verified_cache = {}
user_states = {}
forwarded_msgs = {}

# ══════════════════════════════════════════
#                دوال قاعدة البيانات
# ══════════════════════════════════════════

def execute_query(query, params=(), fetch=False, fetchall=False, commit=False):
    conn = get_db_connection()
    cur = conn.cursor()
    result = None
    try:
        cur.execute(query, params)
        if commit:
            conn.commit()
        if fetch:
            result = cur.fetchone()
        if fetchall:
            result = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return result

def add_user_bot(user):
    query = """
        INSERT INTO users_bot (id, username, first_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username, is_active = TRUE;
    """
    execute_query(query, (user.id, user.username, user.first_name), commit=True)

def get_force_channels():
    rows = execute_query("SELECT id, name, invite_link FROM channels;", fetchall=True)
    return [{"db_id": r[0], "name": r[1], "invite": r[2]} for r in rows]

def add_channel(name, invite_link):
    # نعتمد على SERIAL لتوليد id الداخلي كما في المخطط الخاص بك
    query = "INSERT INTO channels (name, invite_link) VALUES (%s, %s);"
    execute_query(query, (name, invite_link), commit=True)

def delete_channel(db_id):
    execute_query("DELETE FROM channels WHERE id = %s;", (db_id,), commit=True)

def get_all_users():
    return execute_query("SELECT id FROM users_bot WHERE is_active = TRUE;", fetchall=True)

def log_broadcast(message_text):
    query = "INSERT INTO broadcasts (message_preview, message) VALUES (%s, %s) RETURNING id;"
    preview = message_text[:50] + "..." if len(message_text) > 50 else message_text
    result = execute_query(query, (preview, message_text), fetch=True, commit=True)
    return result[0] if result else None

def update_broadcast_stats(broadcast_id, total, success, failed):
    query = "UPDATE broadcasts SET total_users = %s, success_count = %s, failed_count = %s WHERE id = %s;"
    execute_query(query, (total, success, failed, broadcast_id), commit=True)

def log_broadcast_receiver(broadcast_id, user_id, status, error_msg=None):
    query = "INSERT INTO broadcast_receivers (broadcast_id, user_id, status, error_message) VALUES (%s, %s, %s, %s);"
    execute_query(query, (broadcast_id, user_id, status, error_msg), commit=True)

def deactivate_user(user_id):
    execute_query("UPDATE users_bot SET is_active = FALSE WHERE id = %s;", (user_id,), commit=True)

# ══════════════════════════════════════════
#              الدوال المساعدة
# ══════════════════════════════════════════

def is_admin(user_id: int) -> bool:
    return str(user_id) == str(ADMIN_ID)

def extract_telegram_id(invite_link):
    # استخراج @username من الرابط للاعتماد عليه كمعرف للقناة في API تليجرام
    if "t.me/" in invite_link:
        return "@" + invite_link.split("t.me/")[1].split("/")[0].replace("+", "")
    return invite_link

def check_subscriptions(user_id: int) -> list:
    if is_admin(user_id):
        return []

    now = time()
    if user_id in verified_cache and (now - verified_cache[user_id] < 240):
        return []

    channels = get_force_channels()
    not_subscribed = []
    VALID_STATUSES = ['member', 'administrator', 'creator']

    conn = get_db_connection()
    cur = conn.cursor()

    for ch in channels:
        telegram_id = extract_telegram_id(ch['invite'])
        try:
            member = bot.get_chat_member(telegram_id, user_id)
            if member.status in VALID_STATUSES:
                cur.execute("""
                    INSERT INTO user_channels (user_id, channel_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, channel_id) DO NOTHING;
                """, (user_id, ch['db_id']))
            else:
                not_subscribed.append(ch)

        except telebot.apihelper.ApiTelegramException as e:
            error_text = e.description.lower()
            if "user not found" in error_text:
                not_subscribed.append(ch)
            else:
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)

    conn.commit()
    cur.close()
    conn.close()

    if not not_subscribed:
        verified_cache[user_id] = now

    return not_subscribed

# ══════════════════════════════════════════
#              لوحات المفاتيح
# ══════════════════════════════════════════

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📚 المكتبة", "🌌 شبكة سديم", "❓ ما هي شبكة سديم؟", 
               "👨‍💻 المطور", "📩 تواصل مع المالك", "🆘 الدعم", "📋 عن سديم", "💻 قنوات لتعلم البرمجة", "📚 قنوات أدبية")
    return markup

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📢 إضافة قناة إجبارية", "🗑 حذف قناة إجبارية", "📋 قائمة القنوات", 
               "📣 إرسال إذاعة", "📊 إحصائيات", "🔙 الرئيسية")
    return markup

def exit_chat_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("❌ إنهاء المحادثة")
    return markup

# قوائم التحقق لمنع التداخل
USER_BUTTONS = ["📚 المكتبة", "🌌 شبكة سديم", "❓ ما هي شبكة سديم؟", "👨‍💻 المطور", "📩 تواصل مع المالك", "🆘 الدعم", "📋 عن سديم", "🔙 الرئيسية", "❌ إلغاء", "💻 قنوات لتعلم البرمجة", "📚 قنوات أدبية"]
ADMIN_BUTTONS = ["📢 إضافة قناة إجبارية", "🗑 حذف قناة إجبارية", "📋 قائمة القنوات", "📣 إرسال إذاعة", "📊 إحصائيات", "🔙 الرئيسية", "❌ إلغاء"]

# ═════════════════════════════════════════
#         المعالجات (Handlers)
# ══════════════════════════════════════════

@bot.message_handler(commands=['start', 'help'])
def start(message):
    user_id = message.from_user.id 
    add_user_bot(message.from_user) 
    
    # تفريغ حالة المستخدم إن وجدت
    user_states.pop(user_id, None)

    missing = check_subscriptions(user_id)
    if missing:
        markup = types.InlineKeyboardMarkup()
        for ch in missing: 
            markup.add(types.InlineKeyboardButton(text=ch['name'], url=ch['invite']))
        markup.add(types.InlineKeyboardButton("✅ تحققت من اشتراكي", callback_data="check_sub"))
        bot.send_message(user_id, "⚠️ للاستمرار، يرجى الاشتراك في القنوات التالية:", reply_markup=markup)
        return

    if is_admin(user_id):
        bot.send_message(user_id, "👑 أهلاً بك في لوحة تحكم سديم", reply_markup=admin_keyboard())
    else:
        bot.send_message(user_id, "🌌 مرحباً بك في عالم سديم الرقمي", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text == "🔙 الرئيسية")
def go_home(message):
    start(message)

@bot.message_handler(func=lambda m: m.text == "❌ إلغاء")
def cancel_action(message):
    user_states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "❌ تم إلغاء العملية الحالية.", 
                     reply_markup=admin_keyboard() if is_admin(message.from_user.id) else main_keyboard())

@bot.message_handler(func=lambda m: m.text == "❌ إنهاء المحادثة")
def exit_chat_action(message):
    user_states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ تم إنهاء جلسة التواصل مع المالك. عودة للقائمة الرئيسية.", reply_markup=main_keyboard())

# 1. معالجات الأدمن
@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text in ADMIN_BUTTONS)
def admin_buttons_handler(message):
    channels = get_force_channels()

    if message.text == "📢 إضافة قناة إجبارية":
        user_states[message.from_user.id] = 'waiting_ch_name'
        bot.send_message(message.chat.id, "📥 أرسل اسم القناة لعرضه في الأزرار:", 
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ إلغاء"))
    
    elif message.text == "📣 إرسال إذاعة":
        user_states[message.from_user.id] = 'waiting_broadcast_msg'
        bot.send_message(message.chat.id, "📥 أرسل الرسالة التي تريد تعميمها على جميع المستخدمين:", 
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ إلغاء"))
    
    elif message.text == "📊 إحصائيات":
        users_count = execute_query("SELECT COUNT(*) FROM users_bot WHERE is_active = TRUE;", fetch=True)[0]
        bot.send_message(message.chat.id, f"📊 الإحصائيات:\n👥 المستخدمين النشطين: {users_count}\n📢 القنوات الإجبارية: {len(channels)}", reply_markup=admin_keyboard())

    elif message.text == "📋 قائمة القنوات":
        if not channels:
            bot.send_message(message.chat.id, "📭 القائمة فارغة حالياً.")
        else:
            text = "📋 القنوات المضافة:\n" + "\n".join([f"- {c['name']} (ID: {c['db_id']})" for c in channels])
            bot.send_message(message.chat.id, text)

    elif message.text == "🗑 حذف قناة إجبارية":
        if not channels:
            bot.send_message(message.chat.id, "📭 لا توجد قنوات لحذفها.")
            return
        markup = types.InlineKeyboardMarkup()
        for ch in channels:
            markup.add(types.InlineKeyboardButton(text=ch['name'], callback_data=f"del_ch_{ch['db_id']}"))
        bot.send_message(message.chat.id, "🗑 اختر القناة التي تريد حذفها:", reply_markup=markup)

# 2. معالجات المستخدم
@bot.message_handler(func=lambda m: not is_admin(m.from_user.id) and m.text in USER_BUTTONS)
def user_buttons_handler(message):
    user_id = message.from_user.id
    
    if message.text == "📩 تواصل مع المالك":
        user_states[user_id] = 'chat_with_owner'
        bot.send_message(user_id, "✍️ أنت الآن في وضع التواصل المباشر. اكتب رسالتك وسيتم إرسالها لصلاح فوراً.\nللخروج اضغط على 'إنهاء المحادثة'.", reply_markup=exit_chat_keyboard())
    
    elif message.text == "🆘 الدعم":
        bot.send_message(user_id, "🆘 الدعم متاح على مدار الساعة!\n📧 البريد: admin@sadim.com\n🤖 بوت الدعم: @SADIM_Sbot")

    elif message.text == "📚 المكتبة":
        books = Library.get_all_books()
        if not books:
            bot.reply_to(message, "⚠️ لا توجد كتب حالياً في المكتبة.")
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for b in books:
            markup.add(types.InlineKeyboardButton(text=f"📖 {b.get('title', 'بدون عنوان')}", callback_data=f"get_book_{b.get('id')}"))
        bot.send_message(user_id, f"📚 المكتبة — لدينا {len(books)} كتاب متاح.\nاختر الرواية التي تود تحميلها:", reply_markup=markup)
    
    elif message.text == "🌌 شبكة سديم":
        bot.send_message(user_id, "🌌 شبكة سديم ليست مجرد منصة، بل نظام رقمي يجمع بين المعرفة، التقنية، والمحتوى الأدبي في مساحة واحدة.\n\n"
"تُبنى على فكرة الربط بين المحتوى والبرمجة، حيث تتكامل القنوات والمكتبة والخدمات الرقمية ضمن هيكل واحد قابل للتوسع.\n\n"
"🔗 الموقع: https://sadim.cloud")

    elif message.text == "❓ ما هي شبكة سديم؟":
        bot.send_message(user_id, "🌌 شبكة سديم تُبنى على فكرة واحدة:\n"
"تحويل المحتوى من منشورات متفرقة إلى نظام رقمي حيّ يتفاعل ويتوسع.\n\n"
"كل قناة، كتاب، وخدمة هي جزء من هيكل أكبر قابل للنمو.:\n🔗 https://sadim.cloud/about")

    elif message.text == "👨‍💻 المطور":
        bot.send_message(user_id, "👨‍💻 المطوّر: صلاح\n\n"
"مطور مستقل يعمل على بناء أنظمة رقمية متكاملة تجمع بين البرمجة، إدارة المحتوى، وأتمتة الخدمات.\n\n"
"يركّز حالياً على تطوير الباك-إند باستخدام Python وPostgreSQL، وبناء أنظمة قابلة للتوسع مثل البوتاتو المواقع و التطبيقات والمنصات الرقمية.\n\n" 
"🔗 الملف الشخصي: https://www.sadim.cloud/admin/profile/view")

    elif message.text in ["📋 عن سديم", "💻 قنوات لتعلم البرمجة", "📚 قنوات أدبية"]:
        # اختصاراً للردود الثابتة
        responses = {
            "📋 عن سديم": "شبكة سديم هي منصة رقمية متكاملة...",
            "💻 قنوات لتعلم البرمجة": "https://t.me/python_1I",
            "📚 قنوات أدبية": "https://t.me/hx5cb"
        }
        bot.send_message(user_id, responses[message.text])

# 3. محرك الرسائل للأدمن (ردود وحالات)
@bot.message_handler(func=lambda m: is_admin(m.from_user.id), content_types=['text', 'photo', 'voice', 'document'])
def admin_catch_all(message):
    state = user_states.get(message.from_user.id)
    
    # حالة إضافة قناة (الخطوة 1: الاسم)
    if state == 'waiting_ch_name':
        user_states[message.from_user.id] = {'step': 'waiting_ch_link', 'name': message.text}
        bot.send_message(message.chat.id, "✅ حسناً، أرسل الآن رابط الدعوة للقناة (يبدأ بـ https://t.me/):")
        return
        
    # حالة إضافة قناة (الخطوة 2: الرابط وحفظ في القاعدة)
    elif isinstance(state, dict) and state.get('step') == 'waiting_ch_link':
        ch_name = state['name']
        invite_link = message.text
        add_channel(ch_name, invite_link)
        user_states.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "🎊 تمت إضافة القناة بنجاح للقاعدة!", reply_markup=admin_keyboard())
        return

    # حالة الإذاعة
    if state == 'waiting_broadcast_msg':
        bot.send_message(message.chat.id, "⏳ جاري إرسال الإذاعة...", reply_markup=admin_keyboard())
        user_states.pop(message.from_user.id, None)
        
        broadcast_id = log_broadcast(message.text)
        users = get_all_users()
        success, failed = 0, 0
        
        for u in users:
            uid = u[0]
            try:
                bot.send_message(uid, message.text)
                log_broadcast_receiver(broadcast_id, uid, 'success')
                success += 1
            except Exception as e:
                log_broadcast_receiver(broadcast_id, uid, 'failed', str(e))
                deactivate_user(uid) # تحويل المستخدم لغير نشط إذا حظر البوت
                failed += 1
                
        update_broadcast_stats(broadcast_id, len(users), success, failed)
        bot.send_message(message.chat.id, f"✅ اكتملت الإذاعة!\nنجاح: {success}\nفشل: {failed}")
        return

    # معالجة الردود المباشرة على المستخدمين
    if message.reply_to_message:
        target_uid = forwarded_msgs.get(message.reply_to_message.message_id)
        if target_uid:
            try:
                if message.content_type == 'text':
                    bot.send_message(target_uid, f"📩 **رد من صلاح:**\n\n{message.text}", parse_mode="Markdown")
                else:
                    bot.copy_message(target_uid, message.chat.id, message.message_id, caption="📩 **رد من صلاح**", parse_mode="Markdown")
                bot.send_message(message.chat.id, "✅ تم إرسال الرد.")
            except:
                bot.send_message(message.chat.id, "❌ فشل الإرسال (ربما قام المستخدم بحظر البوت).")
        else:
            bot.send_message(message.chat.id, "⚠️ لم أتعرف على صاحب هذه الرسالة بالذاكرة المؤقتة.")

# 4. محرك الرسائل للمستخدم (التوجيه)
@bot.message_handler(func=lambda m: not is_admin(m.from_user.id), content_types=['text', 'photo', 'voice', 'document'])
def user_catch_all(message):
    if check_subscriptions(message.from_user.id):
        start(message)
        return

    # التحقق مما إذا كان المستخدم في وضع التواصل مع المالك
    if user_states.get(message.from_user.id) == 'chat_with_owner':
        try:
            sent = bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            forwarded_msgs[sent.message_id] = message.chat.id
            bot.reply_to(message, "🚀 تم الإرسال.")
        except:
            bot.send_message(message.chat.id, "⚠️ حدث خطأ أثناء إرسال رسالتك.")
    else:
        bot.send_message(message.chat.id, "⚠️ عذراً، لا يمكنني معالجة رسالتك. اضغط على 'تواصل مع المالك' إذا كنت تريد إرسال رسالة له.")

# ═════════════════════════════════════════
#         استدعاءات الأزرار (Callbacks)
# ══════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_ch_"))
def handle_delete_channel(call):
    ch_db_id = call.data.replace("del_ch_", "")
    delete_channel(ch_db_id)
    bot.answer_callback_query(call.id, "✅ تم حذف القناة من قاعدة البيانات", show_alert=True)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_verify(call):
    user_id = call.from_user.id 
    verified_cache.pop(user_id, None)
    missing = check_subscriptions(user_id)
    
    if missing:
        bot.answer_callback_query(call.id, "❌ لم تشترك في كافة القنوات بعد!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "✅ شكراً لاشتراكك!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        if is_admin(user_id):
            bot.send_message(user_id, "👑 أهلاً بك في لوحة تحكم سديم", reply_markup=admin_keyboard())
        else:
            bot.send_message(user_id, "🌌 مرحباً بك في عالم سديم الرقمي", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('get_book_'))
def handle_book_sending(call):
    book_id = call.data.replace('get_book_', '')
    book = Library.get_book_id(book_id) 
    
    if not book:
        bot.answer_callback_query(call.id, "❌ عذراً، لم يتم العثور على بيانات الكتاب.")
        return

    bot.answer_callback_query(call.id, "⏳ جاري تجهيز الملف...")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    
    title = book.get('title', 'بدون عنوان')
    pdf_path = os.path.join(UPLOAD_FOLDER, book.get('pdf_path', ''))
    cover_path = os.path.join(UPLOAD_FOLDER, book.get('cover_path', ''))
    user_id = call.from_user.id

    if os.path.exists(cover_path):
        with open(cover_path, 'rb') as cover:
            bot.send_photo(user_id, cover, caption=f"📖 {title}")

    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as pdf:
            bot.send_document(user_id, pdf)
    else:
        bot.send_message(user_id, f"❌ عذراً، ملف الـ PDF غير متوفر حالياً.")

if __name__ == "__main__":
    print("--- SADIM NETWORK SYSTEM ONLINE ---")
    bot.infinity_polling(skip_pending=True)