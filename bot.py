import telebot
from telebot import types
from config import BOT_TOKEN
from db_handler import init_db, log_day, get_weekly_stats, get_monthly_stats, get_insights, clear_user_data
from analyzer import generate_weekly_chart, generate_insight_text
import os

bot = telebot.TeleBot(BOT_TOKEN)


user_state = {}


main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_add = types.KeyboardButton("➕ Записать день")
btn_stats = types.KeyboardButton("📊 Статистика")
btn_help = types.KeyboardButton("❓ Помощь")
btn_history = types.KeyboardButton("📜 История")
btn_settings = types.KeyboardButton("⚙️ Настройки")
btn_clear = types.KeyboardButton(" Очистить данные")

main_keyboard.add(btn_add, btn_stats)
main_keyboard.add(btn_help, btn_history)
main_keyboard.add(btn_settings, btn_clear)


def get_mood_keyboard():
    mood_keyboard = types.InlineKeyboardMarkup()
    for i in range(1, 6):
        emoji = ["😞", "😐", "🙂", "😊", "🤩"][i-1]
        mood_keyboard.add(types.InlineKeyboardButton(text=f"{i} {emoji}", callback_data=f"mood_{i}"))
    return mood_keyboard


def get_hours_keyboard():
    hours_keyboard = types.InlineKeyboardMarkup()
    for h in [0.5, 1, 2, 4]:
        hours_keyboard.add(types.InlineKeyboardButton(text=f"{h} ч", callback_data=f"hours_{h}"))
    hours_keyboard.add(types.InlineKeyboardButton(text="Другое...", callback_data="hours_other"))
    return hours_keyboard


stats_keyboard = types.InlineKeyboardMarkup()
stats_keyboard.add(types.InlineKeyboardButton("📅 За неделю", callback_data="stats_week"))
stats_keyboard.add(types.InlineKeyboardButton("📅 За месяц", callback_data="stats_month"))
stats_keyboard.add(types.InlineKeyboardButton("🔍 Мои инсайты", callback_data="stats_insights"))
stats_keyboard.add(types.InlineKeyboardButton("📉 График", callback_data="stats_graph"))


init_db()



def send_main_menu(chat_id, text="Выберите действие:"):
    bot.send_message(chat_id, text, reply_markup=main_keyboard)



@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, """
👋 Добро пожаловать в Mood Tracker Bot!

Этот бот поможет вам отслеживать:
• Настроение (1–5)
• Часы работы/учебы
• Часы сна
• Комментарии

Нажмите «➕ Записать день», чтобы начать!
""", reply_markup=main_keyboard)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, """
📋 Команды:

/start — Приветствие
/add — Записать день
/stats — Статистика
/history — История записей
/settings — Настройки
/clear — Очистить все данные
/help — Эта справка
""", reply_markup=main_keyboard)


@bot.message_handler(func=lambda message: message.text == "➕ Записать день")
def cmd_add_button(message):
    start_add_flow(message)

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def cmd_stats_button(message):
    show_stats_menu(message)

@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def cmd_help_button(message):
    send_help(message)

@bot.message_handler(func=lambda message: message.text == " История")
def cmd_history_button(message):
    show_history(message)

@bot.message_handler(func=lambda message: message.text == "️ Настройки")
def cmd_settings_button(message):
    settings(message)

@bot.message_handler(func=lambda message: message.text == "🗑 Очистить данные")
def cmd_clear_button(message):
    confirm_clear(message)

@bot.message_handler(commands=['add'])
def start_add_flow(message):
    user_state[message.chat.id] = {'step': 'mood'}
   
    bot.send_message(message.chat.id, "Оцени свое настроение сегодня от 1 до 5:", reply_markup=get_mood_keyboard())



