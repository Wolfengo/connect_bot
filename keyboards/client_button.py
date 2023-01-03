from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

button_start = InlineKeyboardButton(text='Начать работу', callback_data='start_button')
start_button = InlineKeyboardMarkup(row_width=1)
start_button.add(button_start)

back_all_room = InlineKeyboardButton(text='Назад', callback_data='back_all_room')
back_register = InlineKeyboardMarkup(row_width=1)
back_register.add(back_all_room)

back_rooms = back_all_room = InlineKeyboardButton(text='Назад', callback_data='back_rooms')
back_menu = InlineKeyboardMarkup(row_width=1)
back_menu.add(back_rooms)

room_connect_button = InlineKeyboardButton(text='Обратная связь/Жалоба', callback_data='room_connect')
my_connect = InlineKeyboardButton(text='Мои обращения', callback_data='my_connect')
# setting_client = InlineKeyboardButton(text='Мои настройки', callback_data='setting_client')
# quit_account = InlineKeyboardButton(text='Изменить номер телефона', callback_data='quit')
rooms = InlineKeyboardMarkup(row_width=1)
rooms.add(room_connect_button, my_connect, ) # quit_account

forgot = InlineKeyboardButton(text='Забыл вещи', callback_data='forgot')
payment = InlineKeyboardButton(text='Что-то не так с оплатой', callback_data='payment')
ride = InlineKeyboardButton(text='Проблема с поездкой', callback_data='ride')
connect_question = InlineKeyboardButton(text='Есть вопрос по приложению', callback_data='connect_question')
complaint = InlineKeyboardButton(text='Жалоба', callback_data='complaint')
complaint_r_time = InlineKeyboardButton(text='Жалоба во время поездки (Из машины)',
                                        callback_data='complaint_r_time')
offer = InlineKeyboardButton(text='Пожелание/Предложение', callback_data='offer')
other = InlineKeyboardButton(text='Другое', callback_data='other')
back_connect = InlineKeyboardButton(text='Назад', callback_data='back_connect')
room_connect = InlineKeyboardMarkup(row_width=1)
room_connect.add(forgot, payment, ride, connect_question, complaint, complaint_r_time, offer, other, back_connect)

back_enter_connect = InlineKeyboardMarkup(row_width=1)
back_enter_connect.add(back_connect)

proceed_answer_connect = InlineKeyboardButton(text='Ответить', callback_data='proceed_answer_connect_admin')
close_client_connect = InlineKeyboardButton(text='Закрыть заявку', callback_data='close_client_connect')
next_enter_connect = InlineKeyboardMarkup(row_width=1)
next_enter_connect.add(proceed_answer_connect, close_client_connect)

back_answer = InlineKeyboardButton(text='Отмена', callback_data='back_answer_client')
back_ans_client = InlineKeyboardMarkup(row_width=1)
back_ans_client.add(back_answer)

open_history = InlineKeyboardButton(text='Открытые заявки', callback_data='open_history')
close_history = InlineKeyboardButton(text='Закрытые заявки', callback_data='close_history')
history_button = InlineKeyboardMarkup(row_width=1)
history_button.add(open_history, close_history, back_connect)

move = [InlineKeyboardButton(text='<<<', callback_data='move_down'),
        InlineKeyboardButton(text='>>>', callback_data='move_up')]
history = InlineKeyboardButton(text='Показать историю', callback_data='history')
move_back = InlineKeyboardButton(text='Отмена', callback_data='back_connect')
move_button = InlineKeyboardMarkup(row_width=1)
move_button_solo = InlineKeyboardMarkup(row_width=1)
move_button.row (*move).add(history, move_back)
move_button_solo.add(history, move_back)

