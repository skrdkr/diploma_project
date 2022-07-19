
import socket
import threading
import datetime
from chat_db import ChatDb


class Server:
    """Класс сервера"""
    def __init__(self, ip: str, port: int, chat_db):
        """Метод инициализации сервера"""
        self.ip = ip
        self.port = port
        self.chat_db = chat_db
        self.all_clients = []
        self.all_logins = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ip, self.port))
        self.server.listen(0)
        threading.Thread(target=self.connect).start()
        print('Сервер запущен!')

    def connect(self) -> None:
        """Метод установки соединения с клиентом"""
        while True:
            client, address = self.server.accept()
            threading.Thread(target=self.message_sending, args=(client,)).start()

    def message_sending(self, client_socket):
        """Метод приемки сообщений от клиентов и отправки другим клиентам"""
        while True:
            try:
                message = client_socket.recv(1024)
                message_decode = message.decode('utf-8')
                if message_decode[0:3] == "Reg":
                    dt_registration = datetime.date.today()
                    user_param_list = message_decode.split(";")
                    self.chat_db.insert_user_info(user_param_list[1], user_param_list[2], user_param_list[3],
                                                  user_param_list[4], user_param_list[5], dt_registration)
                    client_socket.send('Успешное подключение к чату!'.encode('utf-8'))
                    start_time = datetime.datetime.now()
                    user_login = user_param_list[1]
                    self.client_online(client_socket, user_param_list[1])
                    self.chat_hist_send(client_socket)
                    self.clients_online(client_socket, self.all_logins)

                elif message_decode[0:3] == "Log":
                    user_login = message_decode.split(";")[1]
                    user_password = message_decode.split(";")[2]
                    db_info = chatdb.select_user(user_login)
                    if not db_info:
                        client_socket.send('Нет такого логина! '
                                           'Повторите попытку или зарегистрируйтесь'.encode('utf-8'))
                    else:
                        if user_password == db_info[0][1]:
                            client_socket.send('Успешное подключение к чату!'.encode('utf-8'))
                            start_time = datetime.datetime.now()
                            self.client_online(client_socket, user_login)
                            self.chat_hist_send(client_socket)
                            self.clients_online(client_socket, self.all_logins)
                        else:
                            client_socket.send('Неправильный пароль! '
                                               'Повторите попытку или зарегистрируйтесь'.encode('utf-8'))

                elif message_decode == 'get_profile':
                    profile = chatdb.get_profile(user_login)
                    self.send_profile(client_socket, profile)

                elif message == b'_exit':
                    self.client_exit(client_socket, user_login, start_time)

                else:
                    msg = f"{user_login}: {message.decode('utf-8')}\n"
                    self.chat_hist_write(msg)
                    chatdb.msg_count(user_login)
                    for client in self.all_clients:
                        if client != client_socket:
                            client.send(msg.encode("utf-8"))

            except:
                client_socket.close()
                break

    def chat_hist_send(self, client_socket) -> None:
        """Метод отправки в чат архива переписки"""
        with open("chat.bin", "rb") as f:
            msg = f.read()
            client_socket.send(msg)

    def chat_hist_write(self, msg: str):
        """Метод записи сообщения пользователя в файл чата"""
        with open("chat.bin", "ab") as f:
            f.write(f"{msg}\n".encode("utf-8"))

    def clients_online(self, client_socket, all_logins: list) -> None:
        """Метод отправки в чат списка пользователей онлайн"""
        users_online = f'**********В чате***********\n'
        for i in all_logins:
            users_online += f'{i}\n'
        users_online += '****************************\n'
        client_socket.send(users_online.encode("utf-8"))

    def send_profile(self, client_socket, profile: list[tuple]) -> None:
        """Метод отправки профиля пользователя"""
        msg = f"GPrЛогин: {profile[0][1]}\n" \
              f"Пароль: {profile[0][2]}\n" \
              f"Имя: {profile[0][3]}\n" \
              f"Фамилия: {profile[0][4]}\n" \
              f"Адрес электронной почты: {profile[0][5]}\n" \
              f"Дата регистрации в чате: {profile[0][6]}\n" \
              f"Общее количество сообщений: {profile[0][7]}\n" \
              f"Общее время онлайн в чате: {str(profile[0][8])[:9]}\n"
        client_socket.send(msg.encode("utf-8"))

    def client_online(self, client_socket, user_login: str) -> None:
        """Пользователь вошел в чат"""
        self.all_clients.append(client_socket)
        self.all_logins.append(user_login)
        for client in self.all_clients:
            if client != client_socket:
                msg = f"**********{user_login.upper()} В ЧАТЕ**********\n"
                client.send(msg.encode("utf-8"))

    def client_exit(self, client_socket, user_login: str, start_time) -> None:
        """Пользователь вышел из чата"""
        self.all_clients.remove(client_socket)
        self.all_logins.remove(user_login)
        tm_online = datetime.datetime.now() - start_time
        chatdb.tm_online(user_login, tm_online)
        for client in self.all_clients:
            if client != client_socket:
                msg = f"**********{user_login.upper()} НЕ В ЧАТЕ**********\n"
                client.send(msg.encode("utf-8"))


if __name__ == "__main__":
    chatdb = ChatDb()
    chatdb.create_tables()
    myserver = Server('127.0.0.1', 50009, chatdb)
