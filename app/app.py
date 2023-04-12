import asyncio
from os import getenv
from contextlib import suppress

from dotenv import load_dotenv
from aiogram.types import Message
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart

from utils import ChatGPT, DBDialog


async def main():
    dp = Dispatcher()  # Объект класса Dispatcher
    db_dialog = DBDialog()  # Объект класса DBDialog
    db_dialog.add_dialog('0', 'Система')  # Создаём системный диалог
    chat_gpt = ChatGPT(getenv('GPT_TOKEN'))  # Объект класса ChatGPT
    bot = Bot(getenv('TG_TOKEN'), parse_mode='HTML')  # Объект класса Bot

    @dp.message(CommandStart())
    async def handler_command_start(m: Message) -> None:
        system_dialog = db_dialog.get_messages('0')  # Получаем все системные сообщения
        system_dialog.append({"role": "user", "content": "Кто ты и чем ты полезен? Оформи текст смайликами."})
        chat_gpt_answer = await chat_gpt.answer(system_dialog)  # Отправляем диалог в Chat GPT
        await m.answer(f'<b>{chat_gpt_answer["choices"][0]["message"]["content"]}</b>')  # Отправляем ответ пользователю

    @dp.message(Command('reset'))
    async def handler_command_start(m: Message) -> None:
        user_id = m.from_user.id
        if db_dialog.get_messages(user_id):  # Проверяем существование диалога
            db_dialog.del_dialog(user_id)  # Сбрасываем диалог
        await m.reply('<b>Контекст диалога сброшен</b> 💬')

    @dp.message()
    async def handler_chat_gpt(m: Message) -> None:
        """
        Обработчик для общения с Chat GPT

        :param m: Объект класса Message
        :return: None
        """
        user_id = m.from_user.id
        first_name = m.from_user.first_name
        db_dialog.add_dialog(user_id, first_name)  # Добавляем диалог, если его не существует
        db_dialog.add_message(user_id, 'user', m.text)  # Добавляем сообщение пользователя в диалог
        user_messages = db_dialog.get_messages(user_id)  # Получаем все сообщения пользователя
        chat_gpt_answer = await chat_gpt.answer(user_messages)  # Отправляем сообщения в Chat GPT
        db_dialog.add_message(user_id, 'assistant',
                              chat_gpt_answer["choices"][0]["message"]["content"])  # Добавляем ответ в диалог
        await m.reply(chat_gpt_answer["choices"][0]["message"]["content"])  # Отправляем ответ пользователю

        if len(db_dialog.get_messages(user_id)) > 100:  # Если в диалоге больше 30 сообщений, сбрасываем его
            db_dialog.del_dialog(user_id)  # Сбрасываем диалог

    await dp.start_polling(bot)


if __name__ == '__main__':
    load_dotenv('../.env')
    with suppress(KeyboardInterrupt):  # Игнорирование ошибок при остановке
        asyncio.run(main())  # Запускаем асинхронную функцию из синхронного контекста
