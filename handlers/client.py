import asyncio
import logging
import json
from typing import List, Union
from aiogram import types, Dispatcher
from create_bot import dp, bot, clients_db
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboards import start_button, back_register, rooms, \
    room_connect, back_enter_connect, buttons_connect, back_ans, next_enter_connect_client, \
    next_enter_connect, history_button, move_button, move_button_solo


logging.basicConfig(level=logging.ERROR, filename="py_client_log.log", filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")


class FSMClient(StatesGroup):
    number = State()
    connect_message = State()
    problem = State()
    proceed_answer = State()
    proceed_answer_id = State()
    move_id = State()
    photo = State()
    media_group = State()
    edit_message_id = State()


class AlbumMiddleware(BaseMiddleware):

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.05):
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if not message.media_group_id:
            self.album_data[message.from_user.id] = [message]

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.from_user.id]
            return
        else:
            try:
                self.album_data[message.media_group_id].append(message)
                raise CancelHandler()
            except KeyError:
                self.album_data[message.media_group_id] = [message]
                await asyncio.sleep(self.latency)

                message.conf["is_last"] = True
                data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: types.Message, result: dict, data: dict):
        if not message.media_group_id:
            if message.from_user.id and message.conf.get("is_last"):
                del self.album_data[message.from_user.id]
        else:
            if message.media_group_id and message.conf.get("is_last"):
                del self.album_data[message.media_group_id]


class Move:
    def __init__(self, iteration=None, button=None, button_error=None):
        self.iteration = iteration
        self.button = button
        self.button_error = button_error
        self.iteration_move = 0

    async def move_iteration(self, message: types.Message, state: FSMContext):
        try:
            all_history = self.iteration[1]
            iteration = self.iteration[0]
            if message.data == 'move_up':
                if iteration >= len(all_history) - 1:
                    iteration = 0
                else:
                    iteration += 1
            elif message.data == 'move_down':
                if iteration == 0:
                    iteration = len(all_history) - 1
                else:
                    iteration -= 1
            self.iteration_move = iteration
            await Move.move_button_object(self, message, state)
        except Exception as e:
            print(f"Произошёл сбой в движении! Пользователь: {message.from_user.id}, ошибка: {e}")
            await state.finish()
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text='Что-то пошло не так, начнём заново',
                                        reply_markup=self.button_error)

    async def move_button_object(self, message: types.Message, state: FSMContext):
        all_history = self.iteration[1]
        iteration = self.iteration_move
        if self.button == move_button:
            status = "Закрыто" if all_history[iteration][-1] == 1 else "Открыто"
            text = f'Обращение {iteration + 1} из {len(all_history)}\n' \
                   f'Статус: {status}\n' \
                   f'Тема вопроса: {all_history[iteration][3]}\n' \
                   f'Ваше обращение: \n{all_history[iteration][2]}'
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=text,
                                    reply_markup=self.button)
        iteration = [iteration, all_history]
        async with state.proxy() as data:
            data['move_id'] = iteration


welcome_text = 'Используйте меня для того, чтобы оставить жалобу, пожелание, предложения.\n'\
               'Через меня обработка ваших запросов идёт намного быстрее'
number_text = 'Введите, пожалуйста, ваш номер для связи\n'\
                                         ' \n'\
                                         'Пример: \n'\
                                         '375 ** *******\n'\
                                         '7 *** *******'


async def start(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id,
                           text=welcome_text,
                           reply_markup=start_button)


async def new_start(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text=welcome_text,
                                reply_markup=start_button)


async def new_client(message: types.Message, state: FSMContext):
    if clients_db.user_exists(message.from_user.id) and clients_db.user_num_exists(message.from_user.id):
        if clients_db.user_name_exists(message.from_user.id) != message.message.chat.username:
            clients_db.change_user_name(message.message.chat.username, message.from_user.id)
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Пожалуйста, выберите нужную вам категорию',
                                    reply_markup=rooms)

    else:
        if not clients_db.user_exists(message.from_user.id):
            clients_db.add_user(user_id=message.from_user.id, user_name=message.message.chat.username)
        await FSMClient.number.set()
        edit_message = await bot.edit_message_text(chat_id=message.from_user.id,
                                                   message_id=message.message.message_id,
                                                   text=number_text,
                                                   reply_markup=back_register)
        async with state.proxy() as data:
            data['edit_message_id'] = edit_message


