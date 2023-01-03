import asyncio
import aiogram
import logging
from aiogram import types, Dispatcher
from typing import List, Union
from create_bot import dp, bot, clients_db
from keyboards import button_operator, history_button_operator, move_button_operator, move_button_solo_operator, \
    move_button_solo_operator_non_answer, move_button_operator_non_answer, move_button_solo_operator_close_answer, \
    move_button_open_operator, move_button_solo_open_operator
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup


logging.basicConfig(level=logging.ERROR, filename="py_other_log.log", filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")


class FSMAdmin(StatesGroup):
    message_cl = State()
    move_id = State()


async def test(message: types.Message):
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message_id,
                                text=message.text)


async def operator(message: types.Message):

    if clients_db.admin_exists(message.from_user.id):
        await bot.send_message(chat_id=message.from_user.id,
                               text='Пожалуйста, выберите нужную вам категорию',
                               reply_markup=button_operator)


async def open_hist(message: types.Message, state: FSMContext):
    if message.data == 'open_history_operator':
        all_history = clients_db.take_history_operator(message.from_user.id)
        button = move_button_open_operator
    if message.data == 'close_history_operator':
        all_history = clients_db.take_history_operator(message.from_user.id, 1)
        button = move_button_operator
    iteration = [0, all_history]
    if len(all_history) != 0:
        async with state.proxy() as data:
            data['move_id'] = iteration
            all_history = iteration[1]
            iteration = iteration[0]
        status = "Закрыто" if all_history[iteration][-1] == 1 else "Открыто"
        if len(all_history) == 1:
            button = move_button_solo_open_operator if status == "Открыто" else move_button_solo_operator
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Обращение {iteration + 1} из {len(all_history)}\n'
                                             f'Статус: {status}\n'
                                             f'Тема вопроса: {all_history[iteration][3]}\n'
                                             f'Начальная жалоба: \n{all_history[iteration][2]}',
                                        reply_markup=button)
        else:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Обращение {iteration+1} из {len(all_history)}\n'
                                             f'Статус: {status}\n'
                                             f'Тема вопроса: {all_history[iteration][3]}\n'
                                             f'Начальная жалоба: \n{all_history[iteration][2]}',
                                        reply_markup=button)
    elif len(all_history) == 0:
        if message.data == 'open_history_operator':
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Открытых обращений нет',
                                        reply_markup=button_operator)
        if message.data == 'close_history_operator':
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Закрытых обращений нет',
                                        reply_markup=button_operator)


async def my_conn_operator(message: types.Message):
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text=f'Выберите нужные вам обращения',
                                reply_markup=history_button_operator)


async def back_connect(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=message.message.message_id,
                                text='Пожалуйста, выберите нужную вам категорию',
                                reply_markup=button_operator)


async def history_operator(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
        id_problem = iteration[1][iteration[0]]
        button = move_button_open_operator if id_problem[-1] is None else move_button_operator
        history = clients_db.take_history_connect_operator(id_problem[1], id_problem[0])
        history_iteration = clients_db.take_history_connect_operator(id_problem[1], id_problem[0])
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=message.message.text)
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
                                    reply_markup=button_operator)


async def move_operator(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
        all_history = iteration[1]
        iteration = iteration[0]
        if message.data == 'move_up_operator':
            if iteration >= len(all_history) - 1:
                iteration = 0
            else:
                iteration += 1
        elif message.data == 'move_down_operator':
            if iteration == 0:
                iteration = len(all_history) - 1
            else:
                iteration -= 1
        # iteration += 1 if message.data == 'move_up' else iteration
        status = "Закрыто" if all_history[iteration][-1] == 1 else "Открыто"
        if status == "Открыто":
            button = move_button_open_operator
        else:
            button = move_button_operator
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=f'Обращение {iteration + 1} из {len(all_history)}\n'
                                         f'Статус: {status}\n'
                                         f'Тема вопроса: {all_history[iteration][3]}\n'
                                         f'Начальная жалоба: \n{all_history[iteration][2]}',
                                    reply_markup=button)
        iteration = [iteration, all_history]
        async with state.proxy() as data:
            data['move_id'] = iteration
    except:
        await state.finish()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Что-то пошло не так, начнём заново',
                                    reply_markup=button_operator)


async def answer_operator(message: types.Message, state: FSMContext):
    all_history = clients_db.take_non_answer_question()
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
                                             f'Начальная жалоба: \n{all_history[iteration][2]}',
                                        reply_markup=move_button_solo_operator_non_answer)
        else:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message.message.message_id,
                                        text=f'Обращение {iteration+1} из {len(all_history)}\n'
                                             f'Статус: {status}\n'
                                             f'Тема вопроса: {all_history[iteration][3]}\n'
                                             f'Начальная жалоба: \n{all_history[iteration][2]}',
                                        reply_markup=move_button_operator_non_answer)
    elif len(all_history) == 0:
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=f'Неотвеченных обращений нет',
                                    reply_markup=button_operator)


