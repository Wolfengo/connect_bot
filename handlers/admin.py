import asyncio
import aiogram
import logging
from aiogram import types, Dispatcher
from typing import List, Union
from create_bot import dp, bot, clients_db
from keyboards import buttons_connect, back_ans, next_enter_connect, next_enter_connect_client, \
    move_button_operator_non_answer, move_button_solo_open_operator, move_button_open_operator, \
    admin_button, back_ans_admin_button, admin_delete, admin_delete_solo, admin_send_history_operator, \
    admin_send_history_operator_solo, admin_history_operator, move_button_operator, \
    admin_change_notification_operator_solo, admin_change_notification_operator, admin_choice_history_operator_solo, \
    admin_choice_history_operator
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup


logging.basicConfig(level=logging.ERROR, filename="py_admin_log.log", filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")


async def test(message: types.Message):
    try:
        a = 1 / 0
        print(a)
    except Exception as e:
        print(e)
        # aiogram.utils.exceptions.MessageNotModified
        if 'division by zero' in str(e):
            print(f'Произошла ошибка при делении')
        else:
            logging.error(f"An ERROR - {e}", exc_info=True)


class FSMAdmin(StatesGroup):
    message_cl = State()
    message_admin = State()
    answer_admin = State()
    answer_message_id = State()
    edit_message_id = State()
    move_id = State()
    proceed_answer_id = State()
    add_new_operator = State()
    id_operator = State()
    name_operator = State()
    number_operator = State()
    move_id = State()
    key_operator = State()
    history_operator = State()


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
            all_info = self.iteration[1]
            iteration = self.iteration[0]
            if message.data == 'move_up_operator_delete' \
                    or message.data == 'move_history_up_operator' \
                    or message.data == 'move_notification_up_operator' \
                    or message.data == 'move_choice_up_operator':
                if iteration >= len(all_info) - 1:
                    iteration = 0
                else:
                    iteration += 1
            elif message.data == 'move_down_operator_delete' \
                    or message.data == 'move_history_down_operator' \
                    or message.data == 'move_notification_down_operator' \
                    or message.data == 'move_choice_down_operator':
                if iteration == 0:
                    iteration = len(all_info) - 1
                else:
                    iteration -= 1
            self.iteration_move = iteration
            await Move.move_button_object(self, message, state)
        except Exception as e:
            print(f'Произошёл сбой в движении! Пользователь: {message.from_user.id}, '
                  f'ошибка: {e}, '
                  f'функция "class Move.move_iteration"')
            await state.finish()
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text='Что-то пошло не так, начнём заново',
                                        reply_markup=self.button_error)

    async def move_button_object(self, message: types.Message, state: FSMContext):
        all_info = self.iteration[1]
        iteration = self.iteration_move
        text = f'Оператор {iteration + 1} из {len(all_info)}\n' \
               f'ID телеграм админа: {all_info[iteration][1]}\n' \
               f'Номер телефона/ключ: {all_info[iteration][4]}\n' \
               f'Имя админа: {all_info[iteration][3]}\n' \
               f'Уведомления: {"ДА" if all_info[iteration][-1] == 1 else "НЕТ"}\n'
        if self.button == admin_send_history_operator or self.button == admin_send_history_operator_solo:
            status = "Закрыто" if all_info[iteration][-1] == 1 else "Открыто"
            text = f'Обращение {iteration + 1} из {len(all_info)}\n' \
                   f'Статус: {status}\n' \
                   f'Тема вопроса: {all_info[iteration][3]}\n' \
                   f'Начальная жалоба: \n{all_info[iteration][2]}'
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=text,
                                    reply_markup=self.button)
        iteration = [iteration, all_info]
        async with state.proxy() as data:
            data['move_id'] = iteration


async def admin(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id,
                           text='Пожалуйста, выберите нужную вам категорию',
                           reply_markup=admin_button)


async def my_id(message: types.Message):
    await bot.send_message(message.from_user.id, f'{message.from_user.id}')


