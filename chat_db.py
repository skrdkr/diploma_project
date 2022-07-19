
import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, Time
from sqlalchemy.sql import select
import psycopg2


class ChatDb:
    """Класс базы данных чата"""
    def __init__(self):
        """Метод инициализации экземпляра базы данных"""
        self.users = None
        self.engine = sqlalchemy.create_engine("postgresql+psycopg2://postgres:1234@localhost/chat")
        self.metadata_obj = MetaData()

    def create_tables(self) -> None:
        """Создание таблиц"""
        self.users = Table('users', self.metadata_obj,
                           Column('id_user', Integer, primary_key=True),
                           Column('login', String(100), unique=True),
                           Column('password', String(100)),
                           Column('name', String(100)),
                           Column('fullname', String(100)),
                           Column('email', String(100), unique=True),
                           Column('dt_registration', String(100)),
                           Column('msg_count', Integer),
                           Column('tm_online', Time))

        self.metadata_obj.create_all(self.engine)

    def insert_user_info(self, login: str, password: str, name: str, fullname: str, email: str, dt_registration) \
            -> None:
        """Внесение данных пользователя в базу данных"""
        ins_user = self.users.insert().values(login=login, password=password, name=name, fullname=fullname,
                                              email=email, dt_registration=dt_registration, msg_count=0,
                                              tm_online='00:00:00')
        conn = self.engine.connect()
        conn.execute(ins_user)

    def select_user(self, login: str) -> list[tuple]:
        """Извлечение логина и пароля из базы данных по логину"""
        s = select(self.users.c.login, self.users.c.password).where(self.users.c.login == login)
        result = self.engine.connect().execute(s)
        user_login_pwd = result.fetchall()
        return user_login_pwd

    def msg_count(self, login: str) -> None:
        """Подсчет сообщений пользователя"""
        msg_count_update = self.users.update().values(msg_count=self.users.c.msg_count + 1). \
            where(self.users.c.login == login)
        conn = self.engine.connect()
        conn.execute(msg_count_update)

    def tm_online(self, login: str, tm_online) -> None:
        """Подсчет времени, проведенного пользователем в чате"""
        tm_online_update = self.users.update().values(tm_online=self.users.c.tm_online + tm_online). \
            where(self.users.c.login == login)
        conn = self.engine.connect()
        conn.execute(tm_online_update)

    def get_profile(self, login: str) -> list[tuple]:
        """Извлечение профиля пользователя из базы данных по логину"""
        s = select(self.users).where(self.users.c.login == login)
        result = self.engine.connect().execute(s)
        profile = result.fetchall()
        return profile
