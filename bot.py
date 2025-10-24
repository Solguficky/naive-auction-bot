import os
import sys
import signal
import asyncio
import logging
from typing import Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext
)

import database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CREATOR_ID = int(os.getenv("CREATOR_ID", "1337"))

if not TG_BOT_TOKEN:
    logger.error("TG_BOT_TOKEN environment variable is required")
    sys.exit(1)

auction_lots = {
    1: {
        'title': 'Значок "Собака"',
        'description': 'Существуют ли пчелы, или это всё гуфеня в костюме. Срисован с арта нашего любимого Пети. С двойным креплением.\n '
        'Автор - Нян',
        'min_bid_step': 50.0,
        'starting_price': 100.0,
        'image_url': 'https://imgur.com/a/PHuRNJw'
    },
    2: {
        'title': 'Кашпо "Cash_po"',
        'description': 'Мистер всратыш, который притворяется кашпо. К передаче владельцу будет обшкурен, очищен и покрашен \n\n'
        'Материал — гипс \n'
        'Диаметр дырки ~7см \n '
        'Высота от внутренней ступеньки до верха ~5см \n\n'
        'Сам кашпо: \n'
        'Диаметр 14,5 см \n'
        'Макс. высота 12 см \n\n'
        'Подойдёт для мелких цветочков, кактусов там, суккулентов. Ну или побольше, иф ю брейв энаф и пофиг на торчащий горшок (при желании можно будет покрасить горшок в цвет и как будто так и надо)\n\n'
        'Еще можно как органайзер использовать, почему бы и нет. \n'
        'P.S. Цветочек с фото в примере вместе с кашпо не отдается \n'
        'Автор - Петя',
        'min_bid_step': 100.0,
        'starting_price': 500.0,
        'image_url': 'https://imgur.com/a/YB0awqD'
    },
    3: {
        'title': 'Футболка "Шесть обличий Алекса Гуфовского"',
        'description': 'Стример, представленный в своих разных амплуа. Кто заметил пасхалку - молодец.\n\n'
        'Данный лот представляет собой возможность использовать экслюзивно отрисованный принт для футболки.\n'
        'С выигравшим лот мы согласуем размер и цвет футболки. По завершению - отдаю готовое изделие.\n'
        'Автор - Nato',
        'min_bid_step': 69.0,
        'starting_price': 1000.0,
        'image_url': 'https://imgur.com/a/YS75ov9'
    },
    4: {
        'title': 'Значок "Хрю"',
        'description': 'ХРЮКНИ. Нейросеть не может, а значок может. С двойным креплением.\n'
        'Автор - Нян',
        'min_bid_step': 50.0,
        'starting_price': 100.0,
        'image_url': 'https://imgur.com/a/Mifg2Cr'
    },
    5: {
        'title': 'Значок "Портал"',
        'description': 'ДЛЯ ТЕБЯ И ДЛЯ НЕЁ/НЕГО. Или только для тебя. Ну портал типа \n'
        'Автор - Нян',
        'min_bid_step': 50.0,
        'starting_price': 100.0,
        'image_url': 'https://imgur.com/a/YKLNNEw'
    },
    6: {
        'title': 'Значок "Пицца"',
        'description': 'ПИЦЦА ПЕППЕРОНИ \n'
        'Автор - Нян',
        'min_bid_step': 50.0,
        'starting_price': 100.0,
        'image_url': 'https://imgur.com/a/tuQc6eK'
    },
    7: {
        'title': 'Псевдо(?)фильм SHODKA',
        'description': 'Короткометражка, из которой можно узнать как проходит подготовка ко сходке, как делаются постеры для анонсов и прочее закульсие.\n'
        'Дабы не спойлерить - покажу только фанпостер к фильму (автор фанпостера -Петя), а также тизер-картинку, который может подтолкнуть к мыслям о содержании данного фильма\n'
        'Выигравший лот получает цифровую копию данного фильма \n'
        'Автор - Nato et al.',
        'min_bid_step': 42.0,
        'starting_price': 666.0,
        'image_url': 'https://imgur.com/a/SA71XIm'
    },
    8: {
        'title': 'Значок "Клоун"',
        'description': 'Обычный вид контент-мейкера, не только на празднике срисованный с работы Нато. С двойным креплением.\n'
        'Автор - Нян',
        'min_bid_step': 50.0,
        'starting_price': 100.0,
        'image_url': 'https://imgur.com/a/U4WdFYF'
    },
    9: {
        'title': 'Фигурка "Gufoffsky na trone *LIMITED*"',
        'description': 'Высота: 13см \n'
        'Покрашена вручную \n'
        'Присутствуют интерактивные элементы \n'
        'Комплект: \n'
        '1. Статуэтка из Photopolymer resin \n'
        '2. Accessories необходимые для проведения streams \n'
        '3. Сертификат of Authenticity \n'
        '4. Подарочный box \n'
        'Автор - Пугало',
        'min_bid_step': 50.0,
        'starting_price': 500.0,
        'image_url': 'https://imgur.com/a/gavAKem'
    },
    10: {
        'title': 'Значок "Пятнистое парнокопытное"',
        'description': 'НУ ТИПА ПОЛЬСКАЯ КОРОВА ОК?? С двойным креплением.\n'
        'Автор - Нян',
        'min_bid_step': 50.0,
        'starting_price': 100.0,
        'image_url': 'https://imgur.com/a/ShVgfrC'
    },
    11: {
        'title': 'Значок "Бумажный самолетик"',
        'description': 'Абсолютно точно не спиздел идею с мерча Нежности на бумаге, убрав сердечко... (прямая цитата автора) С двойным креплением. \n'
        'Автор - Нян',
        'min_bid_step': 50.0,
        'starting_price': 100.0,
        'image_url': 'https://imgur.com/a/qWcYncb'
    },
    12: {
        'title': 'Икона "Явление стрима народу"',
        'description': 'Фоторамка с изображением лика святого, которое, как считается, заряжено на стрим. \n'
        'Если дополнительно помолиться на данное изображение, будучи подписанным на бусти, шанс стрима увеличивается. \n'
        'Выполнено вручную с использованием мифического материала "Медная фольга". \n'
        'Автор - Nato',
        'min_bid_step': 40.0,
        'starting_price': 420.0,
        'image_url': 'https://imgur.com/a/G7g3cMM'
    },
}