async def answer_cl(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['answer_message_id'] = message.message.message_id
        await FSMAdmin.message_admin.set()
        edit_message_id = await bot.edit_message_text(chat_id=message.from_user.id,
                                                      message_id=message.message.message_id,
                                                      text=f'Введите ответ в одном сообщении. \n'
                                                           f'Фото присылайте одним сообщением с комментарием к нему',
                                                      reply_markup=back_ans)
        data['edit_message_id'] = edit_message_id


async def back_answer(message: types.Message, state: FSMContext):
    try:
        try:
            async with state.proxy() as data:
                answer_message_id = data['answer_message_id']
            notification_id = clients_db.take_connect_notification(answer_message_id)
            await state.finish()
            for notification in notification_id:
                if notification[4][0] == 'С':
                    admin_id = clients_db.take_admin_from_id(notification[1])
                    await bot.edit_message_text(chat_id=admin_id,
                                                message_id=notification[3],
                                                text=notification[4],
                                                reply_markup=buttons_connect)
                elif notification[4][0] == 'П':
                    admin_id = clients_db.take_admin_from_id(notification[1])
                    await bot.edit_message_text(chat_id=admin_id,
                                                message_id=notification[3],
                                                text=notification[4],
                                                reply_markup=next_enter_connect_client)
        except IndexError:
            async with state.proxy() as data:
                iteration = data['move_id']
                need_info = iteration[1][iteration[0]]
                if need_info[-2] is not None:
                    if len(iteration[1]) == 1:
                        button = move_button_solo_open_operator
                    else:
                        button = move_button_open_operator
                else:
                    button = move_button_operator_non_answer
                await bot.edit_message_text(chat_id=message.from_user.id,
                                            message_id=message.message.message_id,
                                            text=f'Обращение {iteration[0] + 1} из {len(iteration[1])}\n'
                                                 f'\n'
                                                 f'Тема вопроса: {need_info[3]}\n'
                                                 f'Текст клиента: \n{need_info[2]}',
                                            reply_markup=button)
            await state.finish()
            async with state.proxy() as data:
                data['move_id'] = iteration
    except:
        async with state.proxy() as data:
            answer_message_id = data['proceed_answer_id']
        notification_id = clients_db.take_connect_notification(answer_message_id)
        await state.finish()
        for notification in notification_id:
            admin_id = clients_db.take_admin_from_id(notification[1])
            await bot.edit_message_text(chat_id=admin_id,
                                        message_id=notification[3],
                                        text=notification[4],
                                        reply_markup=next_enter_connect)


async def conn_cl(message: types.Message, state: FSMContext, album: List[types.Message]):
    try:
        async with state.proxy() as data:
            edit_message_id = data['edit_message_id']
            try:
                await bot.edit_message_text(chat_id=message.from_user.id,
                                            message_id=edit_message_id.message_id,
                                            text=edit_message_id.text)
            except Exception as e:
                print(f'Сообщение уже было изменено! - {e}'
                      f'Функция "def conn_cl"')

        if not message.media_group_id:
            async with state.proxy() as data:
                data['message_admin'] = message.text
                answer_message_id = data['answer_message_id']
            try:
                notification_id = clients_db.take_connect_notification(answer_message_id)
            except IndexError:
                async with state.proxy() as data:
                    iteration = data['move_id']
                need_info = iteration[1][iteration[0]]
                message_id = clients_db.take_message_id_from_problem(need_info[0])
                notification_id = clients_db.take_connect_notification(message_id[0][3])
            for notification in notification_id:
                admin_id = clients_db.take_admin_from_id(notification[1])
                try:
                    await bot.edit_message_text(chat_id=admin_id,
                                                message_id=notification[3],
                                                text=notification[4])
                except Exception as e:
                    print(f'При скрытии кнопок у всех операторов произошла ошибка у оператора {admin_id} - ошибка {e} '
                          f'функция: def conn_cl')
            try:
                if not clients_db.answer_exists(answer_message_id):
                    clients_db.give_id_admin_for_connect(answer_message_id)
                    await enter_client(message, answer_message_id)
                    await state.finish()
                else:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=f'Другой оператор уже ответил на этот запрос. '
                                                f'Клиент передан администратору, ответившему первым')
                    await state.finish()
            except IndexError:
                if not clients_db.answer_exists(message_id[0][3]):
                    clients_db.give_id_admin_for_connect(message_id[0][3])
                    await enter_client(message, message_id[0][3])
                    await state.finish()
                else:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=f'Другой оператор уже ответил на этот запрос. '
                                                f'Клиент передан администратору, ответившему первым')
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
                answer_message_id = data['answer_message_id']
            try:
                if not clients_db.answer_exists(answer_message_id):
                    clients_db.give_id_admin_for_connect(answer_message_id)
                    await enter_client_media(message, answer_message_id, media_group, caption)
                    await state.finish()
                else:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=f'Другой администратор уже ответил на этот запрос. '
                                                f'Клиент передан администратору, ответившему первым')
                    await state.finish()
            except IndexError:
                async with state.proxy() as data:
                    iteration = data['move_id']
                need_info = iteration[1][iteration[0]]
                message_id = clients_db.take_message_id_from_problem(need_info[0])
                if not clients_db.answer_exists(message_id[0][3]):
                    clients_db.give_id_admin_for_connect(message_id[0][3])
                    await enter_client_media(message, message_id[0][3], media_group, caption)
                    await state.finish()
                else:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=f'Другой администратор уже ответил на этот запрос. '
                                                f'Клиент передан администратору, ответившему первым')
                    await state.finish()
    except Exception as e:
        logging.exception()


