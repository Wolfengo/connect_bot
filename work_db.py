import sqlite3
import aiogram
import json


class Client_connect:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def take_all_admin(self):
        """Достаём всех админов из базы"""
        result = self.cursor.execute("SELECT * FROM admins WHERE notification = ?", (1,))
        return result.fetchall()

    def take_all_operator(self):
        """Достаём всех админов из базы"""
        result = self.cursor.execute("SELECT * FROM admins",)
        return result.fetchall()

    def take_all_operator_non_delete(self):
        """Достаём всех админов из базы"""
        result = self.cursor.execute("SELECT * FROM admins WHERE deleted IS NULL",)
        return result.fetchall()

    def take_admin_from_id(self, id_admin):
        """Достаём админа по айди из базы"""
        result = self.cursor.execute("SELECT id_admin FROM admins WHERE id = ?", (id_admin,))
        return result.fetchall()[0][0]

    def take_id_admin(self, message_id):
        """Достаём айди админа через айди сообщения"""
        admin = self.cursor.execute("SELECT `admin_id` FROM `notification` WHERE `message_id` = ?", (message_id,))
        id_admin = admin.fetchall()[0][0]
        result = self.cursor.execute("SELECT id_admin FROM admins WHERE id = ?", (id_admin,))
        return result.fetchall()[0][0]

    def user_exists(self, user_id):
        """Проверяем, есть ли юзер в базе"""
        result = self.cursor.execute("SELECT `id` FROM `clients` WHERE `user_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def admin_exists(self, user_id):
        """Проверяем, есть ли admin в базе"""
        result = self.cursor.execute("SELECT `id` FROM `admins` WHERE `id_admin` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def answer_exists(self, message_id):
        """Проверяем, ответил ли кто-то на запрос"""
        id_problem = self.cursor.execute("SELECT `connect_id` "
                                         "FROM `notification` "
                                         "WHERE `message_id` = ?", (message_id,))
        problem = id_problem.fetchall()[0][0]
        result = self.cursor.execute("SELECT id_admin FROM connect WHERE id = ?", (problem,))
        return result.fetchall()[0][0]

    def user_name_exists(self, user_id):
        """Смотрим имя юзера"""
        result = self.cursor.execute("SELECT `user_name` FROM `clients` WHERE `user_id` = ?", (user_id,))
        return result.fetchall()[0][0]

    def user_num_exists(self, user_id):
        """Смотрим id номера юзера"""
        result = self.cursor.execute("SELECT `user_num` FROM `clients` WHERE `user_id` = ?", (user_id,))
        return result.fetchall()[0][0]

    def take_user_id_from_message_id(self, message_id):
        """Смотрим id юзера через айди таблицы"""
        result = self.cursor.execute("SELECT `user_num` FROM `clients` WHERE `user_id` = ?", (message_id,))
        return result.fetchall()[0][0]

    def take_user_num(self, user_id):
        """Достаём номер телефона"""
        id_num = self.cursor.execute("SELECT `user_num` FROM `clients` WHERE `user_id` = ?", (user_id,))
        full_num = self.cursor.execute("SELECT `number` FROM `numbers` WHERE `id` = ?", (id_num.fetchall()[0][0],))
        return full_num.fetchall()[0][0]

    # def take_admin_id_from_number(self, number):
    #     """Достаём номер телефона"""
    #     result = self.cursor.execute("SELECT `id_admin` FROM `admins` WHERE `number` = ?", (number,))
    #     return result.fetchall()[0][0]

    def add_user(self, user_id, user_name):
        """Добавляем, юзера в базу"""
        self.cursor.execute("INSERT INTO `clients` (`user_id`, 'user_name') VALUES (?,?)",
                            (user_id, user_name))
        return self.conn.commit()

    def add_operator(self, id_admin, name, number):
        """Добавляем, оператора в базу"""
        self.cursor.execute("INSERT INTO `admins` (`id_admin`, 'name', 'number') VALUES (?,?,?)",
                            (id_admin, name, number))
        return self.conn.commit()

    def add_deleted_operator(self, id_admin, name, number):
        """Добавляем, оператора в базу"""
        self.cursor.execute("UPDATE admins SET deleted = ?, name = ?, number = ? WHERE id_admin = ?",
                            (None, name, number, id_admin,))
        return self.conn.commit()

    def admin_notification_exists(self, number):
        """Проверяем, есть ли admin с таким ключом в базе"""
        result = self.cursor.execute("SELECT `id` FROM `admins` WHERE `number` = ?", (number,))
        return bool(len(result.fetchall()))

    def add_operator_notification(self, number):
        """Смотрим ключ и меняем получение уведомления"""
        id_notification = self.cursor.execute("SELECT `notification` FROM `admins` WHERE `number` = ?", (number,))
        id_notification = id_notification.fetchall()[0][0]
        if id_notification is None:
            self.cursor.execute("UPDATE admins SET notification = 1 WHERE number = ?",
                                (number,))
        else:
            self.cursor.execute("UPDATE admins SET notification = NULL WHERE number = ?",
                                (number,))
        return self.conn.commit()

    def del_operator(self, user_id):
        """Ставим метку удаления"""
        self.cursor.execute("UPDATE admins SET deleted = 1 WHERE id_admin = ?", (user_id,))
        return self.conn.commit()

    def add_number(self, user_number):
        """Добавляем, номер в базу"""
        result = self.cursor.execute("SELECT `id` FROM `numbers` WHERE `number` = ?", (user_number,))
        if not bool(len(result.fetchall())):
            self.cursor.execute("INSERT INTO `numbers` ('number') VALUES (?)",
                                (user_number,))
            return self.conn.commit()

    def change_user_name(self, name, user_id):
        """Меняем имя аккаунта телеги юзера"""
        self.cursor.execute("UPDATE clients SET user_name = ? WHERE user_id = ?", (name, user_id))
        return self.conn.commit()

    def change_user_number(self, number, user_id):
        """Меняем/удаляем номер телефона юзера"""
        self.cursor.execute("UPDATE clients SET user_num = ? WHERE user_id = ?", (number, user_id))
        return self.conn.commit()

    def save_user_id_number(self, user_number, user_id):
        """Берём айди номера и присваиваем его юзеру"""
        result = self.cursor.execute("SELECT `id` FROM `numbers` WHERE `number` = ?", (user_number,))
        self.cursor.execute("UPDATE clients SET user_num = ? WHERE user_id = ?", (result.fetchall()[0][0], user_id))
        return self.conn.commit()

    def clear_del_mess(self, id_mess):
        """Удаляем строку"""
        self.cursor.execute("DELETE FROM `delete_mess` WHERE id_mess = ?", (id_mess,))
        return self.conn.commit()

    def add_connect(self, user_id, text, problem):
        """Создаём обращение"""
        id_client = self.cursor.execute("SELECT `id` FROM `clients` WHERE `user_id` = ?", (user_id,))
        self.cursor.execute("INSERT INTO `connect` (`id_client`, 'text', 'problem') VALUES (?,?,?)",
                            (id_client.fetchall()[0][0], text, problem))
        return self.conn.commit()

    def add_notification(self, admin_id, last_connect, message_id, text):
        """Сохраняем айди уведомления, для удаления кнопок"""
        self.cursor.execute\
            ("INSERT INTO `notification` (`admin_id`, 'connect_id', 'message_id', text) VALUES (?,?,?,?)",
             (admin_id, last_connect, message_id, text))
        return self.conn.commit()

    def take_last_id_connect(self):
        """Берём последний айди обращения для уведомлений"""
        result = self.cursor.execute("SELECT * FROM connect",)
        return result.fetchall()[-1][0]

    def take_connect_notification(self, message_id):
        """Достаём айди уведомлений, через айди сообщения (для удаления кнопок)"""
        id_connect = self.cursor.execute\
            ("SELECT `connect_id` FROM `notification` WHERE `message_id` = ?", (message_id,))
        result = self.cursor.execute\
            ("SELECT * FROM `notification` WHERE `connect_id` = ?", (id_connect.fetchall()[0][0],))
        return result.fetchall()

    def take_user_id_in_notification(self, message_id):
        """Достаём айди телеги клиента, кому отвечать, через айди уведомления"""
        id_connect = self.cursor.execute\
            ("SELECT `connect_id` FROM `notification` WHERE `message_id` = ?", (message_id,))
        connect = id_connect.fetchall()[0][0]
        id_user = self.cursor.execute\
            ("SELECT id_client FROM `connect` WHERE `id` = ?", (connect,))
        user = id_user.fetchall()[0][0]
        message_id_user = self.cursor.execute \
            ("SELECT user_id FROM `clients` WHERE `id` = ?", (user,))
        return message_id_user.fetchall()[0][0]

    def give_id_admin_for_connect(self, message_id):
        """Присваиваем айди админа к обращению через айди уведомления"""
        id_connect = self.cursor.execute\
            ("SELECT `connect_id` FROM `notification` WHERE `message_id` = ?", (message_id,))
        connect = id_connect.fetchall()[0][0]
        id_admin = self.cursor.execute\
            ("SELECT `admin_id` FROM `notification` WHERE `message_id` = ?", (message_id,))
        admin = id_admin.fetchall()[0][0]
        self.cursor.execute("UPDATE connect SET id_admin = ? WHERE id = ?", (admin, connect))
        return self.conn.commit()

    def take_admin_r_name(self, message_id):
        """Достаём имя админа, через айди уведомления"""
        id_admin = self.cursor.execute \
            ("SELECT `admin_id` FROM `notification` WHERE `message_id` = ?", (message_id,))
        admin = id_admin.fetchall()[0][0]
        result = self.cursor.execute \
            ("SELECT `name` FROM `admins` WHERE `id` = ?", (admin,))
        return result.fetchall()[0][0]

    def create_new_table_user(self, id_user, last_connect, text, photo=None):
        self.cursor.execute (f"CREATE TABLE IF NOT EXISTS [{id_user}]("
                             f"id INTEGER PRIMARY KEY UNIQUE NOT NULL, "
                             f"problem CHAR NOT NULL REFERENCES connect(id),"
                             f"question  CHAR,"
                             f"answer CHAR,"
                             f"admin_id INTEGER,"
                             f"photo CHAR)")
        if photo is None:
            self.cursor.execute (f"INSERT INTO `{id_user}` ("
                                 f"`problem`, 'question') "
                                 f"VALUES (?,?)",
                                 (last_connect, text))
            self.conn.commit()
        else:
            if type(photo) is aiogram.types.input_media.MediaGroup:
                photo = photo.media
                all_photo = []
                for id_photo in photo:
                    all_photo.append(id_photo.media)
                photo = json.dumps(all_photo)
                self.cursor.execute(f"INSERT INTO `{id_user}` ("
                                    f"`problem`, 'question', 'photo') "
                                    f"VALUES (?,?,?)",
                                    (last_connect, text, photo))
                self.conn.commit()
            else:
                self.cursor.execute(f"INSERT INTO `{id_user}` ("
                                    f"`problem`, 'question', 'photo') "
                                    f"VALUES (?,?,?)",
                                    (last_connect, text, photo))
                self.conn.commit()

    def add_answer_table_user(self, id_user, answer_admin, message_id, photo=None):
        id_admin = self.cursor.execute ("SELECT `admin_id` "
                                        "FROM `notification` "
                                        "WHERE `message_id` = ?", (message_id,))
        admin = id_admin.fetchall()[0][0]
        id_problem = self.cursor.execute ("SELECT `connect_id` "
                                          "FROM `notification` "
                                          "WHERE `message_id` = ?", (message_id,))
        problem = id_problem.fetchall()[0][0]
        if photo is None:
            self.cursor.execute(f"INSERT INTO `{id_user}` ("
                                f"`answer`, 'admin_id', 'problem') "
                                f"VALUES (?,?,?)",
                                (answer_admin, admin, problem))
            return self.conn.commit()
        else:
            self.cursor.execute(f"INSERT INTO `{id_user}` ("
                                f"`answer`, 'admin_id', 'problem', 'photo') "
                                f"VALUES (?,?,?)",
                                (answer_admin, admin, problem, photo))
            return self.conn.commit()

    def change_notification_id_text(self, message_id, text_admin, old_message_id):
        self.cursor.execute("UPDATE notification "
                            "SET message_id = ?, text = ? "
                            "WHERE message_id = ?", (message_id, text_admin, old_message_id))
        return self.conn.commit()

    def take_name_problem(self, connect_id):
        result = self.cursor.execute("SELECT problem FROM `connect` WHERE `id` = ?", (connect_id,))
        return result.fetchall()[0][0]

    def take_history_account(self, user_id, status=None):
        """Достаём обращения для составления истории"""
        user_id_id = self.cursor.execute("SELECT `id` FROM `clients` WHERE `user_id` = ?", (user_id,))
        user_id_id = user_id_id.fetchall()[0][0]
        if status is not None:
            result = self.cursor.execute(f"SELECT * FROM connect WHERE status = ? AND id_client = ? ", (status,
                                                                                                        user_id_id,))
            return result.fetchall()
        else:
            result = self.cursor.execute\
                (f"SELECT * FROM connect WHERE status IS NULL AND id_client = ? ", (user_id_id,))
            return result.fetchall()

    def take_history_operator(self, user_id, status=None):
        """Достаём обращения для составления истории оператора"""
        admin = self.cursor.execute("SELECT `id` FROM `admins` WHERE `id_admin` = ?", (user_id,))
        id_admin = admin.fetchall()[0][0]
        if status is not None:
            result = self.cursor.execute(f"SELECT * FROM connect WHERE status = ? AND id_admin = ? ",
                                         (status, id_admin,))
            return result.fetchall()
        else:
            result = self.cursor.execute\
                (f"SELECT * FROM connect WHERE status IS NULL AND id_admin = ? ", (id_admin,))
            return result.fetchall()

    def take_history_connect(self, user_id, id_problem):
        """Достаём историю конкретного запроса"""
        user_id = str(user_id)
        result = self.cursor.execute(f"SELECT * FROM '{user_id}' WHERE problem = ?", (id_problem,))
        return result.fetchall()

    def take_history_connect_operator(self, id_id_user, id_problem):
        """Достаём историю конкретного запроса для оператора"""
        user = self.cursor.execute(f"SELECT user_id FROM 'clients' WHERE id = ?", (id_id_user,))
        user_id = user.fetchall()[0][0]
        result = self.cursor.execute(f"SELECT * FROM '{user_id}' WHERE problem = ?", (id_problem,))
        return result.fetchall()

    def take_non_answer_question(self):
        """Достаём историю неотвеченных запросов"""
        result = self.cursor.execute(f"SELECT * FROM 'connect' WHERE id_admin IS NULL AND status IS NULL",)
        return result.fetchall()

    def close_connect(self, message_id):
        connect = self.cursor.execute("SELECT `connect_id` FROM `notification` WHERE `message_id` = ?", (message_id,))
        id_connect = connect.fetchall()[0][0]
        self.cursor.execute("UPDATE connect SET status = 1 WHERE id = ?", (id_connect,))
        return self.conn.commit()

    def take_text_from_user_id(self, id_user, id_problem):
        result = self.cursor.execute(f"SELECT * FROM '{id_user}' WHERE problem = ?", (id_problem,))
        return result.fetchall()

    def take_user_id_from_message_id(self, message_id):
        connect = self.cursor.execute("SELECT `connect_id` FROM `notification` WHERE `message_id` = ?", (message_id,))
        id_connect = connect.fetchall()[0][0]
        client = self.cursor.execute("SELECT `id_client` FROM `connect` WHERE `id` = ?", (id_connect,))
        id_client = client.fetchall()[0][0]
        user = self.cursor.execute("SELECT `user_id` FROM `clients` WHERE `id` = ?", (id_client,))
        return user.fetchall()[0][0]

    def take_message_id_from_problem(self, id_problem):
        result = self.cursor.execute(f"SELECT * FROM 'notification' WHERE connect_id = ?", (id_problem,))
        return result.fetchall()

    def take_user_id_from_problem(self, id_problem):
        id_user = self.cursor.execute(f"SELECT id_client FROM 'connect' WHERE id = ?", (id_problem,))
        user = id_user.fetchall()[0][0]
        user_id = self.cursor.execute(f"SELECT user_id FROM 'clients' WHERE id = ?", (user,))
        return user_id.fetchall()[0][0]