async def room_conn(message: types.Message):
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text='Выберите интересующий вас пункт\n',
                                reply_markup=room_connect)


async def load_num_client(message: types.Message, state: FSMContext):
    num = ''
    if '/' in message.text:
        async with state.proxy() as data:
            edit_message = data['edit_message_id']
        await bot.send_message(chat_id=message.from_user.id,
                               text="Видимо вы хотели ввести команду, но я ждал номер телефона. \n"
                                    "Пожалуйста, введите вашу команду снова!",)
        await state.finish()
        try:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=edit_message.message_id,
                                        text=edit_message.text)
        except Exception as e:
            print(f'Сообщение уже было изменено! - {e} '
                  f'Функция "def load_num_client 1"')
    else:
        for number in message.text:
            if number.isdigit():
                num += number
        message.text = num
        if message.text.isdigit():
            if len(message.text) == 12 and message.text[0] == '3' or len(message.text) == 11 and message.text[0] == '7':
                async with state.proxy() as data:
                    data['number'] = message.text
                    edit_message = data['edit_message_id']
                    clients_db.add_number(data['number'])
                    clients_db.save_user_id_number(data['number'], message.from_user.id)
                    await state.finish()
                    try:
                        await bot.edit_message_text(chat_id=message.from_user.id,
                                                    message_id=edit_message.message_id,
                                                    text=edit_message.text)
                    except Exception as e:
                        print(f'Сообщение уже было изменено! - {e}'
                              f'Функция "def load_num_client 2"')

                await bot.send_message(chat_id=message.from_user.id,
                                       text='Ваш номер для связи был записан!\n'
                                            'Пожалуйста, выберите нужную вам категорию',
                                       reply_markup=rooms)
            else:
                async with state.proxy() as data:
                    edit_message = data['edit_message_id']
                try:
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=edit_message.message_id,
                                                text=edit_message.text)
                except Exception as e:
                    print(f'Сообщение уже было изменено! - {e}'
                          f'Функция "def load_num_client 3"')
                edit_message = await message.reply('Мы работаем с беларусскими номерами (12 цифр) '
                                                   'и российскими (11 цифр)\n'
                                                   '375 ** *******\n'
                                                   '7 *** *******', reply_markup=back_register)
                async with state.proxy() as data:
                    data['edit_message_id'] = edit_message
        else:
            async with state.proxy() as data:
                edit_message = data['edit_message_id']
            try:
                await bot.edit_message_text(chat_id=message.from_user.id,
                                            message_id=edit_message.message_id,
                                            text=edit_message.text)
            except Exception as e:
                print(f'Сообщение уже было изменено! - {e}'
                      f'Функция "def load_num_client 4"')
            await message.reply('Введите, пожалуйста, цифры!\n'
                                'Например:\n'
                                '375 ** *******\n'
                                '7 *** *******',
                                reply_markup=back_register)


async def back_room_client(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text='Пожалуйста, выберите нужную вам категорию',
                                reply_markup=rooms)