async def enter_client(message, message_id):
    name_admin = clients_db.take_admin_r_name(message_id)
    client_id = clients_db.take_user_id_in_notification(message_id)

    if not message.photo:
        try:
            new_id_message = await bot.send_message(chat_id=client_id,
                                                    text=f'С вами общается {name_admin}:\n'
                                                         f'{message.text}',
                                                    reply_markup=next_enter_connect)
            clients_db.add_answer_table_user(id_user=client_id, answer_admin=message.text, message_id=message_id)
            clients_db.change_notification_id_text(new_id_message.message_id, new_id_message.text, message_id)
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f'Ответ был доставлен клиенту')
        except aiogram.utils.exceptions.BotBlocked:
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f'Возможно, клиент заблокировал бота. Сообщение не было отправлено!')
    else:
        try:
            await bot.send_photo(chat_id=client_id,
                                 photo=message.photo[-1].file_id, )
            new_id_message = await bot.send_message(chat_id=client_id,
                                                    text=f'С вами общается {name_admin}:\n'
                                                         f'{message.caption}',
                                                    reply_markup=next_enter_connect)
            clients_db.add_answer_table_user(id_user=client_id, answer_admin=message.text, message_id=message_id)
            clients_db.change_notification_id_text(new_id_message.message_id, new_id_message.text, message_id)
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f'Ответ был доставлен клиенту')
        except aiogram.utils.exceptions.BotBlocked:
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f'Возможно, клиент заблокировал бота. Сообщение не было доставлено!')


async def enter_client_media(message, message_id, media, caption):
    name_admin = clients_db.take_admin_r_name(message_id)
    text = f'С вами общается {name_admin}:\n' \
           f'{caption}'
    client_id = clients_db.take_user_id_in_notification(message_id)
    if not message.media_group_id and not message.photo:
        clients_db.add_answer_table_user(id_user=client_id, answer_admin=message.text, message_id=message_id)
    else:
        try:
            await bot.send_media_group \
                (chat_id=client_id,
                 media=media)
            new_id_message = await bot.send_message(chat_id=client_id,
                                                    text=text,
                                                    reply_markup=next_enter_connect)
            clients_db.add_answer_table_user(id_user=client_id,
                                             answer_admin=message.text,
                                             message_id=message_id,
                                             photo=media)
            clients_db.change_notification_id_text(new_id_message.message_id, new_id_message.text, message_id)
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f'Ответ был доставлен клиенту')
        except aiogram.utils.exceptions.BotBlocked:
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f'Возможно, клиент заблокировал бота. Сообщение не было отправлено!')


