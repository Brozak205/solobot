from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio

# Критерии для оценивания (с заменой [Имя] на имя из контекста)
criteria_template = [
    "🔴 Оцени вайб {name}\n(Как ты себя чувствуешь ДО, ВО ВРЕМЯ и ПОСЛЕ общения? Отдых или нагрузка? Оцени эти ощущения от 1 до 10)",
    
    "🔴 Насколько вы близки?\n(Попросишь принести бумагу в общественном туалете? Или поймёшь без слов, когда нужно место освободить?)",
    
    "🔴 Оцени живое общение с {name}\n(Если виделись — насколько встречи были естественными и комфортными? Если не виделись — это 1 из 10)",
    
    "🔴 Оцени интеллект {name}\n(Как тебе кажется — человек способен мыслить глубже, чем «погода», «работа» или «тупая мемасина»? Не факт, что он(а) умнее Эйнштейна — а твой личный уровень восприятия)",
    
    "🔴 Видишь ли ты будущее с этим человеком?\n(Любое: дружба, любовь, соседство, работа — если есть картинка, оцени её. Если нет — это 1 из 10)",
    
    "🔴 Оцени внешность и сексуальность {name}\n(Объективно, как произведение искусства. Как бы ты оценил красоту этого человека, если бы он(а) был(а) просто объектом?)",
    
    "🔴 Насколько кинематографична ваша история?\n(Как вы встретились, как общаетесь — всё ли это похоже на кино или просто случайное совпадение двух страничек в контакте?)",
    
    "🔴 Оцени эмоциональную зрелость {name}\n(Умеет ли он(а) чувствовать, но не истерить? Реагировать, но не закапывать эмоции? Управлять собой?)",
    
    "🔴 Насколько ваши ценности совпадают?\n(Если для тебя важны семья, развитие, честность — а для него(неё) вечные вечеринки и игнор ответственности — задумайся)",
    
    "🔴 Оцени надёжность {name}\n(Готов(а) ли держать слово даже когда сложно? Если сказал — сделал. Или «забыл из принципа»?)",
    
    "🔴 Какова социальность {name}?\n(Экстраверт или интроверт? Быстро находит контакт или сразу теряет интерес? Это зависит от тебя — выбери то, что важно именно тебе)",
    
    "🔴 Насколько {name} поддерживает тебя?\n(Готов(а) быть рядом, слушать, помогать, когда тебе плохо? Или исчезает в самый нужный момент?)",
    
    "🔴 Оцени харизму {name}\n(Когда говорит — хочется слушать? Или все уже достали телефон и притворились занятыми?)",
    
    "🔴 Насколько честен(а) {name}?\n(Ты чувствуешь, что реальность приукрашивается, или можно верить каждому слову?)",
    
    "🔴 Оцени онлайн-взаимодействие с {name}\n(Как быстро он(а) читает и отвечает? Участливый диалог или полный игнор? Онлайн-поведение тоже многое скажет)"
]

# Текст вступления
INTRO_TEXT = """\
✨ Товарищ!

В наше время сложно понять: перед тобой — настоящий партнёр или просто ред-флаг?

Этот опросник разработан  
по методике ЦКЧО  
(Центральная Комиссия  
Человеческих Оценок)  
по заказу Министерства  
Социальных Взаимодействий.

Баллы от 1 до 10. Можно дробные значения: 5.7, 8.3 и так далее.  
Арифметика за тебя не решает — только интуиция.

Используй на свой страх и риск.  
Мы за последствия не отвечаем, ты сам(-а) себе психолог.

Продолжая, ты подтверждаешь:  
— тебе есть 18+  
— ты осознан  
— ты несёшь ответственность за свои взаимоотношения с людьми  

Введите имя товарища, прозвище...
"""

# Вердикт по категориям
def get_verdict(score):
    if score >= 8.5:
        return """\
🏆 Категория "Сигма уровня S"  
Этот человек — событие. Как «Москвич» на фоне Запорожца.  
Как джаз в застойную эпоху. Притягивает взгляды, вызывает доверие, умеет слушать и держать слово.  
Если такой рядом — ты в выигрыше."""
    elif score >= 7.5:
        return """\
🤝 Второй эшелон  
Не герой, но уже не шелуха. Хороший товарищ, надёжный партнёр, можно доверить дело.  
Перемен не жди. На вопрос: «Почему он такой?» — ответ всегда один: «Нравится ему так». """
    elif score >= 6.5:
        return """\
🛠 Уровень корректировки  
Человек неплох, но есть моменты. Может быть легкая несерьёзность, хамство, несоответствие ценностей.  
Работай над отношениями — если это реально нужно. А может, и не нужно."""
    elif score >= 5.5:
        return """\
⚠️ Полоса препятствий  
Задумываешься: а зачем он(а) мне нужен(а)?  
Если причины веские — попробуй разобраться.  
Если их нет — проще сказать «привет» и уйти без шума."""
    else:
        return """\
🚫 Отметка "Не наш пассажир"  
Он(а) тебе не особо нравится. Ты на него(её) обижен(а).  
Он(а) странный(ая), или просто вы несовместимы.  
Возможно, со временем что-то изменится... Но скорее всего — нет.  
Лучше отпустить и забыть."""

# Формируем развёрнутую статистику
def get_detailed_report(name, ratings):
    report = f"🔖 Отчёт по классификации ЦК для {name}:\n\n"
    for i, rating in enumerate(ratings):
        report += f"{i+1}. {criteria_template[i].format(name=name)}\nОценка: {rating}/10\n\n"
    return report.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INTRO_TEXT)
    context.user_data['step'] = 'name'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().lower()
    step = context.user_data.get('step')

    if step == 'name':
        name = user_input
        context.user_data['name'] = name
        context.user_data['ratings'] = []
        context.user_data['step'] = 'rating'
        context.user_data['current_index'] = 0
        await ask_question(update, context)

    elif step == 'rating':
        try:
            rating = float(user_input)
            if not (1 <= rating <= 10):
                raise ValueError
            context.user_data['ratings'].append(rating)
            next_index = context.user_data['current_index'] + 1

            if next_index < len(criteria_template):
                context.user_data['current_index'] = next_index
                await ask_question(update, context)
            else:
                name = context.user_data['name']
                ratings = context.user_data['ratings']
                average = sum(ratings) / len(ratings)

                verdict = get_verdict(average)

                await update.message.reply_text(f"✨ {name} набирает: {average:.2f} из 10 возможных.")
                await update.message.reply_text(verdict)
                await update.message.reply_text("Хочешь узнать подробнее? Напиши 'да'.")

                context.user_data.update({
                    'step': 'details',
                    'average': average,
                })

        except:
            await update.message.reply_text("Неправильный формат оценки. Введи число от 1 до 10 (например: 7.5).")

    elif step == 'details':
        if user_input == 'да':
            name = context.user_data['name']
            ratings = context.user_data['ratings']
            detailed_report = get_detailed_report(name, ratings)
            for chunk in [detailed_report[i:i+4096] for i in range(0, len(detailed_report), 4096)]:
                await update.message.reply_text(chunk)
            await update.message.reply_text("Хочешь начать заново? Напиши '/start'.")
        else:
            await update.message.reply_text("Хорошо! Спасибо, что воспользовался(-ась) ботом 😊")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['current_index']
    name = context.user_data['name']
    question = criteria_template[index].format(name=name)
    await update.message.reply_text(question)

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    import os
app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен... Жду команды /start в Telegram.")

    app.run_polling()

if __name__ == '__main__': 
    main() 