async def enter_connect(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        if message.data == 'forgot':
            data['problem'] = 'Забыл вещи'
            await FSMClient.connect_message.set()
            edit_message_id = await bot.edit_message_text \
                (chat_id=message.from_user.id,
                 message_id=message.message.message_id,
                 text='Пожалуйста, опишите проблему и мы разрешим её как можно скорее!\n'
                      'Фото присылайте одним сообщением с комментарием к нему',
                 reply_markup=back_enter_connect)
            data['edit_message_id'] = edit_message_id

        elif message.data == 'payment':
            data['problem'] = 'Что-то не так с оплатой'
            await FSMClient.connect_message.set()
            edit_message_id = await bot.edit_message_text \
                (chat_id=message.from_user.id,
                 message_id=message.message.message_id,
                 text='Пожалуйста, опишите проблему и мы разрешим её как можно скорее!\n'
                      'Фото присылайте одним сообщением с комментарием к нему',
                 reply_markup=back_enter_connect)
            data['edit_message_id'] = edit_message_id

        elif message.data == 'ride':
            data['problem'] = 'Проблема с поездкой'
            await FSMClient.connect_message.set()
            edit_message_id = await bot.edit_message_text \
                (chat_id=message.from_user.id,
                 message_id=message.message.message_id,
                 text='Пожалуйста, опишите проблему и мы разрешим её как можно скорее!\n'
                      'Фото присылайте одним сообщением с комментарием к нему',
                 reply_markup=back_enter_connect)
            data['edit_message_id'] = edit_message_id

        elif message.data == 'connect_question':
            data['problem'] = 'Есть вопрос по приложению'
            await FSMClient.connect_message.set()
            edit_message_id = await bot.edit_message_text \
                (chat_id=message.from_user.id,
                 message_id=message.message.message_id,
                 text='Пожалуйста, задайте ваш вопрос, мы ответим вам в этом чате\n'
                      'Фото присылайте одним сообщением с комментарием к нему',
                 reply_markup=back_enter_connect)
            data['edit_message_id'] = edit_message_id

        elif message.data == 'complaint':
            data['problem'] = 'Жалоба'
            await FSMClient.connect_message.set()
            edit_message_id = await bot.edit_message_text \
                (chat_id=message.from_user.id,
                 message_id=message.message.message_id,
                 text='Пожалуйста, опишите проблему и мы разрешим её как можно скорее!\n'
                      'Фото присылайте одним сообщением с комментарием к нему',
                 reply_markup=back_enter_connect)
            data['edit_message_id'] = edit_message_id

        elif message.data == 'complaint_r_time':
            data['problem'] = 'Жалоба во время поездки (Из машины)'
            await FSMClient.connect_message.set()
            edit_message_id = await bot.edit_message_text \
                (chat_id=message.from_user.id,
                 message_id=message.message.message_id,
                 text='Пожалуйста, опишите проблему если вы прямо сейчас в автомобиле\n'
                      'Фото присылайте одним сообщением с комментарием к нему',
                 reply_markup=back_enter_connect)
            data['edit_message_id'] = edit_message_id

        elif message.data == 'offer':
            data['problem'] = 'Пожелание/Предложение'
            await FSMClient.connect_message.set()
            edit_message_id = await bot.edit_message_text \
                (chat_id=message.from_user.id,
                 message_id=message.message.message_id,
                 text='Пожалуйста, ваше пожелание или предложение, мы ответим вам в этом чате\n'
                      'Фото присылайте одним сообщением с комментарием к нему',
                 reply_markup=back_enter_connect)
            data['edit_message_id'] = edit_message_id

        elif message.data == 'other':
            data['problem'] = 'Другое'
            await FSMClient.connect_message.set()
            edit_message_id = await bot.edit_message_text\
                (chat_id=message.from_user.id,
                 message_id=message.message.message_id,
                 text='Пожалуйста, опишите проблему или тему которую вы хотели затронуть!\n'
                      'Фото присылайте одним сообщением с комментарием к нему',
                 reply_markup=back_enter_connect)
            data['edit_message_id'] = edit_message_id


async def call_admin(message: types.Message, state: FSMContext, album: List[types.Message]):
    if not message.media_group_id:
        if message.photo:
            if message.caption is None:
                await bot.send_message(chat_id=message.from_user.id,
                                       text='Вы не можете отправить запрос без описания проблемы!')
            else:
                async with state.proxy() as data:
                    data['connect_message'] = message.caption
                    edit_message_id = data['edit_message_id']
                    try:
                        await bot.edit_message_text(chat_id=message.from_user.id,
                                                    message_id=edit_message_id.message_id,
                                                    text=edit_message_id.text)
                    except Exception as e:
                        print(f'Сообщение уже было изменено! - {e}'
                              f'Функция "def call_admin 1"')
                    clients_db.add_connect(message.from_user.id, data['connect_message'], data['problem'])
                    """Записать в базу данных"""
                    await enter_admin(data['problem'], data['connect_message'],
                                      message, clients_db.take_last_id_connect())
                    await state.finish()
                    await bot.send_message(message.from_user.id,
                                           'Ваш запрос был создан. В этом чате вам ответит наш специалист\n'
                                           'Чтобы открыть меню, нажмите /start')
                await state.finish()
        else:
            async with state.proxy() as data:
                data['connect_message'] = message.text
                edit_message_id = data['edit_message_id']
                try:
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=edit_message_id.message_id,
                                                text=edit_message_id.text)
                except Exception as e:
                    print(f'Сообщение уже было изменено! - {e}'
                          f'Функция "def call_admin 2"')
                clients_db.add_connect(message.from_user.id, data['connect_message'], data['problem'])
                """Записать в базу данных"""
                await enter_admin(data['problem'], data['connect_message'], message, clients_db.take_last_id_connect())
                await state.finish()
                await bot.send_message(message.from_user.id,
                                       'Ваш запрос был создан. В этом чате вам ответит наш специалист\n'
                                       'Чтобы открыть меню, нажмите /start')
    else:
        media_group = types.MediaGroup()
        for obj in album:
            if obj.photo:
                file_id = obj.photo[-1].file_id
                caption = album[0].caption
            else:
                file_id = obj[obj.content_type].file_id
            try:
                media_group.attach({"media": file_id, "type": obj.content_type})
            except ValueError:
                return await message.answer("Данный тип коллажа не поддерживается.")
        if caption is None:
            await bot.send_message(chat_id=message.from_user.id,
                                   text='Вы не можете отправить запрос без описания проблемы!')
        else:
            async with state.proxy() as data:
                data['connect_message'] = media_group
                edit_message_id = data['edit_message_id']
                try:
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=edit_message_id.message_id,
                                                text=edit_message_id.text)
                except Exception as e:
                    print(f'Сообщение уже было изменено! - {e}'
                          f'Функция "def call_admin 3"')
            await call_media_admin(message, media_group, data['problem'], caption)
            await state.finish()
            await bot.send_message(message.from_user.id,
                                   'Ваш запрос был создан. В этом чате вам ответит наш специалист\n'
                                   'Чтобы открыть меню, нажмите /start')