async def proceed_answer_connect_client(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['answer_message_id'] = message.message.message_id
        await FSMAdmin.answer_admin.set()
        elit_message = await bot.edit_message_text(chat_id=message.from_user.id,
                                                   message_id=message.message.message_id,
                                                   text=f'Введите ответ в одном сообщении',
                                                   reply_markup=back_ans)
        data['edit_message_id'] = elit_message


async def next_conn_cl(message: types.Message, state: FSMContext, album: List[types.Message]):
    if not message.media_group_id:
        try:
            async with state.proxy() as data:
                data['message_admin'] = message.text
                answer_message_id = data['answer_message_id']
                elit_message = data['edit_message_id']
            notification_id = clients_db.take_connect_notification(answer_message_id)
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=elit_message.message_id,
                                        text=elit_message.text)
            await enter_client(message, answer_message_id)
        except IndexError:
            async with state.proxy() as data:
                iteration = data['move_id']
                elit_message = data['edit_message_id']
            need_info = iteration[1][iteration[0]]
            notification_id = clients_db.take_message_id_from_problem(need_info[0])
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=elit_message.message_id,
                                        text=elit_message.text)
            await enter_client(message, notification_id[0][3])
        for notification in notification_id:
            admin_id = clients_db.take_admin_from_id(notification[1])
            try:
                await bot.edit_message_text(chat_id=admin_id,
                                            message_id=notification[3],
                                            text=notification[4])
            except aiogram.utils.exceptions.MessageNotModified:
                pass
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
        try:
            async with state.proxy() as data:
                data['connect_message'] = media_group
                answer_message_id = data['answer_message_id']
            await enter_client_media(message, answer_message_id, media_group, caption)
        except IndexError:
            async with state.proxy() as data:
                iteration = data['move_id']
            need_info = iteration[1][iteration[0]]
            message_id = clients_db.take_message_id_from_problem(need_info[0])
            clients_db.give_id_admin_for_connect(message_id[0][3])
            await enter_client_media(message, message_id[0][3], media_group, caption)
        await state.finish()


async def close_connect_admin(message: types.Message):
    clients_db.close_connect(message.message.message_id)
    user = clients_db.take_user_id_from_message_id(message.message.message_id)
    notification_id = clients_db.take_connect_notification(message.message.message_id)
    problem = clients_db.take_name_problem(notification_id[0][2])
    history = clients_db.take_history_connect(user, notification_id[0][2])
    for admin_message_edit in notification_id:
        admin_id = clients_db.take_admin_from_id(admin_message_edit[1])
        await bot.edit_message_text(chat_id=admin_id,
                                    message_id=notification_id[0][3],
                                    text=f"Обращение закрыто! Клиент был уведомлен\n"
                                         f"\n"
                                         f"{notification_id[0][4]}")
    await bot.send_message(chat_id=user,
                           text=f"Обращение закрыто администратором\n"
                                f"\n"
                                f'Жалоба: {problem}\n'
                                f'Текст первого запроса: \n\n{history[0][2]}')


