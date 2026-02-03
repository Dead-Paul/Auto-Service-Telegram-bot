import sqlite3
from sqlite3 import Connection, Cursor
from typing import Literal, TypedDict


class SQLiteParamsDict(TypedDict, total = False):
    database: str
    detect_types: int
    isolation_level: Literal["DEFERRED", "EXCLUSIVE", "IMMEDIATE"]|None
    check_same_thread: bool
    autocommit: bool


class SQLite:
    def __init__(self, connection_params: SQLiteParamsDict, isRowReturn: bool):
        self.connection_params: SQLiteParamsDict = connection_params
        self.isRowReturn: bool = isRowReturn

        self.__connection: Connection = self.__create_connection()
        self.__cursor: Cursor = self.__connection.cursor()

    def __create_connection(self) -> Connection:
        connection: Connection = sqlite3.connect(**self.connection_params)
        if self.isRowReturn:
            connection.row_factory = sqlite3.Row
        return connection

    def cursor(self) -> Cursor:
        try:
            self.__connection.execute("SELECT 1")
        except sqlite3.Error:
            self.__connection = self.__create_connection()
            self.__cursor = self.__connection.cursor()
        return self.__cursor