async def call_media_admin(message, media_group, problem, caption):
    clients_db.add_connect(message.from_user.id, caption, problem)
    last_connect = clients_db.take_last_id_connect()
    notification = clients_db.take_all_admin()
    text = f'Создано обращение от пользователя!\n'\
           f'Номер пользователя: +{clients_db.take_user_num(message.from_user.id)}\n'\
           f'Ссылка телеграм: @{message.chat.username}\n'\
           f'Жалоба: {problem}\n'\
           f'Текст обращения: \n\n{caption}'
    for admins in notification:
        await bot.send_media_group \
            (chat_id=admins[1],
             media=media_group)
        take_id_message = await bot.send_message(admins[1], text, reply_markup=buttons_connect)
        clients_db.add_notification(admins[0], last_connect, take_id_message.message_id, take_id_message.text)
    clients_db.create_new_table_user(message.from_user.id, last_connect, caption, media_group)


async def quit_account(message: types.Message):
    clients_db.change_user_number(None, message.from_user.id)
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text=welcome_text,
                                reply_markup=start_button)


async def enter_admin(problem, text, message_client, last_connect):
    notification = clients_db.take_all_admin()
    text_message = f'Создано обращение от пользователя!\n'\
                   f'Номер пользователя: +{clients_db.take_user_num(message_client.from_user.id)}\n'\
                   f'Ссылка телеграм: @{message_client.chat.username}\n'\
                   f'Жалоба: {problem}\n'\
                   f'Текст обращения: \n\n{text}'
    if not message_client.photo:
        for admins in notification:
            take_id_message = await bot.send_message \
                (chat_id=admins[1],
                 text=text_message,
                 reply_markup=buttons_connect)
            clients_db.add_notification(admins[0], last_connect, take_id_message.message_id, take_id_message.text)
        clients_db.create_new_table_user(message_client.from_user.id, last_connect, text)
    else:
        for admins in notification:
            await bot.send_photo (chat_id=admins[1], photo=message_client.photo[-1].file_id)
            take_id_message = await bot.send_message \
                (chat_id=admins[1],
                 text=text_message,
                 reply_markup=buttons_connect)
            clients_db.add_notification(admins[0], last_connect, take_id_message.message_id, take_id_message.text)
        clients_db.create_new_table_user\
            (message_client.from_user.id, last_connect, text, message_client.photo[-1].file_id)