async def add_new_operator(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        edit_message = await bot.edit_message_text(chat_id=message.from_user.id,
                                                   message_id=message.message.message_id,
                                                   text=f"Введите id телеграмм оператора. \n"
                                                        f"Будущий оператор может посмотреть "
                                                        f"его можно через команду /my_id "
                                                        f"(если оператор вы - нажмите на эту команду)",
                                                   reply_markup=back_ans_admin_button)
        data['edit_message_id'] = edit_message
    await FSMAdmin.id_operator.set()


async def add_id_operator(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.isdigit() or '/my_id' in message.text:
            edit_message = data['edit_message_id']
            if message.text == '/my_id':
                data['id_operator'] = message.from_user.id
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f'Ваш ID был взят - {message.from_user.id}',)
            else:
                data['id_operator'] = message.text
            await FSMAdmin.name_operator.set()
            try:
                await bot.edit_message_text(chat_id=message.from_user.id,
                                            message_id=edit_message.message_id,
                                            text=edit_message.text, )
            except Exception as e:
                print(f'Сообщение уже было изменено! - {e} '
                      f'Функция "def add_id_operator 1"')
            edit_message = await bot.send_message(chat_id=message.from_user.id,
                                                  text='Введите имя оператора, оно будет указано клиенту',
                                                  reply_markup=back_ans_admin_button, )
            data['edit_message_id'] = edit_message
        else:
            if '/' in message.text:
                edit_message = data['edit_message_id']
                try:
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=edit_message.message_id,
                                                text=edit_message.text, )
                except Exception as e:
                    print(f'Сообщение уже было изменено! - {e}'
                          f'Функция "def add_id_operator 2"')
                await state.finish()
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f'Я ожидал ID, но, видимо, вам нужна другая команда! Введите её снова!')
            else:
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f'Вводите цифры')


async def add_name_operator(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        edit_message = data['edit_message_id']
        data['name_operator'] = message.text
        await FSMAdmin.number_operator.set()
        try:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=edit_message.message_id,
                                        text=edit_message.text, )
        except Exception as e:
            print(f'Сообщение уже было изменено! - {e}'
                  f'Функция "def add_name_operator"')
        edit_message = await bot.send_message(chat_id=message.from_user.id,
                                              text='Введите номер телефона, '
                                                   'или ключ оператора, для доступа к его информации',
                                              reply_markup=back_ans_admin_button, )
        data['edit_message_id'] = edit_message


async def add_phone_operator(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            if message.text.isdigit():
                edit_message = data['edit_message_id']
                try:
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=edit_message.message_id,
                                                text=edit_message.text, )
                except Exception as e:
                    print(f'Сообщение уже было изменено! - {e}'
                          f'Функция "def add_phone_operator"')
                all_admins = clients_db.take_all_operator()
                for admins in all_admins:
                    if str(admins[1]) == str(data['id_operator']):
                        print(1)
                        if admins[2] == 1:
                            clients_db.add_deleted_operator(data['id_operator'], data['name_operator'], message.text)
                            await bot.send_message(chat_id=message.from_user.id,
                                                   text='Данные перезаписаны, оператор был восстановлен! \n'
                                                        'Для открытия меню нажмите /admin', )
                            await state.finish()
                            return
                        else:
                            await bot.send_message(chat_id=message.from_user.id,
                                                   text='Данный оператор уже существует '
                                                        'и не является удалённым - сброс! \n'
                                                        'Для открытия меню нажмите /admin', )
                            await state.finish()
                            return
                clients_db.add_operator(data['id_operator'], data['name_operator'], message.text)
                await bot.send_message(chat_id=message.from_user.id,
                                       text='Данные записаны, оператор добавлен. Для открытия меню нажмите /admin', )

                await state.finish()
            else:
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f'Вводите цифры')
        except Exception as e:
            print(f"Ошибка сохранения данных нового оператора, ошибка: {e}, функция: add_phone_operator")
            await FSMAdmin.number_operator.set()
            edit_message = await bot.send_message(chat_id=message.from_user.id,
                                                  text=f'Ошибка сохранения данных нового оператора, '
                                                       f'возможно, такой ключ или номер уже используется\n'
                                                       f'\n'
                                                       f'Введите ключ/номер оператора снова, '
                                                       f'или пройдите регистрацию заново',
                                                  reply_markup=back_ans_admin_button, )
            data['edit_message_id'] = edit_message


async def back_menu_admin(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text="Пожалуйста, выберите нужную вам категорию",
                                reply_markup=admin_button)