welcome_message = "Привет. Напиши что угодно в чат для получения информации что тут вообще происходит или сразу тыкай кнопки, если знаешь что делать"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("Показать лоты")],
        [KeyboardButton("Показать свои ставки")],
        [KeyboardButton("📋 Информация об аукционе")],
        [KeyboardButton("ℹ️ О боте")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    context.user_data['first_message'] = True
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def handle_back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    keyboard = [
        [KeyboardButton("Показать лоты")],
        [KeyboardButton("Показать свои ставки")],
        [KeyboardButton("📋 Информация об аукционе")],
        [KeyboardButton("ℹ️ О боте")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.callback_query.message.reply_text(welcome_message, reply_markup=reply_markup)

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Да, объяснить", callback_data="auction_info")],
        [InlineKeyboardButton("Нет, не надо", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Либо что-то пошло не так, либо ты тут впервые. Объяснить как работает бот?",
        reply_markup=reply_markup
    )

async def show_user_bids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_bids = {}

    for lot_id, lot_info in auction_lots.items():
        max_bid = await database.get_current_max_bid(lot_id)

        if max_bid:
            lot_bids = await database.get_lot_bids(lot_id)
            user_bid = max((bid for bid in lot_bids if bid['user_id'] == user.id),
                          key=lambda x: x['amount'], default=None)

            if user_bid:
                user_bids[lot_id] = {
                    'title': lot_info['title'],
                    'current_bid': max_bid['amount'],
                    'current_bidder_id': max_bid['user_id']
                }

    if user_bids:
        message_lines = []
        for lot_id, bid_info in user_bids.items():
            current_bid = bid_info['current_bid']
            current_bidder_id = bid_info['current_bidder_id']

            try:
                current_bid_user_name = (await context.bot.get_chat(current_bidder_id)).first_name
            except Exception:
                current_bid_user_name = "Неизвестный"

            message_lines.append(
                f"Лот {lot_id}: '{bid_info['title']}' - Текущая максимальная ставка: {current_bid} рублей от {current_bid_user_name}.\n"
            )

        await update.message.reply_text("\n".join(message_lines))

        buttons = [
            [InlineKeyboardButton("Назад", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("У вас пока нет ставок.")

async def delete_bid(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if user.id != CREATOR_ID:
        logger.warning(f'Попытка несанкционированного удаления ставки пользователем ID {user.id}.')
        await update.message.reply_text('У вас нет прав на удаление ставок. Рапорт уже составлен')
        return

    if len(context.args) != 1:
        await update.message.reply_text("Пожалуйста, укажите ID ставки для удаления.")
        context.user_data['awaiting_bid_id'] = True


async def notify_outbid_users(lot_id: int, previous_max_bid: Optional[Dict], new_max_bid_amount: float, new_bidder_id: int, context: ContextTypes.DEFAULT_TYPE):
    lot = auction_lots[lot_id]

    if previous_max_bid and previous_max_bid['user_id']:
        user_id = previous_max_bid['user_id']
        
        if user_id == new_bidder_id:
            return
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❗ Ваша ставка в {previous_max_bid['amount']} рублей на лот '{lot['title']}' была перебита. "
                     f"Текущая максимальная ставка теперь составляет {new_max_bid_amount} рублей."
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

async def show_lots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lot_buttons = []
    for lot_id, lot_info in auction_lots.items():
        lot_buttons.append([InlineKeyboardButton(f'Лот {lot_id}: {lot_info["title"]}', callback_data=f'view_{lot_id}')])

    reply_markup = InlineKeyboardMarkup(lot_buttons)
    await update.message.reply_text('Доступные лоты:', reply_markup=reply_markup)

async def handle_show_lots_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_lots(update, context)

async def lot_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lot_id = int(query.data.split('_')[1])
    lot = auction_lots[lot_id]

    max_bid = await database.get_current_max_bid(lot_id)
    current_bid = max_bid['amount'] if max_bid else None

    starting_price = lot['starting_price']
    min_bid_step = lot['min_bid_step']

    buttons = []

    if current_bid is None:
        buttons.append([InlineKeyboardButton("Посмотреть описание", callback_data=f'description_{lot_id}')])
        buttons.append([InlineKeyboardButton(f"Начать торги за {starting_price} рублей", callback_data=f'bid_start_{lot_id}')])
    else:
        new_bid = current_bid + min_bid_step
        buttons.append([InlineKeyboardButton("Посмотреть описание", callback_data=f'description_{lot_id}')])
        buttons.append([InlineKeyboardButton(f"Повысить на {min_bid_step} рублей (новая ставка: {new_bid} рублей)", callback_data=f'bid_increase_{lot_id}')])
        buttons.append([InlineKeyboardButton(f"Индивидуальная ставка (>{min_bid_step})", callback_data=f'set_bid_{lot_id}')])

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        text=f"Лот: {lot['title']}\n"
             f"Текущая ставка: {current_bid if current_bid else 'Нет ставок'}\n"
             "Выберите действие:",
        reply_markup=reply_markup
    )

async def go_to_lots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await show_lots(update, context)

async def start_bid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lot_id = int(query.data.split('_')[2])
    starting_price = auction_lots[lot_id]['starting_price']

    bid_id = await database.save_bid(lot_id, query.from_user.id, starting_price)

    await query.edit_message_text(
        text=f"✅ Торги начались для '{auction_lots[lot_id]['title']}'. Спасибо!\n"
             f"Текущая ставка: {starting_price} рублей.\n"
             "Используйте кнопку Показать лоты, чтобы посмотреть этот или другие лоты"
    )

async def bid_increase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lot_id = int(query.data.split('_')[2])
    lot = auction_lots[lot_id]

    previous_max_bid = await database.get_current_max_bid(lot_id)
    current_bid = previous_max_bid['amount'] if previous_max_bid else lot['starting_price']

    new_bid = current_bid + lot['min_bid_step']

    bid_id = await database.save_bid(lot_id, query.from_user.id, new_bid)

    await notify_outbid_users(lot_id, previous_max_bid, new_bid, query.from_user.id, context)

    await query.edit_message_text(
        text=f"✅ Ставка в {new_bid} рублей была поднята для '{lot['title']}'. Ваш ID ставки: {bid_id}. Спасибо!\n\n"
             "Используйте кнопку Показать лоты, чтобы посмотреть этот или другие лоты."
    )

async def list_lots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    if user.id != CREATOR_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    message_lines = []

    for lot_id, lot_info in auction_lots.items():
        message_lines.append(f"Лот ID: {lot_id} - Название: '{lot_info['title']}'")

    if message_lines:
        await update.message.reply_text("Доступные лоты:\n" + "\n".join(message_lines))
    else:
        await update.message.reply_text("На данный момент лотов нет.")

async def set_individual_bid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lot_id = int(query.data.split('_')[2])
    context.user_data["current_lot"] = lot_id

    max_bid = await database.get_current_max_bid(lot_id)
    current_bid = max_bid['amount'] if max_bid else None

    buttons = [
        [InlineKeyboardButton("Назад", callback_data=f'view_{lot_id}')],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        text=f"Введите вашу индивидуальную ставку для '{auction_lots[lot_id]['title']}'.\n"
             f"Текущая ставка: {current_bid if current_bid else 'Нет ставок'} рублей.\n"
             "Ваша ставка должна быть больше текущей.",
        reply_markup=reply_markup
    )

async def process_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'awaiting_bid_id' in context.user_data and context.user_data['awaiting_bid_id']:
        bid_id_str = update.message.text.strip()
        try:
            bid_id = int(bid_id_str)
            await update.message.reply_text(f"Функция удаления ставок в данной версии не реализована. ID: {bid_id}")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное число для ID ставки.")
        context.user_data['awaiting_bid_id'] = False
        return

    user = update.effective_user
    message = update.message.text
    lot_id = context.user_data.get("current_lot")

    try:
        bid_amount = float(message)

        if not lot_id:
            await update.message.reply_text("Пожалуйста, сначала выберите лот, используя кнопку 'Показать лоты'.")
            return

        lot = auction_lots[lot_id]

        previous_max_bid = await database.get_current_max_bid(lot_id)
        current_bid = previous_max_bid['amount'] if previous_max_bid else None

        if current_bid is not None:
            min_required_bid = current_bid + lot['min_bid_step']
            if bid_amount < min_required_bid:
                await update.message.reply_text(
                    f"Ваша ставка должна быть минимум {min_required_bid} рублей "
                    f"(текущая ставка {current_bid} + минимальный шаг {lot['min_bid_step']})."
                )
                return

        bid_id = await database.save_bid(lot_id, user.id, bid_amount)

        if current_bid is None or bid_amount > current_bid:
            await notify_outbid_users(lot_id, previous_max_bid, bid_amount, user.id, context)

        await update.message.reply_text(
            f"✅ Ставка в {bid_amount} рублей была сделана для '{lot['title']}'. Ваш ID ставки: {bid_id}. Спасибо!\n\n"
            "Используйте кнопку Показать лоты, чтобы посмотреть этот или другие лоты."
        )

    except ValueError:
        await handle_unknown_message(update, context)

async def show_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lot_id = int(query.data.split('_')[1])
    lot = auction_lots[lot_id]

    image_url = lot['image_url']
    if not image_url.startswith("http"):
        await query.message.reply_text("Ошибка: Неверный URL изображения.")
        return

    max_bid = await database.get_current_max_bid(lot_id)
    current_bid = max_bid['amount'] if max_bid else None

    try:
        await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=image_url,
            caption=(
                f"Описание лота '{lot['title']}':\n"
                f"{lot['description']}\n\n"
                f"Текущая ставка: {current_bid if current_bid else 'Нет ставок'}"
            )
        )
    except Exception as e:
        await query.message.reply_text(f"Ошибка при отправке изображения: {str(e)}")

    buttons = []
    starting_price = lot['starting_price']

    if current_bid is None:
        buttons.append([InlineKeyboardButton(f"Начать торги за {starting_price} рублей", callback_data=f'bid_start_{lot_id}')])
    else:
        min_bid_step = lot['min_bid_step']
        new_bid = current_bid + min_bid_step
        buttons.append([
            InlineKeyboardButton(f"Повысить на {min_bid_step} рублей (новая ставка: {new_bid} рублей)", callback_data=f'bid_increase_{lot_id}')
        ])
        buttons.append([InlineKeyboardButton(f"Индивидуальная ставка (>{min_bid_step})", callback_data=f'set_bid_{lot_id}')])

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.message.reply_text(
        text="Выберите действие:",
        reply_markup=reply_markup
    )

async def auction_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        message = update.message

    buttons = [
        [InlineKeyboardButton("Задать вопрос", url="https://t.me/Neptunini")],
        [InlineKeyboardButton("Назад", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await message.reply_text(
        "Добро пожаловать на солевой аукцион. Все операции на аукционе осуществляются через данного бота:\n\n"
        "Информация о том, как работать с ботом:\n\n"
        "Через кнопки можно вызвать список лотов (Показать лоты) или посмотреть на какие лоты вы уже сделали ставки (Показать свои ставки), чтобы посмотреть держите ли вы максимальную ставку по своему лоту. В списке лотов при выборе конкретного лота вы можете: посмотреть его описание, и сделать ставку (если вы первый, то она = стартовой цене; при наличии других ставок вы можете либо повысить ставку на минимальный шаг, либо сделать индивидуальную ставку -  указать любую другую сумму ставки, превышающую минимальный шаг)\n\n"
        "Аукцион продлится с 18:10 6/04 по 20:00 12/04 (время по СПБ). Все ставки принимаются в рублях. Выигравшей считается последняя принятая ставка (последний час торгов проходит в гибридном формате оффлайн/онлайн аукциона) \n\n"
        "Победителям аукциона лоты выдаются/высылаются по договоренности, в удобный обеим сторонам день\n\n"
        "Если у вас есть вопросы, вы можете обратиться с ними в чат к Nato \n"
        "P.S. Если вы думаете что очень умны и нашли какую-то уязвимость в боте - скорее всего так и есть, скорее всего она уже сотню раз оплакана в попытках исправить и не была исправлена. Живите с этим, я же как-то живу...",
        reply_markup=reply_markup
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    video_url = "https://www.youtube.com/watch?v=LjQZaD9EEJ0"
    buttons = [
        [InlineKeyboardButton("Назад", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await message.reply_text(
        "Это бот для проведения солевых аукционов. \n\n"
        "Данный бот сделан с помощью бесплатного chatgpt, храни его господь.\n"
        f'<a href="{video_url}">Все желающие приглашаются на Шрека 5 в 2026 году</a>\n'
        "Спасибо тестировщикам (тут не забыть указать их)",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def main() -> None:
    await database.init_db()

    app = (
        ApplicationBuilder()
        .token(TG_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auction", auction_info))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("delete", delete_bid))

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Показать лоты$'), handle_show_lots_button))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex('^Показать свои ставки$'), show_user_bids))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex('^📋 Информация об аукционе$'), auction_info))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex('^ℹ️ О боте$'), info))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text_message))

    app.add_handler(CallbackQueryHandler(lot_detail, pattern="^view_"))
    app.add_handler(CallbackQueryHandler(go_to_lots, pattern="^go_to_lots$"))
    app.add_handler(CallbackQueryHandler(start_bid, pattern="^bid_start_"))
    app.add_handler(CallbackQueryHandler(bid_increase, pattern="^bid_increase_"))
    app.add_handler(CallbackQueryHandler(set_individual_bid, pattern="^set_bid_"))
    app.add_handler(CallbackQueryHandler(show_description, pattern="^description_"))
    app.add_handler(CallbackQueryHandler(auction_info, pattern='^auction_info$'))
    app.add_handler(CallbackQueryHandler(handle_back_to_start, pattern="^back_to_start$"))

    logger.info("Bot starting...")

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        logger.info("Bot started successfully")

        # Keep the bot running until a shutdown signal is received
        while True:
            await asyncio.sleep(60)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received, stopping gracefully...")
    finally:
        if app.updater and app.updater.running:
            await app.updater.stop()
        if app.running:
            await app.stop()
        await app.shutdown()
        await database.close_pool()
        logger.info("Bot stopped gracefully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # This can happen if the event loop is already running, e.g. in some environments.
        # We can try to get the existing loop and run the main function in it.
        loop = asyncio.get_running_loop()
        loop.run_until_complete(main())

