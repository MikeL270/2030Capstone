# Abstraction module to make it easy to change database drivers 
# Author: Michael B. Lance
# Created: November 17, 2024
# Updated: April 5, 2025
#---------------------------------------------------------------------------------------------------------------------------#

from abc import ABC, abstractmethod
from typing import Any

#---------------------------------------------------------------------------------------------------------------------------#

# Add user table and mutex to images table

class Database(ABC): # Abstract class for all database types
    _conn: Any
    _cursor: Any

    def __init__(self):
        self.class_labels_foward = {}
        self.class_labels_reverse = {}
        self.herd_units_forward = {}
        self.herd_units_reverse = {}
        self.models_forward = {}
        self.models_reverse = {}

    @abstractmethod 
    def connect(self):
        pass
    
    @abstractmethod
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
                        ModelName CHAR(19) NOT NULL UNIQUE
                    )''')

         # Create HerdUnit table
        self._cursor.execute(f''' CREATE TABLE IF NOT EXISTS HerdUnits (
                        HerdUnitID SERIAL NOT NULL PRIMARY KEY,
                        HerdUnitName VARCHAR(6) NOT NULL UNIQUE
                    )''')

        # Create Images table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Images ( 
                        ImageId {auto_increment_column},
                        HerdUnitID INT,
                        Name CHAR(50) NOT NULL UNIQUE,
                        InTraining SMALLINT NOT NULL CHECK (InTraining IN (0, 1)),
                        Reviewed SMALLINT NOT NULL CHECK (Reviewed IN (0, 1)),
                        "Error" SMALLINT NOT NULL CHECK ("Error" IN (0, 1)),
                        OPEN SMALLINT NOT NULL CHECK (OPEN IN (0, 1)),
                        CropsGen INTEGER,
                        FOREIGN KEY (HerdUnitID) REFERENCES HerdUnits (HerdUnitID)
                    )''')

        # Create Predictions table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Predictions (
                        PredId {auto_increment_column},
                        ModelId INTEGER,
                        ImageId INTEGER,
                        BoxTx SMALLINT,
                        BoxTy SMALLINT,
                        BoxBx SMALLINT,
                        BoxBy SMALLINT, 
                        Score FLOAT,
                        Label SMALLINT,
                        FOREIGN KEY (ImageId) REFERENCES Images (ImageId),
                        FOREIGN KEY (ModelId) REFERENCES Models (ModelId)
                    )''')

        # Create Crops table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Crops (
                        CropId {auto_increment_column},
                        ImageId INTEGER NOT NULL,
                        ModelId INTEGER NOT NULL,
                        CropName VARCHAR(58) NOT NULL UNIQUE,
                        InLabelBox INTEGER NOT NULL CHECK (InLabelBox IN (0, 1)),
                        CropTx SMALLINT,
                        CropTy SMALLINT,
                        CropBx SMALLINT,
                        CropBy SMALLINT,
                        Created DATE,
                        globalKey CHAR(36) UNIQUE,
                        FOREIGN KEY (ImageId) REFERENCES Images (ImageId),
                        FOREIGN KEY (ModelId) REFERENCES Models (ModelId)
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

        # Create Annotations table
        self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Annotations (
                        AnnotationId {auto_increment_column},
                        CropID INT,
                        BoxTx SMALLINT,
                        BoxTy SMALLINT,
                        BoxBx SMALLINT,
                        BoxBy SMALLINT,
                        FOREIGN KEY (CropID) REFERENCES Crops (CropID)
                    )''')

        # Create Training table
        self._cursor.execute(f''' CREATE TABLE IF NOT EXISTS Training (
                        ModelId INT,
                        CropID INT,
                        FOREIGN KEY (ModelId) REFERENCES Models (ModelId),
                        FOREIGN KEY (CropId) REFERENCES CROPS (CropId),
                        PRIMARY KEY (Modelid, Cropid)
                    )''')
        
        # Create Classlabels table
        self._cursor.execute(f''' CREATE TABLE IF NOT EXISTS ClassLabels (
                             label_id INT PRIMARY KEY,
                             label VARCHAR(15))
                    ''')
        
    def create_indexes(self):
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_reviewed ON Images (Reviewed);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_imageid ON Predictions (ImageId);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_crops_imageid ON Crops (ImageId);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_croppreds_cropid ON CropPredictions (CropId)')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_herdunit_herdunitid ON HerdUnits (herdunitid)')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_modelid on Models (modelid)')
        
        self.commit()
    
    def commit(self):
        self._conn.commit()

    def query(self, query: str, params=None):
        query = query.replace('?', self.get_placeholder()) #type: ignore
        self._cursor.execute(query, params or ())
        if 'select' in query.strip().lower():
            return self._cursor.fetchall()
        else:
            return self._cursor.rowcount

    def lastrowid(self) -> int:
        return self._cursor.lastrowid

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if self._conn:
            self._conn.close

    def get_class_labels(self):
        
        self.class_labels_forward = {}
        self.class_labels_reverse = {}
        query = """
            SELECT * FROM classlabels
            
        """
        rows = self.query(query,())

        for id, name in rows:
            self.class_labels_forward[id] = name
            self.class_labels_reverse[name] = id

    def get_herd_units(self):
        query = """
            SELECT * FROM herdunits
        """
        rows = self.query(query,())

        for id, name in rows:
            self.herd_units_forward[id] = name
            self.herd_units_reverse[name] = id
    
    def get_models(self):
        query = """
            SELECT * FROM models
        """
        rows = self.query(query,())
        for id, name in rows:
            self.models_forward[id] = name
            self.models_reverse[name] = id

    def get_pred_and_images(self, batch_size: int, desired_class: int, min_confidence: float, herd_unit: str, model_name: str) -> dict:
        """ Query batch_size Images and associated predictions above a minimum score from the database
        
        Args:
            batch_size: number of images that will consist a batch 
            desired_class: integer id of desired class object derived from labelbox ontology
            min_confidence: minimum confidence for fetched predictions
            herd
            
        Returns true if image_name is origin of one of the training images.
        """

        herd_unit_id = self.herd_units_reverse[herd_unit]
        model_id = self.models_reverse[model_name]
       
        print("Querying database...")
        query = """
                WITH SelectedImageIds AS (
                    SELECT DISTINCT I.ImageId
                    FROM Images I
                    INNER JOIN Predictions P ON I.ImageId = P.ImageId
                    WHERE I.HerdUnitId = ?
                        AND I.Reviewed = ?
                        AND I.Open = 0
                        AND P.Label = ?
                        AND P.Score > ?
                    LIMIT ?
                )
                SELECT json_agg(row_to_json(img_preds))
                FROM (
                    SELECT
                        I.ImageId,
                        I.Name,
                        I.InTraining,
                        json_agg(
                            json_build_object(
                                'PredId', P.PredId,
                                'BoxTx', P.BoxTx,
                                'BoxTy', P.BoxTy,
                                'BoxBx', P.BoxBx,
                                'BoxBy', P.BoxBy,
                                'Score', P.Score,
                                'Label', P.Label
                            )
                            ORDER BY P.Score DESC
                        ) AS predictions
                    FROM Images I
                    INNER JOIN Predictions P ON I.ImageId = P.ImageId
                    WHERE I.ImageId IN (SELECT ImageId FROM SelectedImageIds)
                        AND P.Label = ?
                        AND P.Score > ?
                        AND P.ModelId = ?
                    GROUP BY I.ImageId, I.Name, I.InTraining
                    ORDER BY I.ImageId
                ) AS img_preds;
        """
        rows = self.query(query, (herd_unit_id, 0, desired_class, min_confidence, batch_size, desired_class, min_confidence, model_id,)) #type: ignore
        
        if type(rows) == 'None':
            # TODO: Raise an error here
            print("No results returned, try lowering min confidence!")
        else:
            return rows[0][0]