async def delete_operator_or_notification(message: types.Message, state: FSMContext):
    if message.data == "send_history_operator":
        all_admin = clients_db.take_all_operator()
    else:
        all_admin = clients_db.take_all_operator_non_delete()
    iteration = [0, all_admin]
    if len(all_admin) != 0:
        async with state.proxy() as data:
            data['move_id'] = iteration
            all_admin = iteration[1]
            iteration = iteration[0]
        if len(all_admin) == 1:
            if message.data == 'del_operator':
                button = admin_delete_solo
            elif message.data == 'notification':
                button = admin_change_notification_operator_solo
            elif message.data == 'send_history_operator':
                button = admin_choice_history_operator_solo

            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Оператор {iteration + 1} из {len(all_admin)}\n'
                                             f'ID телеграм админа: {all_admin[iteration][1]}\n'
                                             f'Статус: {"Удалён" if all_admin[iteration][2] == 1 else "Активен"}\n'
                                             f'Ключ/номер оператора: {all_admin[iteration][4]}\n'
                                             f'Имя админа: {all_admin[iteration][3]}\n'
                                             f'Уведомления: {"ДА" if all_admin[iteration][-1] == 1 else "НЕТ"}\n',
                                        reply_markup=button)
        else:
            if message.data == 'del_operator':
                button = admin_delete
            elif message.data == 'notification':
                button = admin_change_notification_operator
            elif message.data == 'send_history_operator':
                button = admin_choice_history_operator
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Оператор {iteration + 1} из {len(all_admin)}\n'
                                             f'ID телеграм админа: {all_admin[iteration][1]}\n'
                                             f'Статус: {"Удалён" if all_admin[iteration][2] == 1 else "Активен"}\n'
                                             f'Ключ/номер оператора: {all_admin[iteration][4]}\n'
                                             f'Имя админа: {all_admin[iteration][3]}\n'
                                             f'Уведомления: {"ДА" if all_admin[iteration][-1] == 1 else "НЕТ"}\n',
                                        reply_markup=button)
    elif len(all_admin) == 0:
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=f'Операторы отсутствуют',
                                    reply_markup=admin_button)


async def move_admin_delete(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
        all_admin = iteration[1]
        button = admin_delete if len(all_admin) != 1 else admin_delete_solo
        move_history = Move(iteration=iteration, button=button, button_error=admin_button)
        await move_history.move_iteration(message, state)
    except Exception as e:
        print(f'Произошёл сбой в движении! Пользователь: {message.from_user.id}, '
              f'ошибка: {e}, '
              f'функция "def move_admin_delete"')
        await state.finish()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Что-то пошло не так, начнём заново',
                                    reply_markup=admin_button)


async def admin_delete_operator(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        iteration = data['move_id']
    all_admin = iteration[1]
    iteration = iteration[0]
    print(all_admin[iteration][1])
    clients_db.del_operator(all_admin[iteration][1])
    if len(all_admin) == 1:
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=f'ВНИМАНИЕ! ВСЕ ОПЕРАТОРЫ УДАЛЕНЫ!\n'
                                         f'\n'
                                         f'ID телеграм админа: {all_admin[iteration][1]}\n'
                                         f'Номер телефона/ключ: {all_admin[iteration][4]}\n'
                                         f'Имя админа: {all_admin[iteration][3]}\n'
                                         f'Уведомления: {"ДА" if all_admin[iteration][-1] == 1 else "НЕТ"}\n',
                                    reply_markup=admin_button)
        await state.finish()
    else:
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=f'Оператор был удалён!\n'
                                         f'\n'
                                         f'ID телеграм админа: {all_admin[iteration][1]}\n'
                                         f'Номер телефона/ключ: {all_admin[iteration][4]}\n'
                                         f'Имя админа: {all_admin[iteration][3]}\n'
                                         f'Уведомления: {"ДА" if all_admin[iteration][-1] == 1 else "НЕТ"}\n',
                                    reply_markup=admin_delete)
    del all_admin[iteration]
    iteration = [iteration, all_admin]
    async with state.proxy() as data:
        data['move_id'] = iteration