async def move_non_answer(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            iteration = data['move_id']
        all_history = iteration[1]
        iteration = iteration[0]
        if message.data == 'move_up_operator_non_answer':
            if iteration >= len(all_history) - 1:
                iteration = 0
            else:
                iteration += 1
        elif message.data == 'move_down_operator_non_answer':
            if iteration == 0:
                iteration = len(all_history) - 1
            else:
                iteration -= 1
        status = "Закрыто" if all_history[iteration][-1] == 1 else "Открыто"
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=f'Обращение {iteration + 1} из {len(all_history)}\n'
                                         f'Статус: {status}\n'
                                         f'Тема вопроса: {all_history[iteration][3]}\n'
                                         f'Начальная жалоба: \n{all_history[iteration][2]}',
                                    reply_markup=move_button_operator_non_answer)
        iteration = [iteration, all_history]
        async with state.proxy() as data:
            data['move_id'] = iteration
    except:
        await state.finish()
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text='Что-то пошло не так, начнём заново',
                                    reply_markup=button_operator)


async def close_connect_non_answer(message: types.Message, state: FSMContext):
    # try:
        async with state.proxy() as data:
            iteration = data['move_id']
        need_info = iteration[1][iteration[0]]
        print(iteration[1][iteration[0]])
        message_id_text = clients_db.take_message_id_from_problem(need_info[0])
        print(message_id_text)
        print(message.message.message_id)
        user = clients_db.take_user_id_from_problem(need_info[0])
        try:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=message_id_text[0][3],
                                        text=f"Обращение закрыто! Клиент был уведомлен\n"
                                             f"\n"
                                             f"{message_id_text[0][-1]}")
        except aiogram.utils.exceptions.MessageNotModified:
            pass
        '''Убирать кнопку у всех операторов, при закрытии'''
        print(123)
        await bot.edit_message_text(chat_id=message.from_user.id,
                                    message_id=message.message.message_id,
                                    text=f"Обращение закрыто оператором {message.from_user.id}! Клиент был уведомлен\n"
                                         f"\n"
                                         f"{message.message.text}")
        print(321)
        clients_db.close_connect(message_id_text[0][3])
        await bot.send_message(chat_id=user,
                               text=f"Обращение закрыто администратором\n"
                                    f"\n"
                                    f'Жалоба: {need_info[3]}\n'
                                    f'Начальная жалоба: \n\n{need_info[2]}')
        iteration[1].remove(need_info)
        iteration[0] = 0
        need_info = iteration[1][iteration[0]]
        await bot.send_message(chat_id=message.from_user.id,
                               text=f'Обращение {iteration[0]+1} из {len(iteration[1])}\n'
                                    f'\n'
                                    f'Тема вопроса: {need_info[3]}\n'
                                    f'Начальная жалоба: \n{need_info[2]}',
                               reply_markup=move_button_operator_non_answer)
    # except Exception as e:
    #     print(f'Произошла ошибка во время закрытия обращения оператором! - {e}')
    #     await state.finish()
    #     await bot.edit_message_text(chat_id=message.from_user.id,
    #                                 message_id=message.message.message_id,
    #                                 text='Что-то пошло не так, начнём заново',
    #                                 reply_markup=button_operator)


def register_handlers_other(dp: Dispatcher):
    dp.register_message_handler(operator, commands=['operator'])
    dp.register_message_handler(test, commands=['test'])

    dp.register_callback_query_handler(my_conn_operator, text='my_order_operator')
    dp.register_callback_query_handler(back_connect, text='back_connect_operator', state='*')
    dp.register_callback_query_handler(open_hist, text=['open_history_operator', 'close_history_operator'])
    dp.register_callback_query_handler(history_operator, text=['history_operator'])
    dp.register_callback_query_handler(move_operator, text=['move_up_operator', 'move_down_operator'], state=None)
    dp.register_callback_query_handler(move_non_answer, text=['move_up_operator_non_answer',
                                                              'move_down_operator_non_answer'], state=None)
    dp.register_callback_query_handler(close_connect_non_answer, text='close_admin_connect_non_answer', state='*')
    # dp.register_callback_query_handler(answer_connect_non_answer, text='answer_operator_non_answer', state='*')

    dp.register_callback_query_handler(answer_operator, text=['not_answer_operator'])