async def proceed_answer_connect_admin(message: types.Message, state: FSMContext):
    """Нажатие на кнопку ответа. Создание сообщения о вводе текcта, и ожадании ввода"""
    async with state.proxy() as data:
        data['proceed_answer_id'] = message.message.message_id
        await FSMClient.proceed_answer.set()
        edit_message_id = await bot.edit_message_text(chat_id=message.from_user.id,
                                                      message_id=message.message.message_id,
                                                      text='Введите ответ в одном сообщении.\n'
                                                           'Фото присылайте одним сообщением с комментарием к нему',
                                                      reply_markup=back_ans)
        data['edit_message_id'] = edit_message_id


async def proceed_answer(message: types.Message, state: FSMContext, album: List[types.Message]):
    async with state.proxy() as data:
        edit_message_id = data['edit_message_id']
        try:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=edit_message_id.message_id,
                                        text=edit_message_id.text)
        except Exception as e:
            print(f'Сообщение уже было изменено! - {e}'
                  f'Функция "def proceed_answer"')
    if not message.media_group_id:
        if message.photo:
            async with state.proxy() as data:
                proceed_answer_id = data['proceed_answer_id']
                data['proceed_answer'] = message.text
            notification_id = clients_db.take_connect_notification(proceed_answer_id)
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=notification_id[0][3],
                                        text=notification_id[0][4])
            await proceed_admin_media(text=message.caption, message_client=message,
                                      last_connect=notification_id[0][2], admin_id=notification_id[0][1],
                                      old_message_id=notification_id[0][3])
            await bot.send_message(message.from_user.id,
                                   'Ваш ответ был доставлен специалисту. В этом чате вы получите ответ')
            await state.finish()
        else:
            async with state.proxy() as data:
                proceed_answer_id = data['proceed_answer_id']
                data['proceed_answer'] = message.text
            notification_id = clients_db.take_connect_notification(proceed_answer_id)
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=notification_id[0][3],
                                        text=notification_id[0][4])
            await proceed_admin(text=message.text, message_client=message,
                                last_connect=notification_id[0][2], admin_id=notification_id[0][1],
                                old_message_id=notification_id[0][3])
            await bot.send_message(message.from_user.id,
                                   'Ваш ответ был доставлен специалисту. В этом чате вы получите ответ\n'
                                   'Чтобы открыть меню, нажмите /start')
            await state.finish()
    else:
        media_group = types.MediaGroup()
        for obj in album:
            if obj.photo:
                file_id = obj.photo[-1].file_id
                caption = album[0].caption
            else:
                file_id = obj[obj.content_type].file_id
            try:
                media_group.attach({"media": file_id, "type": obj.content_type})
            except ValueError:
                return await message.answer("Данный тип коллажа не поддерживается.")
        async with state.proxy() as data:
            data['connect_message'] = media_group
            proceed_answer_id = data['proceed_answer_id']
            data['proceed_answer'] = caption
        notification_id = clients_db.take_connect_notification(proceed_answer_id)
        await proceed_admin_media(text=caption, message_client=message,
                                  last_connect=notification_id[0][2], admin_id=notification_id[0][1],
                                  old_message_id=notification_id[0][3], media=media_group)
        await state.finish()
        await bot.send_message(message.from_user.id,
                               'Ваш ответ был доставлен оператору.\n'
                               'Чтобы открыть меню, нажмите /start')


