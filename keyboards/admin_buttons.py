from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

conn_cl = InlineKeyboardButton(text='Ответить на на жалобу', callback_data='answer_cl')
close_admin_connect = InlineKeyboardButton(text='Закрыть заявку', callback_data='close_admin_connect')
buttons_connect = InlineKeyboardMarkup(row_width=1)
buttons_connect.add(conn_cl, close_admin_connect)

add_new_operator = InlineKeyboardButton(text='Добавить оператора', callback_data='add_new_operator')
delete_operator = InlineKeyboardButton(text='Удалить оператора', callback_data='del_operator')
send_history_operator = InlineKeyboardButton(text='Показать историю оператора', callback_data='send_history_operator')
notification = InlineKeyboardButton(text='Включить оповещения оператора', callback_data='notification')
admin_button = InlineKeyboardMarkup(row_width=1)
admin_button.add(add_new_operator, delete_operator, notification, send_history_operator)
#
back_answer = InlineKeyboardButton(text='Отмена', callback_data='back_answer')
back_answer_admin = InlineKeyboardButton(text='Отмена', callback_data='back_menu_admin')
back_ans = InlineKeyboardMarkup(row_width=1)
back_ans_admin_button = InlineKeyboardMarkup(row_width=1)
back_ans.add(back_answer)
back_ans_admin_button.add(back_answer_admin)

move_admin = [InlineKeyboardButton(text='<<<', callback_data='move_down_operator_delete'),
              InlineKeyboardButton(text='>>>', callback_data='move_up_operator_delete')]
operator_delete = InlineKeyboardButton(text='Удалить', callback_data='operator_delete')
admin_delete = InlineKeyboardMarkup(row_width=1)
admin_delete_solo = InlineKeyboardMarkup(row_width=1)
admin_delete.row(*move_admin).add(operator_delete, back_answer_admin)
admin_delete_solo.add(operator_delete, back_answer_admin)

proceed_answer_connect = InlineKeyboardButton(text='Ответить', callback_data='proceed_answer_connect_client')
close_client_connect = InlineKeyboardButton(text='Закрыть заявку', callback_data='close_admin_connect')
next_enter_connect_client = InlineKeyboardMarkup(row_width=1)
next_enter_connect_client.add(proceed_answer_connect, close_client_connect)

admin_open_history = InlineKeyboardButton(text='Открытые заявки', callback_data='admin_open_history_operator')
admin_close_history = InlineKeyboardButton(text='Закрытые заявки', callback_data='admin_close_history_operator')
admin_history_operator = InlineKeyboardMarkup(row_width=1)
admin_history_operator.add(admin_open_history, admin_close_history, back_answer_admin)

move_operator_history = [InlineKeyboardButton(text='<<<', callback_data='move_history_down_operator'),
                         InlineKeyboardButton(text='>>>', callback_data='move_history_up_operator')]
history = InlineKeyboardButton(text='Показать историю', callback_data='take_history_operator')
admin_send_history_operator = InlineKeyboardMarkup(row_width=1)
admin_send_history_operator_solo = InlineKeyboardMarkup(row_width=1)
admin_send_history_operator.row(*move_operator_history).add(history, back_answer_admin)
admin_send_history_operator_solo.add(history, back_answer_admin)

move_operator_notification = [InlineKeyboardButton(text='<<<', callback_data='move_notification_down_operator'),
                              InlineKeyboardButton(text='>>>', callback_data='move_notification_up_operator')]
notification_operator = InlineKeyboardButton(text='Включить/Выключить', callback_data='change_notification_operator')
admin_change_notification_operator = InlineKeyboardMarkup(row_width=1)
admin_change_notification_operator_solo = InlineKeyboardMarkup(row_width=1)
admin_change_notification_operator.row(*move_operator_notification).add(notification_operator, back_answer_admin)
admin_change_notification_operator_solo.add(notification_operator, back_answer_admin)


move_operator_for_history = [InlineKeyboardButton(text='<<<', callback_data='move_choice_down_operator'),
                             InlineKeyboardButton(text='>>>', callback_data='move_choice_up_operator')]
choice_operator = InlineKeyboardButton(text='Выбрать оператора', callback_data='choice_history_operator')
admin_choice_history_operator = InlineKeyboardMarkup(row_width=1)
admin_choice_history_operator_solo = InlineKeyboardMarkup(row_width=1)
admin_choice_history_operator.row(*move_operator_for_history).add(choice_operator, back_answer_admin)
admin_choice_history_operator_solo.add(choice_operator, back_answer_admin)
