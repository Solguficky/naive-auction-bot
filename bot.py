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
        'title': 'Набор из двух значков "Тыковки. Обычные"',
        'description': 'Хэлуин и тыквы. Осень. Вы поняли.\n'
        'Автор - Нян',
        'min_bid_step': 9.0,
        'starting_price': 42.0,
        'image_url': 'https://disk.yandex.ru/i/Y9HWQdxinuS9ZQ'
    },
    2: {
        'title': 'Фигурка "ТВ-Стример"',
        'description': 'Комплект: \n'
        '1. Статуэтка из Photopolymer resin \n'
        '2. Сертификат of Authenticity \n'
        '3. Подарочный box \n'
        'Получите настоящее воплощение стримов ТВ-дичи себе на полку.\n'
        'Автор - Пугало',
        'min_bid_step': 50.0,
        'starting_price': 500.0,
        'image_url': 'https://disk.yandex.ru/i/SA4oiZGjprRyOw'
    },
    3: {
        'title': 'Вечный календарь СТРИМОВЕЧНОСТЬ',
        'description': 'Чтобы точно не пропустить стрим или сходку!\n'
        'Перед вами "рендер" вечного календаря с кастомным принтом. С таким календарем вы сможете больше никогда не пользоваться обычными физическими календарями! Вместо этого на многие года вам составит компанию Гуфовский и Спотти.\n'
        'P.S. Лот уже передан в печать, но физически на руки еще не получен..предполагается что он будет готов к Хэллоуину, но если изготовление задержится - не беспокойтесь, я лично заеду за ним и передам владельцу лота так или иначе).\n'
        'Автор - Nato',
        'min_bid_step': 88.0,
        'starting_price': 1111.0,
        'image_url': 'https://disk.yandex.ru/i/EEC_N2byM7h7jg'
    },
    4: {
        'title': 'Картина по номерам Тыковский',
        'description': 'КРАСКА В КОМПЛЕКТ НЕ ВХОДИТ. \n'
        'В комплекте - холст на подрамнике. Две кисти. И открытка с легендой цветов. \n'
        'Размер 10х10 \n'
        'Автор - Нян',
        'min_bid_step': 42.0,
        'starting_price': 142.0,
        'image_url': 'https://disk.yandex.ru/i/l0cIA-f1w7yafA'
    },
    5: {
        'title': 'Комплект из двух значков "Трупики"',
        'description': 'Это приведение и череп... Кого-то из почивших :d \n'
        'Автор - Нян',
        'min_bid_step': 9.0,
        'starting_price': 42.0,
        'image_url': 'https://disk.yandex.ru/i/IMiczpfl1EqwMQ'
    },
    6: {
        'title': 'Картина по номерам с подвохом',
        'description': 'Неклассический набор для росписи картины. В набор входит холст 40х50 с разметкой, инструменты, краски и инструкция\n'
        'Автор - Петя',
        'min_bid_step': 100.0,
        'starting_price': 1000.0,
        'image_url': 'https://disk.yandex.ru/i/9ch-pVrhW-4Zbw'
    },
    7: {
        'title': 'Набор из двух значков "Zомби"',
        'description': 'Надгробие и мозги.\n'
        'надгробие с пасхалкой, мозги, судя по черноте уже залежавшие!\n'
        'Автор - Нян',
        'min_bid_step': 9.0,
        'starting_price': 42.0,
        'image_url': 'https://disk.yandex.ru/i/XpNppWNXyl4N-A'
    },
    8: {
        'title': 'Лонгслив NEDOSTRIMNOST\'',
        'description': 'Оно живое?\n'
        'Выигравшему(ей) лот я смогу напечатать представленный принт на черном/белом лонгсливе точно по размеру. Я закажу печать, схожу ножками в студию забрать заказ по готовности (пара дней), и доставлю тем или иным способом вам.\n'
        'Принт в процессе, но к финальным торгам будет готов.\n'
        'Автор - Nato',
        'min_bid_step': 120.0,
        'starting_price': 3000.0,
        'image_url': 'https://disk.yandex.ru/i/Z4oAyoOJO4ZbMA'
    },
    9: {
        'title': 'Фигурка "Стример наводит порядок"',
        'description': 'Комплект: \n'
        '1. Статуэтка из Photopolymer resin \n'
        '2. Сертификат of Authenticity \n'
        '3. Подарочный box \n'
        '4. Банка 0,5л (по желанию победителя торгов)\n'
        'А вот о том, что у него под юбкой - вы узнаете только если победите в торгах\n'
        'Автор - Пугало',
        'min_bid_step': 50.0,
        'starting_price': 500.0,
        'image_url': 'https://disk.yandex.ru/i/jwSvEC8sBdx8YQ'
    },
    10: {
        'title': 'Набор из двух значков "Тыковки. Майнкрафтовые"',
        'description': 'Осень - время тыквенного спаса! А какой тыквенный спас без светильника Джека (любой)\n'
        'Квадратно\n'
        'Автор - Нян',
        'min_bid_step': 9.0,
        'starting_price': 42.0,
        'image_url': 'https://disk.yandex.ru/i/vpO9MTf65TSRoQ'
    },
    11: {
        'title': 'Сертификат на мерч от Пугала',
        'description': 'Абсолютно эксклюзивная фигурка. Да да, вы не знаете какая, это знаю только я. Готовы ли вы рискнуть? Оххх ну вы бы видели что там за концепт...Поборитесь за право обладать тем, чего еще нет, но точно будет, дайте мне 3 дня. Ну может и не 3 дня. Срок изготовления - ну примерно до новогодней сходки. Ну или до нового года. Как вам считать удобнее. Но гарантирую - фигурка крутая\n'
        'Автор - Пугало',
        'min_bid_step': 50.0,
        'starting_price': 100.0,
        'image_url': 'https://disk.yandex.ru/i/pKjp5OOY-j5Jmw'
    }
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