async def key_operator_notification(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        iteration = data['move_id']
        all_admin = iteration[1]
        iteration_move = iteration[0]
        button = admin_change_notification_operator_solo if len(all_admin) == 1 else admin_change_notification_operator
        clients_db.add_operator_notification(all_admin[iteration_move][-2])
        all_admin = clients_db.take_all_operator()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=f'Оператор {iteration_move + 1} из {len(all_admin)}\n'
                                         f'ID телеграм админа: {all_admin[iteration_move][1]}\n'
                                         f'Номер телефона/ключ: {all_admin[iteration_move][-2]}\n'
                                         f'Имя админа: {all_admin[iteration_move][3]}\n'
                                         f'Уведомления: {"ДА" if all_admin[iteration_move][-1] == 1 else "НЕТ"}\n',
                                    reply_markup=button)
        iteration = [iteration_move, all_admin]
        data['move_id'] = iteration


async def history_operator(message: types.Message, state: FSMContext):
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text='Выберите интересующие вас обращения',
                                reply_markup=admin_history_operator)


async def open_history_operator(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        iteration = data['move_id']
        info_operator = iteration[1][iteration[0]]
        key_operator = info_operator[-2]
        all_admin = clients_db.take_all_operator()
        if message.data == 'admin_open_history_operator':
            for take_admin in all_admin:
                if str(key_operator) == str(take_admin[-2]):
                    all_history = clients_db.take_history_operator(take_admin[1])
                    data['history_operator'] = take_admin[1]

        if message.data == 'admin_close_history_operator':
            for take_admin in all_admin:
                if str(key_operator) == str(take_admin[-2]):
                    all_history = clients_db.take_history_operator(take_admin[1], 1)
                    data['history_operator'] = take_admin[1]

        iteration = [0, all_history]
        if len(all_history) != 0:
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
                                                 f'Начальная жалоба: \n{all_history[iteration][2]}',
                                            reply_markup=admin_send_history_operator_solo)
            else:
                await bot.edit_message_text(chat_id=message.from_user.id,
                                            message_id=message.message.message_id,
                                            text=f'Обращение {iteration + 1} из {len(all_history)}\n'
                                                 f'Статус: {status}\n'
                                                 f'Тема вопроса: {all_history[iteration][3]}\n'
                                                 f'Начальная жалоба: \n{all_history[iteration][2]}',
                                            reply_markup=admin_send_history_operator)
        elif len(all_history) == 0:
            if message.data == 'admin_open_history_operator':
                await bot.edit_message_text(chat_id=message.from_user.id,
                                            message_id=message.message.message_id,
                                            text=f'Открытых обращений нет',
                                            reply_markup=admin_button)
            if message.data == 'admin_close_history_operator':
                await bot.edit_message_text(chat_id=message.from_user.id,
                                            message_id=message.message.message_id,
                                            text=f'Закрытых обращений нет',
                                            reply_markup=admin_button)


async def take_history_operator(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
            operator_id = data['history_operator']
        id_problem = iteration[1][iteration[0]]
        history = clients_db.take_history_connect_operator(id_problem[1], id_problem[0])
        history_iteration = clients_db.take_history_connect_operator(id_problem[1], id_problem[0])
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=message.message.text)
        button = admin_send_history_operator if len(iteration[1]) != 1 else admin_send_history_operator_solo
        for mess in history:
            del history_iteration[0]
            if not mess[-2]:
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f"Вопрос клиента: \n"
                                            f"{mess[2]}")
                if not history_iteration:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=message.message.text,
                                           reply_markup=button)

            else:
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f"Ваш ответ: \n"
                                            f"{mess[3]}")
                if not history_iteration:
                    await bot.send_message(chat_id=message.from_user.id,
                                           text=message.message.text,
                                           reply_markup=button)
    except:
        await state.finish()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Что-то пошло не так, начнём заново',
                                    reply_markup=admin_button)


