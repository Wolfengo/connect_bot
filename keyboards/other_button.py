from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

my_order_operator = InlineKeyboardButton(text='Мои обращения', callback_data='my_order_operator')
not_answer_operator = InlineKeyboardButton(text='Неотвеченные обращения', callback_data='not_answer_operator')
button_operator = InlineKeyboardMarkup(row_width=1)
button_operator.add(my_order_operator, not_answer_operator)

open_history = InlineKeyboardButton(text='Открытые заявки', callback_data='open_history_operator')
close_history = InlineKeyboardButton(text='Закрытые заявки', callback_data='close_history_operator')
back_connect = InlineKeyboardButton(text='Назад', callback_data='back_connect_operator')
history_button_operator = InlineKeyboardMarkup(row_width=1)
history_button_operator.add(open_history, close_history, back_connect)

move_operator = [InlineKeyboardButton(text='<<<', callback_data='move_down_operator'),
                 InlineKeyboardButton(text='>>>', callback_data='move_up_operator')]
answer_proceed = InlineKeyboardButton(text='Ответить', callback_data='proceed_answer_connect_client')
close_client_connect_non_answer = InlineKeyboardButton(text='Закрыть заявку',
                                                       callback_data='close_admin_connect_non_answer')
history = InlineKeyboardButton(text='Показать историю', callback_data='history_operator')
move_back = InlineKeyboardButton(text='Отмена', callback_data='back_connect_operator')
move_button_operator = InlineKeyboardMarkup(row_width=1)
move_button_solo_operator = InlineKeyboardMarkup(row_width=1)
move_button_open_operator = InlineKeyboardMarkup(row_width=1)
move_button_solo_open_operator = InlineKeyboardMarkup(row_width=1)
move_button_operator.row (*move_operator).add(history, move_back)
move_button_solo_operator.add(history, move_back)
move_button_open_operator.row (*move_operator).add(history, answer_proceed, close_client_connect_non_answer, move_back)
move_button_solo_open_operator.add(history, answer_proceed, close_client_connect_non_answer, move_back)

move_non_answer = [InlineKeyboardButton(text='<<<', callback_data='move_down_operator_non_answer'),
                   InlineKeyboardButton(text='>>>', callback_data='move_up_operator_non_answer')]
answer_non_answer = InlineKeyboardButton(text='Ответить', callback_data='answer_cl')
close_client_connect_non_answer = InlineKeyboardButton(text='Закрыть заявку',
                                                       callback_data='close_admin_connect_non_answer')
move_back_non_answer = InlineKeyboardButton(text='Отмена', callback_data='back_connect_operator')
move_button_operator_non_answer = InlineKeyboardMarkup(row_width=1)
move_button_solo_operator_non_answer = InlineKeyboardMarkup(row_width=1)
move_button_solo_operator_close_answer = InlineKeyboardMarkup(row_width=1)
move_button_operator_non_answer.row (*move_non_answer).add(answer_non_answer,
                                                           close_client_connect_non_answer,
                                                           move_back_non_answer)
move_button_solo_operator_non_answer.add(answer_non_answer, close_client_connect_non_answer, move_back_non_answer)
move_button_solo_operator_close_answer.row (*move_non_answer).add(move_back_non_answer)



