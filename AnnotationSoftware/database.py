# Abstraction Module to make it easy to change database backend 
# Author: Michael B. Lance
# Created: November 17, 2024
# Updated: November 21, 2024
# Disclosure: ChatGPT was used to assist with the finer points of POOP, typing, and SQL
#---------------------------------------------------------------------------------------------------------------------------#

from abc import ABC, abstractmethod
from typing import Any

class Database(ABC): # Abstract class for all database types
    _conn: Any
    _cursor: Any

    @abstractmethod 
    def connect(self):
        pass

    def create_tables(self):
        if self._conn == None:
            self.connect() 
        
        self._cursor.execute('''CREATE TABLE IF NOT EXISTS Images ( 
                        ImageId INTEGER PRIMARY KEY,
                        Name TEXT NOT NULL,
                        InTraining INTEGER NOT NULL CHECK (InTraining IN (0, 1)),
                        Reviewed INTEGER NOT NULL CHECK (Reviewed IN (0, 1)),
                        CropsGen INTEGER
                    )''')

        self._cursor.execute('''CREATE TABLE IF NOT EXISTS Predictions (
                        PredId INTEGER PRIMARY KEY,
                        ImageId INTEGER,
                        BoxTx INTEGER,
                        BoxTy INTEGER,
                        BoxBx INTEGER,
                        BoxBy INTEGER, 
                        Score FLOAT,
                        Label INTEGER,
                        FOREIGN KEY (ImageId) REFERENCES Images (ImageId)
                    )''')

        self._cursor.execute('''CREATE TABLE IF NOT EXISTS Crops (
                        CropId INTEGER PRIMARY KEY,
                        PredId INTEGER,
                        InLabelBox INTEGER NOT NULL CHECK (InLabelBox IN (0, 1)),
                        CropTx INTEGER,
                        CropTy INTEGER,
                        CropBx INTEGER,
                        CropBy INTEGER,
                        FOREIGN KEY (PredId) REFERENCES Predictions (PredId)
                    )''')

        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_reviewed ON Images (Reviewed);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_imageid ON Predictions (ImageId);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_crops_predid ON Crops (PredId);')
        self._conn.commit()

    def commit(self):
        self._conn.commit()

    def query(self, query: str, params=None):
        self._cursor.execute(query, params or ())
        return self._cursor.fetchall()

    def lastrowid(self) -> int:
        return self._cursor.lastrowid

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if self._conn:
            self._conn.close

class SQLite(Database):
    import sqlite3
    def __init__(self, conn_string: str):
        self._db_name = conn_string
        self._conn = None
        self._cursor = None

    def connect(self):
        self._conn = self.sqlite3.connect(self._db_name)
        self._cursor = self._conn.cursor()
        self._cursor.execute("PRAGMA journal_mode = WAL;")
        self._cursor.execute("PRAGMA cache_size = -20000;")
        self._cursor.execute("PRAGMA synchronous = NORMAL;")
        self._cursor.execute("PRAGMA temp_store = MEMORY;")