async def move_history_operator(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
        all_info = iteration[1]
        button = admin_send_history_operator if len(all_info) != 1 else admin_send_history_operator_solo
        move_history = Move(iteration=iteration, button=button, button_error=admin_button)
        await move_history.move_iteration(message, state)
    except Exception as e:
        print(f'Произошёл сбой в движении! Пользователь: {message.from_user.id} @{message.from_user.username}, '
              f'ошибка: {e}, '
              f'функция "def move_history_operator"')
        await state.finish()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Что-то пошло не так, начнём заново',
                                    reply_markup=admin_button)


async def all_move(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
        all_info = iteration[1]
        if message.data == 'move_down_operator_delete' or message.data == 'move_up_operator_delete':
            button = admin_delete if len(all_info) != 1 else admin_delete_solo
        elif message.data == 'move_history_down_operator' or message.data == 'move_history_up_operator':
            button = admin_send_history_operator if len(all_info) != 1 else admin_send_history_operator_solo
        elif message.data == 'move_notification_down_operator' or message.data == 'move_notification_up_operator':
            button = \
                admin_change_notification_operator if len(all_info) != 1 else admin_change_notification_operator_solo
        elif message.data == 'move_choice_down_operator' or message.data == 'move_choice_up_operator':
            button = admin_choice_history_operator if len(all_info) != 1 else admin_choice_history_operator_solo
        move_history = Move(iteration=iteration, button=button, button_error=admin_button)
        await move_history.move_iteration(message, state)
    except Exception as e:
        print(f'Произошёл сбой в движении! Пользователь: {message.from_user.id}, '
              f'ошибка: {e}, '
              f'функция "def all_move"')
        await state.finish()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Что-то пошло не так, начнём заново',
                                    reply_markup=admin_button)


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(admin, commands=['admin'])
    dp.register_message_handler(my_id, commands=['my_id'])
    dp.register_message_handler(test, commands=['test'])

    dp.register_callback_query_handler(back_answer, text='back_answer', state="*")
    dp.register_callback_query_handler(add_new_operator, text='add_new_operator', state=None)
    dp.register_callback_query_handler(answer_cl, text='answer_cl', state=None)
    dp.register_callback_query_handler(proceed_answer_connect_client, text='proceed_answer_connect_client', state=None)
    dp.register_callback_query_handler(close_connect_admin, text='close_admin_connect')
    dp.register_callback_query_handler(back_menu_admin, text='back_menu_admin', state='*')
    dp.register_callback_query_handler(admin_delete_operator, text='operator_delete')
    dp.register_callback_query_handler(delete_operator_or_notification, text=['del_operator',
                                                                              'notification',
                                                                              'send_history_operator'])
    dp.register_callback_query_handler(history_operator, text='choice_history_operator',)
    dp.register_callback_query_handler(open_history_operator, text=['admin_open_history_operator',
                                                                    'admin_close_history_operator'])
    dp.register_callback_query_handler(take_history_operator, text='take_history_operator')
    dp.register_callback_query_handler(key_operator_notification, text='change_notification_operator')
    dp.register_callback_query_handler(all_move, text=['move_history_down_operator',
                                                       'move_history_up_operator',
                                                       'move_down_operator_delete',
                                                       'move_up_operator_delete',
                                                       'move_notification_up_operator',
                                                       'move_notification_down_operator',
                                                       'move_choice_up_operator',
                                                       'move_choice_down_operator'])

    dp.register_message_handler(conn_cl, content_types=['text', 'photo'], state=FSMAdmin.message_admin)
    dp.register_message_handler(next_conn_cl, content_types=['text', 'photo'], state=FSMAdmin.answer_admin)
    dp.register_message_handler(add_id_operator, content_types=['text'], state=FSMAdmin.id_operator)
    dp.register_message_handler(add_name_operator, content_types=['text'], state=FSMAdmin.name_operator)
    dp.register_message_handler(add_phone_operator, content_types=['text'], state=FSMAdmin.number_operator)
    # dp.register_message_handler(send_history_operator, content_types=['text'], state=FSMAdmin.history_operator)
