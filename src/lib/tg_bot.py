import json

from lib.options import Options
from lib.gspread_reader import GspreadReader
import logging
import json
from typing import Optional

from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.constants import ChatMemberStatus

from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)

class TgBot:
    token = ''
    app = None
    logger = None
    options = None

    commands = {
        'get_source': {'args': [], 'description': 'Показать мой текущий источник'},
        'set_source': {'args': ['source name'], 'description': 'Установить мой источник'},
        'i': {'args': ['key'], 'description': 'Найти строку и вывести выбранные столбцы'},
        'cfg_set_source': {'args': ['source name', 'source url', 'sheet_number', 'seek column', 'return columns'],
                           'description': 'Добавить/обновить источник данных'},
        'cfg_get_source': {'args': ['source name'], 'description': 'Показать конфигурацию источника'},
        'start':            {'args': [], 'description': 'Показать приветствие'},
        'help':             {'args': [], 'description': 'Показать справку'},
    }

    def __init__(self, token, config):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )

        # set higher logging level for httpx to avoid all GET and POST requests being logged
        logging.getLogger("httpx").setLevel(logging.WARNING)
        self.logger = logging.getLogger(__name__)

        self.token = token
        self.app = Application.builder().token(token).build()

        # Get Redis connection parameters from config
        redis_host = config.get('redis_host', 'localhost')
        redis_port = int(config.get('redis_port', 6379))
        redis_password = config.get('redis_password', None)

        self.options = Options({
            'current_source':              {'type': 'str', 'description': 'Current data source', 'is_global_entity': False, 'default': 'default'},
            'sources':                     {'type': 'dict', 'description': 'Data source name', 'is_global_entity': True},
        }, redis_host=redis_host, redis_port=redis_port, redis_password=redis_password)

        self.gspread = GspreadReader(config)

    async def is_admin(self, update: Update, user_id) -> bool:
        """Checks if a user is an administrator in the current chat."""
        if not update.effective_chat:
            return False

        member = await update.effective_chat.get_member(user_id)

        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

    async def cmd_i(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_message.from_user

        try:
            if len(context.args) < 1:
                await update.effective_chat.send_message('Использование: /i <ключ>')
                return
            key = context.args[0]
            
            source_name = self.options.get_option(user.id, 'current_source')
            source_options = json.loads(self.options.get_option(user.id, 'sources', source_name))

            if source_options == {}:
                await update.effective_chat.send_message('Конфигурация источника не найдена')
                return

            # Validate required fields
            missing = [f for f in ['url', 'seek', 'columns'] if f not in source_options or source_options[f] in [None, '']]
            if missing:
                await update.effective_chat.send_message('Источник настроен некорректно: отсутствует(ют) ' + ", ".join(missing))
                return

            url = source_options['url']
            seek = source_options['seek']
            columns = [c.strip() for c in str(source_options['columns']).split(',') if c.strip()]
            sheet_idx = int(source_options['sheet'])

            info = await self.gspread.get_info(url, key, seek, columns, sheet_idx)

            if not info or info == {}:
                await update.effective_chat.send_message('Значение не найдено')
                return

            # Форматирование ответа: заголовок и выравненные колонки
            title = f'<b>Результат для ключа</b> <code>{key}</code> (лист {sheet_idx})\n'
            max_header = max((len(h) for h in info.keys()), default=0)
            lines = []
            for h, v in info.items():
                pad = ' ' * (max_header - len(h))
                lines.append(f'<code>{h}{pad}</code> : <b>{v}</b>')
            await update.effective_chat.send_message(title + "\n".join(lines), parse_mode=ParseMode.HTML)
            return
        except Exception as e:
            await update.effective_chat.send_message(f'Ошибка при получении данных: {str(e)}')

    async def cmd_cfg_get_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_message.from_user
        source_name = context.args[0]

        try:
            source = self.options.get_option(user.id, 'sources', source_name)
            await update.effective_chat.send_message(f'Конфигурация источника "{source_name}": {json.dumps(source)}')
        except Exception as e:
            await update.effective_chat.send_message(f'Ошибка при получении конфигурации: {str(e)}')

    async def cmd_cfg_set_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """ """
        # /add_source my https://docs.google.com/spreadsheets/d/1iUWfjYlGYiMTAN0b9oXy1OLAf-mic9PDK0p8PoRQzEQ 1 2,3,4

        user = update.effective_message.from_user
        source_name = context.args[0]

        source_params = {
            'url': context.args[1],
            'sheet': context.args[2],
            'seek': context.args[3],
            'columns': context.args[4]
        }

        try:
            await update.effective_chat.send_message(f'Сохраняю источник {source_name}')
            self.options.set_option(user.id, 'sources', json.dumps(source_params), source_name)
        except Exception as e:
            await update.effective_chat.send_message(f'Ошибка при сохранении источника: {str(e)}')

    async def cmd_get_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """ """
        user = update.effective_message.from_user

        try:
            source_name = self.options.get_option(user.id, 'current_source')
            await update.effective_chat.send_message(f'Ваш текущий источник: "{source_name}"')
        except Exception as e:
            await update.effective_chat.send_message(f'Ошибка при получении имени источника: {str(e)}')

    async def cmd_set_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """ """
        user = update.effective_message.from_user

        source_name = context.args[0]

        try:
            source = self.options.get_option(user.id, 'sources', source_name)
            if source == {}:
                await update.effective_chat.send_message(f'Источник не найден: {source_name}')

                return

            await update.effective_chat.send_message(f'Сменяю источник на "{source_name}"')
            self.options.set_option(user.id, 'current_source', source_name)
        except Exception as e:
            await update.effective_chat.send_message(f'Ошибка при установке источника: {str(e)}')


    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        start_message = "<b>Бот для получения данных из Google Таблиц</b>\n"
        start_message += "Простой бот, который получает информацию из Google Spreadsheet.\n\n"
        start_message += "<b>Исходники и руководство:</b> https://bit.ly/3WzVOtB\n"

        start_message += "\n" + self.help_message()

        await update.effective_chat.send_message(start_message,
                                                 parse_mode=ParseMode.HTML
                                                 )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать справку"""
        help_message = self.help_message()

        await update.effective_chat.send_message(help_message,
                                                 parse_mode=ParseMode.HTML
                                                 )

    def help_message(self) -> str:
        result = '<b>Доступные команды:</b>\n'

        for command in self.commands:
            result += f'<b>/{command}</b>'

            if 'args' in self.commands[command]:
                for arg in self.commands[command]['args']:
                    parts = arg.split('=')

                    if len(parts) == 1:
                        da = '&lt;'
                        db = '&gt;'
                    else:
                        da = '['
                        db = ']'

                    result += f' {da}{arg}{db}'

            result += ': ' + self.commands[command]['description'] + '\n'

        return result

    def extract_status_change(self, chat_member_update: ChatMemberUpdated) -> Optional[tuple[bool, bool]]:
        """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
        of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
        the status didn't change.
        """
        status_change = chat_member_update.difference().get("status")
        old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

        if status_change is None:
            return None

        old_status, new_status = status_change
        was_member = old_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
        is_member = new_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

        return was_member, is_member

    async def track_chats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Tracks the chats the bot is in."""
        result = self.extract_status_change(update.my_chat_member)
        if result is None:
            return
        was_member, is_member = result

        # Let's check who is responsible for the change
        cause_name = update.effective_user.full_name

        # Handle chat types differently:
        chat = update.effective_chat
        if chat.type == Chat.PRIVATE:
            if not was_member and is_member:
                # This may not be really needed in practice because most clients will automatically
                # send a /start command after the user unblocks the bot, and start_private_chat()
                # will add the user to "user_ids".
                # We're including this here for the sake of the example.
                self.logger.info("%s unblocked the bot", cause_name)
                context.bot_data.setdefault("user_ids", set()).add(chat.id)
            elif was_member and not is_member:
                self.logger.info("%s blocked the bot", cause_name)
                context.bot_data.setdefault("user_ids", set()).discard(chat.id)
        elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
            if not was_member and is_member:
                self.logger.info("%s added the bot to the group %s", cause_name, chat.title)
                context.bot_data.setdefault("group_ids", set()).add(chat.id)
            elif was_member and not is_member:
                self.logger.info("%s removed the bot from the group %s", cause_name, chat.title)
                context.bot_data.setdefaПокult("group_ids", set()).discard(chat.id)
        elif not was_member and is_member:
            self.logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            self.logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)

    async def common_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Bot commands dispatcher"""
        user = update.effective_message.from_user
        message_text = update.effective_message.text
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id

        command_with_bot_name = message_text.split(' ')[0]
        command_name = command_with_bot_name.split('@')[0][1:]

        if command_name not in self.commands:
            await update.effective_chat.send_message('Неизвестная команда')
            return

        if 'admin' in self.commands[command_name] and self.commands[command_name]['admin'] is True:
            if not await self.is_admin(update, user.id):
                await update.effective_chat.send_message('Только администраторы могут вызвать эту команду')

                return

        obl_args_count = 0

        if 'args' in self.commands[command_name]:
            for arg in self.commands[command_name]['args']:
                parts = arg.split('=')

                if len(parts) == 1:
                    obl_args_count += 1

        if len(context.args) < obl_args_count:
            await update.effective_chat.send_message(f'Эта команда требует минимум {obl_args_count} аргумент(ов)')
            return

        handler = getattr(self, 'cmd_' + command_name)

        if not handler:
            await update.effective_chat.send_message(f'Нет обработчика для команды {command_name}')

        await handler(update, context)

        return

    def run(self):
        """Start the bot"""
        for command in self.commands:
            self.app.add_handler(CommandHandler(command, self.common_handler))

        # Handle chat join request
        self.app.add_handler(ChatMemberHandler(self.track_chats, ChatMemberHandler.MY_CHAT_MEMBER))

        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    def stop(self):
        """Stop the bot and close Redis connection"""
        if hasattr(self, 'options') and self.options:
            self.options.close()