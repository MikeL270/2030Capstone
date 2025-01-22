# Abstraction Module to make it easy to change database backend 
# Author: Michael B. Lance
# Created: November 17, 2024
# Updated: January 21, 2025
#---------------------------------------------------------------------------------------------------------------------------#

from abc import ABC, abstractmethod
from typing import Any
import psycopg2

# Add user table and mutex to images table

class Database(ABC): # Abstract class for all database types
    _conn: Any
    _cursor: Any

    @abstractmethod 
    def connect(self):
        pass
    
    def get_auto_increment_column(self):
        pass

    def get_placeholder(self):
        pass
    
    def create_tables(self):
        if self._conn is None:
            self.connect()

        auto_increment_column = self.get_auto_increment_column()
    
        # Create Models table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Models (
                        ModelId {auto_increment_column},
                        ModelName TEXT
                    )''')

        # Create Images table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Images ( 
                        ImageId {auto_increment_column},
                        Name TEXT NOT NULL UNIQUE,
                        InTraining INTEGER NOT NULL CHECK (InTraining IN (0, 1)),
                        Reviewed INTEGER NOT NULL CHECK (Reviewed IN (0, 1)),
                        "Error" INTEGER NOT NULL CHECK ("Error" IN (0, 1)),
                        CropsGen INTEGER
                    )''')

        # Create Predictions table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Predictions (
                        PredId {auto_increment_column},
                        ModelId INTEGER,
                        ImageId INTEGER,
                        BoxTx INTEGER,
                        BoxTy INTEGER,
                        BoxBx INTEGER,
                        BoxBy INTEGER, 
                        Score FLOAT,
                        Label INTEGER,
                        FOREIGN KEY (ImageId) REFERENCES Images (ImageId),
                        FOREIGN KEY (ModelId) REFERENCES Models (ModelId)
                    )''')

        # Create Crops table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Crops (
                        CropId {auto_increment_column},
                        ImageId INTEGER NOT NULL,
                        CropName TEXT NOT NULL UNIQUE,
                        InLabelBox INTEGER NOT NULL CHECK (InLabelBox IN (0, 1)),
                        CropTx INTEGER,
                        CropTy INTEGER,
                        CropBx INTEGER,
                        CropBy INTEGER,
                        Created DATE,
                        globalKey TEXT UNIQUE,
                        FOREIGN KEY (ImageId) REFERENCES Images (ImageId)
                    )''')

        # Create CropPredictions table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS CropPredictions (
                        CropPredId {auto_increment_column},
                        CropId INTEGER,
                        PredId INTEGER,
                        ImageId INTEGER,
                        BoxTx INTEGER,
                        BoxTy INTEGER,
                        BoxBx INTEGER,
                        BoxBy INTEGER,
                        FOREIGN KEY (CropId) REFERENCES Crops (CropId),
                        FOREIGN KEY (PredId) REFERENCES Predictions (PredId),
                        FOREIGN KEY (ImageId) REFERENCES Images (ImageId)
                    )''')

        # Create indexes
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_reviewed ON Images (Reviewed);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_imageid ON Predictions (ImageId);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_crops_imageid ON Crops (ImageId);')
        
        self.commit()
        
    def commit(self):
        self._conn.commit()

    def query(self, query: str, params=None):
        query = query.replace("?", self.get_placeholder()) #type: ignore
        self._cursor.execute(query, params or ())
        if query.strip().lower().startswith("select"):
            return self._cursor.fetchall()
        else:
            return None

    def lastrowid(self) -> int:
        return self._cursor.lastrowid

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if self._conn:
            self._conn.close

class SQLite(Database):
    import sqlite3
    def __init__(self, db_config: dict):
        self._db_name = db_config["database"]
        self._conn = None
        self._cursor = None
                
    def connect(self):
        self._conn = self.sqlite3.connect(self._db_name)
        self._cursor = self._conn.cursor()
        self._cursor.execute("PRAGMA journal_mode = WAL;")
        self._cursor.execute("PRAGMA cache_size = -20000;")
        self._cursor.execute("PRAGMA synchronous = NORMAL;")
        self._cursor.execute("PRAGMA temp_store = MEMORY;")

    def get_auto_increment_column(self) -> str:
        return "INTEGER PRIMARY KEY"
    
    def get_placeholder(self) -> str:
        return "?"
    
class Postgres(Database):
    def __init__(self, db_config: dict):
        self._config = db_config
        self._conn = None
        self._cursor = None
        self._pooled_conn = None

    def connect(self):
        try:
            self._conn = psycopg2.connect(**self._config) #type: ignore
            self._cursor = self._conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def get_auto_increment_column(self) -> str:
        return "SERIAL NOT NULL PRIMARY KEY"

    def get_placeholder(self) -> str:
        return "%s"

    def lastrowid(self) -> int:
        self._cursor.execute("SELECT LASTVAL()")
        return self._cursor.fetchone()[0]


    