#---------------------------------------------------------------------------------------------------------------------------#

class SQLite(Database):
    import sqlite3
    def __init__(self, db_config: dict):
        self._db_name = db_config['database']
        self._conn = None
        self._cursor = None
                
    def connect(self):
        self._conn = self.sqlite3.connect(self._db_name)
        self._cursor = self._conn.cursor()
        self._cursor.execute('PRAGMA journal_mode = WAL;')
        self._cursor.execute('PRAGMA cache_size = -20000;')
        self._cursor.execute('PRAGMA synchronous = NORMAL;')
        self._cursor.execute('PRAGMA temp_store = MEMORY;')

    def get_auto_increment_column(self) -> str:
        return "INTEGER PRIMARY KEY"
    
    def get_placeholder(self) -> str:
        return "?"
    
#---------------------------------------------------------------------------------------------------------------------------#

class Postgres(Database):
    import psycopg2
    from psycopg2.extras import DictCursor
    def __init__(self, db_config: dict):
        super().__init__()
        self._config = db_config
        self._conn = None
        self._cursor = None
        self._dict_cursor = None
        self._pooled_conn = None

    def connect(self):
        try:
            self._conn = self.psycopg2.connect(**self._config) #type: ignore
            self._cursor = self._conn.cursor()
            self._dict_cursor = self._conn.cursor(cursor_factory=self.DictCursor)
        except (Exception, self.psycopg2.DatabaseError) as error:
            print(error)
        
        self.get_class_labels()
        self.get_herd_units()
        self.get_models()

    def get_auto_increment_column(self) -> str:
        return 'SERIAL NOT NULL PRIMARY KEY'

    def get_placeholder(self) -> str:
        return '%s'

    def lastrowid(self) -> int:
        self._cursor.execute('SELECT LASTVAL()')
        return self._cursor.fetchone()[0]

#---------------------------------------------------------------------------------------------------------------------------#

db_types = {
    "default": Postgres,
    "sqlite": SQLite,
    "postgres": Postgres,
}