async def proceed_admin(text, message_client, last_connect, admin_id, old_message_id):
    problem = clients_db.take_name_problem(last_connect)
    admin = clients_db.take_admin_from_id(admin_id)
    take_id_message = await bot.send_message (chat_id=admin,
                                              text=f'Получен ответ от пользователя!\n'
                                                   f'Номер пользователя: '
                                                   f'+{clients_db.take_user_num(message_client.from_user.id)}\n'
                                                   f'Ссылка телеграм: @{message_client.chat.username}\n'
                                                   f'Жалоба: {problem}\n'
                                                   f'Текст обращения: \n\n{text}',
                                                   reply_markup=next_enter_connect_client)
    clients_db.change_notification_id_text(take_id_message.message_id, take_id_message.text, old_message_id)
    clients_db.create_new_table_user(message_client.from_user.id, last_connect, text)


async def proceed_admin_media(text, message_client, last_connect, admin_id, old_message_id, media=None):
    problem = clients_db.take_name_problem(last_connect)
    media_text = f'Получен ответ от пользователя!\n' \
                 f'Номер пользователя: ' \
                 f'+{clients_db.take_user_num(message_client.from_user.id)}\n' \
                 f'Ссылка телеграм: @{message_client.chat.username}\n' \
                 f'Жалоба: {problem}\n' \
                 f'Текст обращения: \n\n{text}'
    if not message_client.media_group_id:
        admin = clients_db.take_admin_from_id(admin_id)
        await bot.send_photo \
            (chat_id=admin,
             photo=message_client.photo[-1].file_id)
        take_id_message = await bot.send_message(chat_id=admin,
                                                 text=media_text,
                                                 reply_markup=next_enter_connect_client)
        clients_db.change_notification_id_text(take_id_message.message_id, take_id_message.text, old_message_id)
        clients_db.create_new_table_user\
            (message_client.from_user.id, last_connect, text, message_client.photo[-1].file_id)
    else:
        admin = clients_db.take_admin_from_id(admin_id)
        await bot.send_media_group \
            (chat_id=admin,
             media=media)
        take_id_message = await bot.send_message (chat_id=admin,
                                                  text=media_text,
                                                  reply_markup=next_enter_connect_client)
        clients_db.change_notification_id_text(take_id_message.message_id, take_id_message.text, old_message_id)
        clients_db.create_new_table_user(message_client.from_user.id, last_connect, text, media)


async def close_connect(message: types.Message):
    clients_db.close_connect(message.message.message_id)
    admin = clients_db.take_id_admin(message.message.message_id)
    notification_id = clients_db.take_connect_notification(message.message.message_id)
    problem = clients_db.take_name_problem(notification_id[0][2])
    history = clients_db.take_history_connect(message.from_user.id, notification_id[0][2])
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=notification_id[0][3],
                                text=f"Обращение закрыто! Спасибо что обратились к нам\n"
                                     f"{notification_id[0][4]}")
    await bot.send_message(chat_id=admin,
                           text=f"Обращение закрыто клиентом\n"
                                f"\n"
                                f'Номер пользователя: '
                                f'+{clients_db.take_user_num(message.from_user.id)}\n'
                                f'Ссылка телеграм: @{message.message.chat.username}\n'
                                f'Жалоба: {problem}\n'
                                f'Текст первого запроса: \n\n{history[0][2]}')


async def my_conn(message: types.Message):
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text=f'Выберите нужные вам обращения',
                                reply_markup=history_button)


async def open_hist(message: types.Message, state: FSMContext):
    if message.data == 'open_history':
        all_history = clients_db.take_history_account(message.from_user.id)
    if message.data == 'close_history':
        all_history = clients_db.take_history_account(message.from_user.id, 1)
    iteration = [0, all_history]
    if len(all_history) != 0:
        async with state.proxy() as data:
            data['move_id'] = iteration
            all_history = iteration[1]
            iteration = iteration[0]
        status = "Закрыто" if all_history[iteration][-1] == 1 else "Открыто"
        if len(all_history) == 1:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Обращение {iteration + 1} из {len(all_history)}\n'
                                             f'Статус: {status}\n'
                                             f'Тема вопроса: {all_history[iteration][3]}\n'
                                             f'Ваше обращение: \n{all_history[iteration][2]}',
                                        reply_markup=move_button_solo)
        else:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Обращение {iteration+1} из {len(all_history)}\n'
                                             f'Статус: {status}\n'
                                             f'Тема вопроса: {all_history[iteration][3]}\n'
                                             f'Ваше обращение: \n{all_history[iteration][2]}',
                                        reply_markup=move_button)
    elif len(all_history) == 0:
        if message.data == 'open_history':
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Открытых обращений нет',
                                        reply_markup=rooms)
        if message.data == 'close_history':
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Закрытых обращений нет',
                                        reply_markup=rooms)