@bot.callback_query_handler(func=lambda call: call.data.startswith('mood_'))
def handle_mood(call):
    chat_id = call.message.chat.id
    mood = int(call.data.split('_')[1])
    
   
    user_state[chat_id] = {'step': 'work_hours', 'mood': mood}
    
   
    bot.send_message(chat_id, "Сколько часов ты потратил на полезную работу/учебу?", reply_markup=get_hours_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith('hours_') and user_state.get(call.message.chat.id, {}).get('step') == 'work_hours')
def handle_work_hours(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == 'hours_other':
        user_state[chat_id]['step'] = 'work_hours_input'
        bot.send_message(chat_id, "Введите количество часов работы (числом, например: 3.5)")
    else:
        work_hours = float(data.split('_')[1])
        user_state[chat_id]['work_hours'] = work_hours
        user_state[chat_id]['step'] = 'sleep_hours'
        
        bot.send_message(chat_id, "Сколько часов ты спал?", reply_markup=get_hours_keyboard())

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'work_hours_input')
def handle_work_hours_input(message):
    try:
        work_hours = float(message.text)
        user_state[message.chat.id]['work_hours'] = work_hours
        user_state[message.chat.id]['step'] = 'sleep_hours'
        bot.send_message(message.chat.id, "Сколько часов ты спал?", reply_markup=get_hours_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число (например: 7.5)")

@bot.callback_query_handler(func=lambda call: call.data.startswith('hours_') and user_state.get(call.message.chat.id, {}).get('step') == 'sleep_hours')
def handle_sleep_hours(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == 'hours_other':
        user_state[chat_id]['step'] = 'sleep_hours_input'
        bot.send_message(chat_id, "Введите количество часов сна (числом, например: 8.0)")
    else:
        sleep_hours = float(data.split('_')[1])
        user_state[chat_id]['sleep_hours'] = sleep_hours
        user_state[chat_id]['step'] = 'comment'
       
        skip_kb = types.InlineKeyboardMarkup()
        skip_kb.add(types.InlineKeyboardButton("Пропустить", callback_data="skip_comment"))
        
        bot.send_message(chat_id, "Хочешь добавить комментарий? (Напиши текст или нажми кнопку ниже)", reply_markup=skip_kb)

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'sleep_hours_input')
def handle_sleep_hours_input(message):
    try:
        sleep_hours = float(message.text)
        user_state[message.chat.id]['sleep_hours'] = sleep_hours
        user_state[message.chat.id]['step'] = 'comment'
        
        skip_kb = types.InlineKeyboardMarkup()
        skip_kb.add(types.InlineKeyboardButton("Пропустить", callback_data="skip_comment"))
        
        bot.send_message(message.chat.id, "Хочешь добавить комментарий? (Напиши текст или нажми кнопку ниже)", reply_markup=skip_kb)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число (например: 7.5)")

@bot.callback_query_handler(func=lambda call: call.data == 'skip_comment')
def handle_skip_comment(call):
    chat_id = call.message.chat.id
    user_state[chat_id]['comment'] = ''
    save_log(chat_id)

@bot.message_handler(func=lambda message: message.chat.id in user_state and user_state[message.chat.id].get('step') == 'comment')
def handle_comment(message):
    chat_id = message.chat.id
    user_state[chat_id]['comment'] = message.text
    save_log(chat_id)

def save_log(chat_id):
    data = user_state[chat_id]
    success = log_day(
        telegram_id=chat_id,
        mood=data['mood'],
        work_hours=data['work_hours'],
        sleep_hours=data['sleep_hours'],
        comment=data.get('comment', '')
    )
    
    if success:
        bot.send_message(chat_id, "✅ Данные успешно сохранены!", reply_markup=main_keyboard)
    else:
        bot.send_message(chat_id, " Произошла ошибка при сохранении.", reply_markup=main_keyboard)
    
    if chat_id in user_state:
        del user_state[chat_id]



@bot.message_handler(commands=['stats'])
def show_stats_menu(message):
    bot.send_message(message.chat.id, "Что хочешь узнать?", reply_markup=stats_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('stats_'))
def handle_stats(call):
    chat_id = call.message.chat.id
    action = call.data.split('_')[1]
    

    bot.answer_callback_query(call.id)
    
    if action == 'week':
        df = get_weekly_stats(chat_id)
        if df.empty:
            bot.send_message(chat_id, "Нет данных за неделю.")
            return
        
        summary = f"📊 Статистика за неделю:\n\n"
        summary += f"Среднее настроение: {df['mood'].mean():.1f}\n"
        summary += f"Средние часы работы: {df['work_hours'].mean():.1f}\n"
        summary += f"Средние часы сна: {df['sleep_hours'].mean():.1f}\n"
        summary += f"Записей: {len(df)}"
        
        bot.send_message(chat_id, summary, reply_markup=main_keyboard)
        
    elif action == 'month':
        df = get_monthly_stats(chat_id)
        if df.empty:
            bot.send_message(chat_id, "Нет данных за месяц.")
            return
        
        summary = f"📅 Статистика за месяц:\n\n"
        summary += f"Среднее настроение: {df['mood'].mean():.1f}\n"
        summary += f"Средние часы работы: {df['work_hours'].mean():.1f}\n"
        summary += f"Средние часы сна: {df['sleep_hours'].mean():.1f}\n"
        summary += f"Записей: {len(df)}"
        
        bot.send_message(chat_id, summary, reply_markup=main_keyboard)
        
    elif action == 'insights':
        insight = generate_insight_text(chat_id)
        bot.send_message(chat_id, insight, reply_markup=main_keyboard)
        
    elif action == 'graph':
        chart_path = generate_weekly_chart(chat_id)
        if chart_path and os.path.exists(chart_path):
            with open(chart_path, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption="📈 График за неделю", reply_markup=main_keyboard)
            os.remove(chart_path)
        else:
            bot.send_message(chat_id, "Не удалось создать график. Возможно, нет данных.", reply_markup=main_keyboard)



@bot.message_handler(commands=['history'])
def show_history(message):
    chat_id = message.chat.id

    df = get_weekly_stats(chat_id)  
    if df.empty:
        bot.send_message(chat_id, "У вас пока нет записей.", reply_markup=main_keyboard)
        return
    
    history_text = "📜 Последние записи (за неделю):\n\n"
   
    for _, row in df.tail(5).iterrows():
        date_str = row['date'].strftime('%d.%m') if hasattr(row['date'], 'strftime') else row['date']
        history_text += f"📅 {date_str}: Настр={row['mood']}, Раб={row['work_hours']}ч, Сон={row['sleep_hours']}ч\n"
        if row['comment']:
            history_text += f"   💬 {row['comment']}\n"
        history_text += "\n"
    
    bot.send_message(chat_id, history_text, reply_markup=main_keyboard)



@bot.message_handler(commands=['clear'])
def confirm_clear(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✅ Да, очистить", callback_data="confirm_clear"))
    keyboard.add(types.InlineKeyboardButton("❌ Нет, отмена", callback_data="cancel_clear"))
    bot.send_message(message.chat.id, "⚠️ Вы уверены, что хотите удалить ВСЕ свои данные? Это действие необратимо!", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_clear')
def handle_confirm_clear(call):
    chat_id = call.message.chat.id
    clear_user_data(chat_id)
    bot.answer_callback_query(call.id, "Данные удалены.")
    bot.send_message(chat_id, "🗑 Все ваши данные были удалены.", reply_markup=main_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_clear')
def handle_cancel_clear(call):
    bot.answer_callback_query(call.id, "Операция отменена.")
    bot.send_message(call.message.chat.id, "Отлично, данные остались в безопасности 😊", reply_markup=main_keyboard)



@bot.message_handler(commands=['settings'])
def settings(message):
    bot.send_message(message.chat.id, "⚙️ Настройки пока не реализованы. Скоро будет!", reply_markup=main_keyboard)

if __name__ == '__main__':
    print(" Бот запущен...")
    bot.infinity_polling()