async def delete_bid_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if user.id != CREATOR_ID:
        logger.warning(f'Попытка несанкционированного удаления ставки пользователем ID {user.id}.')
        await update.message.reply_text('У вас нет прав на удаление ставок. Рапорт уже составлен')
        return

    # Если ID ставки передан сразу в команде
    if len(context.args) == 1:
        try:
            bid_id = int(context.args[0])
            await perform_bid_deletion(update, bid_id)
        except ValueError:
            await update.message.reply_text("Пожалуйста, укажите корректный числовой ID ставки.")
    else:
        # Если ID не передан, просим ввести
        await update.message.reply_text("Пожалуйста, укажите ID ставки для удаления.\nФормат: /delete [ID] или введите ID в следующем сообщении.")
        context.user_data['awaiting_bid_id'] = True

async def perform_bid_deletion(update: Update, bid_id: int) -> None:
    """Выполняет удаление ставки и отправляет результат"""
    # Сначала получаем информацию о ставке
    bid = await database.get_bid_by_id(bid_id)
    
    if not bid:
        await update.message.reply_text(f"❌ Ставка с ID {bid_id} не найдена.")
        return
    
    # Показываем информацию о ставке перед удалением
    lot_title = auction_lots.get(bid['lot_id'], {}).get('title', 'Неизвестный лот')
    
    await update.message.reply_text(
        f"Информация о ставке:\n"
        f"ID: {bid['id']}\n"
        f"Лот: {lot_title} (ID: {bid['lot_id']})\n"
        f"Пользователь ID: {bid['user_id']}\n"
        f"Сумма: {bid['amount']} руб.\n"
        f"Дата: {bid['created_at']}"
    )
    
    # Удаляем ставку
    success = await database.delete_bid(bid_id)
    
    if success:
        await update.message.reply_text(f"✅ Ставка с ID {bid_id} успешно удалена.")
        logger.info(f"Admin {update.effective_user.id} deleted bid {bid_id}")
    else:
        await update.message.reply_text(f"❌ Не удалось удалить ставку с ID {bid_id}.")


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
    
    # Кнопка возврата к списку лотов
    buttons.append([InlineKeyboardButton("◀️ Назад к лотам", callback_data='go_to_lots')])

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(
        text=f"Лот: {lot['title']}\n"
             f"Текущая ставка: {current_bid if current_bid else 'Нет ставок'}\n"
             "Выберите действие:",
        reply_markup=reply_markup
    )