async def move(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
        move_history = Move(iteration=iteration, button=move_button, button_error=rooms)
        await move_history.move_iteration(message, state)
    except Exception as e:
        print(f"Произошёл сбой в движении! Пользователь: {message.from_user.id}, ошибка: {e}")
        await state.finish()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Что-то пошло не так, начнём заново',
                                    reply_markup=rooms)


async def history_connect(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
        id_problem = iteration[1][iteration[0]]
        history = clients_db.take_history_connect(message.from_user.id, id_problem[0])
        history_iteration = clients_db.take_history_connect(message.from_user.id, id_problem[0])
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=message.message.text)
        for mess in history:
            del history_iteration[0]
            if not mess[-2]:
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f"Ваше обращение: \n"
                                            f"{mess[2]}")
                if mess[-1]:
                    if ',' in mess[-1]:
                        photo = json.loads(mess[-1])
                        media = types.MediaGroup()
                        for add_photo in photo:
                            media.attach_photo(types.InputMediaPhoto(add_photo))
                        await bot.send_media_group(chat_id=message.from_user.id, media=media)
                    else:
                        await bot.send_photo(chat_id=message.from_user.id, photo=mess[-1])
                if not history_iteration:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=message.message.text,
                                           reply_markup=move_button)

            else:
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f"Ответ оператора: \n"
                                            f"{mess[3]}")
                if mess[-1]:
                    if ',' in mess[-1]:
                        photo = json.loads(mess[-1])
                        media = types.MediaGroup()
                        for add_photo in photo:
                            media.attach_photo(types.InputMediaPhoto(add_photo))
                        await bot.send_media_group(chat_id=message.from_user.id, media=media)
                    else:
                        await bot.send_photo(chat_id=message.from_user.id, photo=mess[-1])
                if not history_iteration:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=message.message.text,
                                           reply_markup=move_button)

                if not history_iteration:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=message.message.text,
                                           reply_markup=move_button)
    except Exception as e:
        print(f'Ошибка при выводе истории пользователя. Функция "async def history_connect", ошибка {e}')
        await state.finish()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Что-то пошло не так, начнём заново',
                                    reply_markup=rooms)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'])

    dp.register_callback_query_handler(move, text='move_up', state=None)
    dp.register_callback_query_handler(move, text='move_down', state=None)
    dp.register_callback_query_handler(close_connect, text='close_client_connect')
    dp.register_callback_query_handler(my_conn, text='my_connect')
    dp.register_callback_query_handler(open_hist, text='open_history')
    dp.register_callback_query_handler(open_hist, text='close_history')
    dp.register_callback_query_handler(new_client, text='start_button', state=None)
    dp.register_callback_query_handler(history_connect, text='history')
    dp.register_callback_query_handler(new_start, text='back_all_room', state="*")
    dp.register_callback_query_handler(room_conn, text='room_connect')
    dp.register_callback_query_handler(back_room_client, text='back_connect', state="*")
    dp.register_callback_query_handler(proceed_answer_connect_admin, text='proceed_answer_connect_admin', state=None)
    dp.register_callback_query_handler(quit_account, text='quit')
    dp.register_callback_query_handler(enter_connect,
                                       text=['forgot', 'payment', 'ride',
                                             'connect_question', 'complaint', 'complaint_r_time',
                                             'offer', 'other'], state=None)

    # dp.register_message_handler(start_register, commands=['new'], state=None)
    #
    dp.register_message_handler(load_num_client, content_types=['text'], state=FSMClient.number)
    dp.register_message_handler(call_admin, content_types=['text', 'photo'], state=FSMClient.connect_message)
    dp.register_message_handler(proceed_answer, content_types=['text', 'photo'], state=FSMClient.proceed_answer)
    # dp.register_callback_query_handler(cansel_handler, text='back_all_room', state="*")