async def go_to_lots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    
    # Создаем кнопки с лотами
    lot_buttons = []
    for lot_id, lot_info in auction_lots.items():
        lot_buttons.append([InlineKeyboardButton(f'Лот {lot_id}: {lot_info["title"]}', callback_data=f'view_{lot_id}')])
    
    reply_markup = InlineKeyboardMarkup(lot_buttons)
    
    # Отправляем новое сообщение со списком лотов
    await update.callback_query.message.reply_text('Доступные лоты:', reply_markup=reply_markup)

async def start_bid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lot_id = int(query.data.split('_')[2])
    starting_price = auction_lots[lot_id]['starting_price']
    
    user = query.from_user
    bid_id = await database.save_bid(
        lot_id, 
        user.id, 
        starting_price,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

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
    
    user = query.from_user
    bid_id = await database.save_bid(
        lot_id, 
        user.id, 
        new_bid,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

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

async def view_all_bids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все ставки по всем лотам (для админа)"""
    user = update.effective_user

    if user.id != CREATOR_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    bids_by_lots = await database.get_all_bids_by_lots()
    
    if not bids_by_lots:
        await update.message.reply_text("Пока нет ни одной ставки.")
        return

    for lot_id in sorted(bids_by_lots.keys()):
        lot_title = auction_lots.get(lot_id, {}).get('title', 'Неизвестный лот')
        bids = bids_by_lots[lot_id]
        
        message_lines = [f"📦 <b>Лот {lot_id}: {lot_title}</b>", f"Всего ставок: {len(bids)}\n"]
        
        for bid in bids[:10]:  # Показываем только топ-10 ставок
            username = bid.get('username') or 'Нет username'
            first_name = bid.get('first_name') or ''
            display_name = f"@{username}" if username != 'Нет username' else first_name or f"ID{bid['user_id']}"
            
            message_lines.append(
                f"• ID ставки: {bid['id']} | {display_name}\n"
                f"  Сумма: {bid['amount']} руб. | {bid['created_at']}"
            )
        
        if len(bids) > 10:
            message_lines.append(f"\n... и еще {len(bids) - 10} ставок")
        
        await update.message.reply_text("\n".join(message_lines), parse_mode="HTML")

async def view_lot_bids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все ставки по конкретному лоту (для админа)"""
    user = update.effective_user

    if user.id != CREATOR_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Пожалуйста, укажите ID лота.\nФормат: /view_lot [ID]")
        return

    try:
        lot_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите корректный числовой ID лота.")
        return

    if lot_id not in auction_lots:
        await update.message.reply_text(f"Лот с ID {lot_id} не найден.")
        return

    lot_title = auction_lots[lot_id]['title']
    bids = await database.get_lot_bids(lot_id)
    
    if not bids:
        await update.message.reply_text(f"По лоту '{lot_title}' пока нет ставок.")
        return

    max_bid = max(bid['amount'] for bid in bids)
    
    message_lines = [
        f"📦 <b>Лот {lot_id}: {lot_title}</b>",
        f"Всего ставок: {len(bids)}",
        f"Максимальная ставка: {max_bid} руб.\n"
    ]
    
    # Сортируем по сумме (убывание)
    sorted_bids = sorted(bids, key=lambda x: x['amount'], reverse=True)
    
    for bid in sorted_bids:
        username = bid.get('username') or 'Нет username'
        first_name = bid.get('first_name') or ''
        display_name = f"@{username}" if username != 'Нет username' else first_name or f"ID{bid['user_id']}"
        
        message_lines.append(
            f"• ID ставки: {bid['id']} | {display_name}\n"
            f"  Сумма: {bid['amount']} руб. | {bid['created_at']}"
        )
    
    # Telegram ограничивает сообщения 4096 символами, разбиваем если нужно
    current_message = "\n".join(message_lines)
    if len(current_message) > 4000:
        # Отправляем по частям
        chunks = [message_lines[0:3]]  # Заголовок
        chunk = []
        for line in message_lines[3:]:
            chunk.append(line)
            if len("\n".join(chunk)) > 3500:
                chunks.append(chunk)
                chunk = []
        if chunk:
            chunks.append(chunk)
        
        for i, chunk in enumerate(chunks):
            await update.message.reply_text("\n".join(chunk), parse_mode="HTML")
    else:
        await update.message.reply_text(current_message, parse_mode="HTML")

async def bids_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает краткую сводку по всем лотам (для админа)"""
    user = update.effective_user

    if user.id != CREATOR_ID:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return

    summary = await database.get_bids_summary()
    
    if not summary:
        await update.message.reply_text("Пока нет ни одной ставки.")
        return

    message_lines = ["📊 <b>Сводка по ставкам</b>\n"]
    
    for item in summary:
        lot_id = item['lot_id']
        lot_title = auction_lots.get(lot_id, {}).get('title', 'Неизвестный лот')
        
        message_lines.append(
            f"<b>Лот {lot_id}</b>: {lot_title}\n"
            f"  Ставок: {item['bid_count']}\n"
            f"  Макс: {item['max_bid']} руб. | Мин: {item['min_bid']} руб.\n"
        )
    
    await update.message.reply_text("\n".join(message_lines), parse_mode="HTML")

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
    # Проверяем, ожидается ли ввод ID ставки для удаления
    if 'awaiting_bid_id' in context.user_data and context.user_data['awaiting_bid_id']:
        bid_id_str = update.message.text.strip()
        try:
            bid_id = int(bid_id_str)
            await perform_bid_deletion(update, bid_id)
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

        bid_id = await database.save_bid(
            lot_id, 
            user.id, 
            bid_amount,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

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
    
    # Кнопка возврата к списку лотов
    buttons.append([InlineKeyboardButton("◀️ Назад к лотам", callback_data='go_to_lots')])

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
        chat_id = query.message.chat.id
    else:
        message = update.message
        chat_id = message.chat.id

    buttons = [
        [InlineKeyboardButton("Задать вопрос", url="https://t.me/Neptunini")],
        [InlineKeyboardButton("Назад", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Сначала отправляем текст
    await message.reply_text(
        "Добро пожаловать на солевой аукцион. Все операции на аукционе осуществляются через данного бота:\n\n"
        "Информация о том, как работать с ботом:\n\n"
        "Через кнопки можно вызвать список лотов (Показать лоты) или посмотреть на какие лоты вы уже сделали ставки (Показать свои ставки), чтобы посмотреть держите ли вы максимальную ставку по своему лоту. В списке лотов при выборе конкретного лота вы можете: посмотреть его описание, и сделать ставку (если вы первый, то она = стартовой цене; при наличии других ставок вы можете либо повысить ставку на минимальный шаг, либо сделать индивидуальную ставку -  указать любую другую сумму ставки, превышающую минимальный шаг)\n\n"
        "Аукцион продлится с 25.10.2025 по 01.11.2025 (время по СПБ). Все ставки принимаются в рублях. Выигравшей считается последняя принятая ставка (последний час торгов проходит в гибридном формате оффлайн/онлайн аукциона).\n\n"
        "Победителям аукциона лоты выдаются/высылаются по договоренности, в удобный обеим сторонам день\n\n"
        "Если у вас есть вопросы, вы можете обратиться с ними в чат к Nato \n"
        "P.S. Если вы думаете что очень умны и нашли какую-то уязвимость в боте - скорее всего так и есть, скорее всего она уже сотню раз оплакана в попытках исправить и не была исправлена. Живите с этим, я же как-то живу...",
        reply_markup=reply_markup
    )

    # Потом отправляем фото со стикерпаком
    sticker_image_url = 'https://disk.yandex.ru/i/TO62nQyVMBjNiw'
    
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=sticker_image_url,
            caption="🎁 БОНУС ДЛЯ ПОБЕДИТЕЛЕЙ! 🎁\n\n"
                    "Каждый победитель любого лота получает В ПОДАРОК набор стикеров!\n"
                    "(не больше одного стикерпака в руки)"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке изображения стикерпака: {e}")

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
    app.add_handler(CommandHandler("delete", delete_bid_command))
    app.add_handler(CommandHandler("list_lots", list_lots))
    app.add_handler(CommandHandler("view_all_bids", view_all_bids))
    app.add_handler(CommandHandler("view_lot", view_lot_bids))
    app.add_handler(CommandHandler("summary", bids_summary))

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

