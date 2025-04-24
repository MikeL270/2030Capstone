# Dataself wrapper module for crop_generator
# Author: Michael B. Lance
# Created: November 17, 2024
# Updated: April 23, 2025
#---------------------------------------------------------------------------------------------------------------------------#

from abc import ABC, abstractmethod
from typing import Any
import json
import os
import datetime
from uuid import uuid4
from multiprocessing import Pool, cpu_count 
from ..generatorobjects.generatorobjects import *
from labelbox.data.annotation_types import Label, ObjectAnnotation, Rectangle, Point
from dotenv import load_dotenv
import labelbox as lb
from typing import Dict, List, Union
import signal

#---------------------------------------------------------------------------------------------------------------------------#
# Add user table and mutex to images table

class Database(ABC): # Abstract class for all dataself types
    _conn: Any
    _cursor: Any
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def __init__(self):
        self.class_labels_foward = {}
        self.class_labels_reverse = {}
        self.herd_units_forward = {}
        self.herd_units_reverse = {}
        self.models_forward = {}
        self.models_reverse = {}
        load_dotenv()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    @abstractmethod 
    def connect(self):
        pass
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    @abstractmethod
    def get_auto_increment_column(self):
        pass
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def get_placeholder(self):
        pass
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
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
                        'Error' SMALLINT NOT NULL CHECK ('Error' IN (0, 1)),
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#  
    def create_indexes(self):
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_reviewed ON Images (Reviewed);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_imageid ON Predictions (ImageId);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_crops_imageid ON Crops (ImageId);')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_croppreds_cropid ON CropPredictions (CropId)')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_herdunit_herdunitid ON HerdUnits (herdunitid)')
        self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_modelid on Models (modelid)')
        
        self.commit()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def commit(self):
        self._conn.commit()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def query(self, query: str, params=None):
        query = query.replace('?', self.get_placeholder()) #type: ignore
        self._cursor.execute(query, params or ())
        if 'select' in query.strip().lower():
            return self._cursor.fetchall()
        else:
            return self._cursor.rowcount
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def lastrowid(self) -> int:
        return self._cursor.lastrowid
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def rollback(self):
        self._conn.rollback()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def close(self):
        if self._conn:
            self._conn.close
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def get_class_labels(self):      
        self.class_labels_forward = {}
        self.class_labels_reverse = {}
        query = '''
            SELECT * FROM classlabels
            
        '''
        rows = self.query(query,())
        for id, name in rows:
            self.class_labels_forward[id] = name
            self.class_labels_reverse[name] = id
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def get_herd_units(self):
        query = '''
            SELECT * FROM herdunits
        '''
        rows = self.query(query,())

        for id, name in rows:
            self.herd_units_forward[id] = name
            self.herd_units_reverse[name] = id
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def insert_herd_unit(self, herd_unit_name):
        query = '''
            INSERT INTO HerdUnits (HerdUnitName)
            VALUES (?)
            ON CONFLICT(HerdUnitName) DO NOTHING
        '''      
        self.query(query, (herd_unit_name,))
        self.commit()
        self.get_herd_units()
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#   
    def get_models(self):
        query = '''
            SELECT * FROM models
        '''
        rows = self.query(query,())
        for id, name in rows:
            self.models_forward[id] = name
            self.models_reverse[name] = id
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def insert_model(self, model_name):
        query = '''
            INSERT INTO Models (ModelName)
            VALUES (?)
            ON CONFLICT(ModelName) DO NOTHING
        ''' 
        self.query(query, (model_name,))   
        self.commit()
        self.get_models()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def set_open(self, image_id: int):
        query = '''
            UPDATE Images
            SET Open = 1
            WHERE ImageId = ?
        '''
        self.query(query, (image_id,))
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def set_closed(self, image_id: int):
        query = '''
            UPDATE Images
            SET Open = 0
            WHERE ImageId = ?
        '''
        self.query(query, (image_id,))
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def set_reviewed(self, image_id: int):
        query = '''
            UPDATE Images
            SET Reviewed = 1
            WHERE ImageId = ?
        '''
        self.query(query, (image_id,))
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def update_training(self, image_names: list, modelId):
        for name in image_names:
            query = '''
                SELECT CropId, imageID
                FROM Crops
                WHERE CropName = ?
            '''
            ids = self.query(query, (name,))
            if len(ids) == 0:
                continue
            query = ''' 
                INSERT INTO TRAINING (CropId, ModelId)
                VALUES (?, ?)
                ON CONFLICT (CropId, ModelId) DO NOTHING
            '''
            self.query(query, (ids[0][0], modelId))
            query = '''
                    UPDATE Images
                    SET intraining = 1 
                    WHERE Imageid = ?
            '''
            self.query(query, (ids[0][1],))
            self.commit()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def insert_manual_crops(self, train_json_path: str, model_id: int):
        prefix = len('high-altitude-pronghorn-survey-')
        suffix = len('_crop_xx')
        current_date = datetime.date.today().strftime('%Y-%m-%d')

        with open(train_json_path) as f:
            train_json = json.load(f)

        for image_info in train_json['images']:
            query = '''
                SELECT ImageId 
                FROM Images
                WHERE Name = ?
            '''
            image_id = self.query(query, (os.path.splitext(image_info['file_name'])[0][prefix:-suffix],))[0][0]
            query = '''
                INSERT INTO Crops (ImageId, modelId, CropName, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created, GlobalKey)
                Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(CropName) DO NOTHING
            '''
            self.query(query, (image_id, model_id, os.path.splitext(image_info['file_name'])[0][prefix:], 1, 0, 0, 0, 0, current_date, str(uuid4()),))
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def concurrent_populate_images(self, images: dict[Image, Prediction], model_id: int, 
                                   herd_id: int, insert_images: bool, insert_predictions: bool):  
        concurrent_base = type(self)(self._config)
        
        concurrent_base.connect()
    
        for image in images:
            # add max score to image table, insert score based on prediction values
            # /\ I have no clue what this talking about -ML 4/22/2025
    
            if insert_images:   
                query = '''
                    INSERT INTO Images (Name, HerdUnitID, InTraining, Reviewed, 'Error', CropsGen, Open)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                '''
                try:
                    concurrent_base.query(query, (image.name, image.herd_unit_id, 1 if image.in_training == True else 0, 0, 0, 0, 0))
                except Postgres.psycopg2.errors.UniqueViolation: #TODO: Replace with generic exception
                    print('Image already in database...')
                    continue
            image_id = image.id
            if insert_predictions:
                for pred in images[image]:
                    # Prediction level IOU would most likely be less efficient than comparing individual crops
                    query = '''
                        INSERT INTO Predictions (ImageId, ModelId, BoxTx, BoxTy, BoxBx, BoxBy, Score, Label)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    try: 
                        concurrent_base.query(query, (image_id, pred.model_id, pred.dimensions.get_points(), pred.score, pred.label)) #type: ignore
                    except Postgres.psycopg2.errors.UniqueViolation: #TODO: replace with more generic catch
                        print('Prediction Already in database...')
    # Async await commit from other workers 
        concurrent_base.commit() 
        concurrent_base.close() 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def insert_to_database(self, images: dict[Image, Prediction],bootstrap: bool=False, 
                           insert_images: bool=True, insert_predictions: bool=True):
        
        # Cache the model_id and herd_unit_id
        model_id = images.values()[0].model_id
        herd_unit_id = images.keys(0)[0].herd_unit_id
        
        # Actual row insertion uses multiple processes to greatly speed up data insertion
        process_count = max(1, cpu_count())
        print(f'Inserting into the dataself on {process_count} threads...')
        total_images = len(images)
        chunk_size = (total_images + process_count - 1) // process_count # Size of each block of
        pool = Pool(processes = process_count)
        tasks = []

        # delegate chunks of total images to threads evenly
        for i in range(process_count):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i != process_count - 1 else total_images
            tasks.append((images[start:end], model_id, herd_unit_id, insert_images, insert_predictions))
            
        pool.starmap(self.concurrent_populate_images, tasks)
        pool.close()
        pool.join()

        #TODO: Go and update these methods BEFORE TESTING 
        if bootstrap:
            self.insert_manual_crops(model_id)
        self.update_training(model_id)
        self.create_indexes()
        self.commit()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def insert_full(self):
        self.insert_to_database(bootstrap=False, insert_images=True, insert_predictions=True)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def insert_new_images(self):
        self.insert_to_database(bootstrap=False, insert_images=True, insert_predictions=False)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def insert_new_preds(self):
        self.insert_to_database(bootstrap=False, insert_images=False, insert_predictions=False)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def bootstrap_database(self):
        ''' Populate a SQL database with image names and predictions

            Returns None, populate tables in a database
        '''
        # First part is single threaded for simplicity purposes
        self.create_tabfles()     
        self.insert_to_database(bootstrap=True, insert_images=True, insert_predictions=True)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def retrieve_batch(self, batch_size: int, desired_class: int, min_confidence: float,
                    herd_unit_id: str, model_id: str, img_folder: str) -> dict[Image, list[Prediction]]:
        
        batch = {}
        rows = self.get_pred_and_images(batch_size, desired_class, min_confidence, herd_unit_id, model_id)
    
        for img in rows:
            img_id =img['imageid']
            self.set_open(img_id)
        
            batch[img_id] = {}
            image = Image(
                db_id = img_id,
                name = img['name'],
                herd_unit_id = herd_unit_id,
                in_training = True if img['intraining'] == 1 else False,
                folder_path = img_folder,
                )
            batch[img_id]['image'] = image
            for pred in img['predictions']:
                batch[img_id]['predictions'] = []
                batch[img_id]['predictions'].append(
                    Prediction(
                        db_id = pred['PredId'],
                        dimensions = Box(
                            top_left = (pred['BoxTx'], pred['BoxTy']),
                            bottom_right = (pred['BoxBx'], pred['BoxBy'])
                        ),
                        score = pred['Score'],
                        label = pred['Label'],
                        model_id = model_id
                        )
                )
        self.commit()
        return batch
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def close_batch(self, batch: Dict[str, Union[Image, List[Prediction]]]):
        for image_id in batch.keys():
            self.set_closed(image_id)
        self.commit()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def interrupt_handler(self, signum, frame):
        usr_input = input(f"Interrupt signal: {signum} in {frame} recieved | IMPORTANT DON'T SAVE IF THERE WAS A PROBLEM | Save work? (Y or N): ")
        if usr_input in set(['y', 'Y', 'yes', 'Yes', 's', 'S', 'Save', 'save']):
            try:
                self.commit() 
                self.close() 
            except Exception as e:
                print(f'Exception {e} encountered')
                os.exit()
        else:    
            self.rollback() 
            self.close() 
            os.exit()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def setup_interrupt_handler(self):
        ''' Gracefully handle ^C interrupts regarding the database
        
        '''
        signal.signal(signal.SIGINT, self.interrupt_handler)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def upload_crops(self, crops: dict[Crop, list[Prediction]]):
        current_date = datetime.now()
        for crop, predictions in crops.items():
            query = '''
                INSERT INTO Crops (ModelID, ImageId, CropName, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created, GlobalKey)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''

            self.query(query, (crop.model_id, crop.image_id, crop.name, 0, crop.dimensions.get_points(), current_date, str(uuid4()))) 
            num_crops += 1

            for pred in predictions:
                query = '''
                    INSERT INTO CropPredictions (CropId, PredId, ImageId, BoxTx, BoxTy, BoxBx, BoxBy)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                '''
                self.query(query, (crop.id, pred.id, crop.image_id, pred.dimensions.get_points())) #type: ignore
            
            # Save with opencv without compression, highest quality score
            self.commit() #type: ignore
        query = '''
            UPDATE Images
            SET Reviewed = 1, Open = 0, CropsGen = ?
            WHERE ImageId = ?
        '''
        self.query(query, (num_crops, pred['image_id'])) 
        self.commit() 

        return num_crops
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def upload_to_labelbox(self, batch_size, desired_class: int, save_folder: str):
        #TODO: update to use new data structures and derive save folder from image object to reduce number of args because you 
        # (michael lance) are terrible at python
        global uploading
        if uploading:
            return 
        uploading = True
        client = lb.Client(os.environ.get('API_KEY'))
        project = client.get_project(os.environ.get('PROJECT_ID'))
        dataset = client.get_dataset(os.environ.get('DATASET_ID'))

        data_rows = []
        global_keys = []
        row_ids = []
        labels = []

        query = '''
            SELECT C.CropId, C.CropName, C.GlobalKey
            FROM Crops C 
            WHERE C.InLabelBox = 0
            LIMIT 50
            '''
        crops = base.query(query,(batch_size,)) #type: ignore
        
        if len(crops) == 0: #type: ignore
            print('No valid crops to upload, please approve predictions first!') #type: ignore
            return
        else:
            print(f'\n{len(crops)} valid crops not yet uploaded to labelbox, working!') #type: ignore

        for crop_info in crops: #type: ignore
            data_rows.append({
                'row_data': f'{save_folder}/{crop_info[1]}.jpg',
                'global_key': crop_info[2],
                'external_id': crop_info[1]
            })
            query = '''
                UPDATE Crops 
                SET InLabelBox = 1 
                WHERE CropId = ?
                '''
            self.query(query, (crop_info[0],))
            global_keys.append(crop_info[2])
            query = '''
                SELECT CP.BoxTx, BoxTy, BoxBx, BoxBy
                FROM CropPredictions CP
                WHERE ? = CP.CropId
            '''
            crop_preds = self.query(query,(crop_info[0],)) 
            for pred_info in crop_preds: #type: ignore 
                labels.append(
                    Label(
                        data = {'global_key': crop_info[2]}, #type: ignore
                        annotations = [
                            ObjectAnnotation(
                                name = self.class_labels_forward[desired_class],
                                value = Rectangle(
                                    start = Point(x = pred_info[0], y = pred_info[1]),
                                    end = Point( x = pred_info[2], y = pred_info[3])
                                )
                            )
                        ]
                    ) 
                )
        # determine chunk_size from number of data_rows
        num_data_rows = len(data_rows)
        # Multiprocessing configuration
        process_count = max(1, cpu_count())

        if num_data_rows < process_count:
            process_count = num_data_rows

        print(f'Uploading to labelbox on {process_count} threads...')

        chunk_size = (num_data_rows + process_count - 1) // process_count 
        pool = Pool(processes = process_count)
        tasks = []

        for i in range(process_count):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i != process_count - 1 else num_data_rows

            tasks.append((data_rows, start, end, dataset))

        pool.starmap(self.concurrent_upload, tasks)
        pool.close()
        pool.join()
        base.commit() #type: ignore
        # Request data rows associated with global_ids we generated for labelbox shenannigans
        res = client.get_data_row_ids_for_global_keys(global_keys)
        
        # loop over the dict to append the actual ids to a list that is useful to us
        for id in res['results']:
            row_ids.append(id)
        
        project.create_batch(
            name = f'high-altitude-pronghorn-survey-{str(uuid4())}', # add model name to batch
            data_rows = row_ids, #type_ignore
            priority = 5,
        )
    # Upload MAL label for this data row in project
        lb.MALPredictionImport.create_from_objects(
            client = client, 
            project_id = project.uid, #type: ignore 
            name='mal_job'+str(uuid4()), 
            predictions=labels
        )
        print('Upload complete!')
        uploading = False
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def concurrent_upload(data_rows, start, end, dataset):
        task = dataset.create_data_rows(data_rows[start:end])
        task.wait_until_done()
        if task.errors:
            print(task.errors)

#---------------------------------------------------------------------------------------------------------------------------#

class SQLite(Database):
    import sqlite3
    def __init__(self, db_config: dict):
        self._db_name = db_config['dataself']
        self._conn = None
        self._cursor = None
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#             
    def connect(self):
        self._conn = self.sqlite3.connect(self._db_name)
        self._cursor = self._conn.cursor()
        self._cursor.execute('PRAGMA journal_mode = WAL;')
        self._cursor.execute('PRAGMA cache_size = -20000;')
        self._cursor.execute('PRAGMA synchronous = NORMAL;')
        self._cursor.execute('PRAGMA temp_store = MEMORY;')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def get_auto_increment_column(self) -> str:
        return 'INTEGER PRIMARY KEY'
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#    
    def get_placeholder(self) -> str:
        return '?'
    
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
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def connect(self):
        try:
            self._conn = self.psycopg2.connect(**self._config) #type: ignore
            self._cursor = self._conn.cursor()
            self._dict_cursor = self._conn.cursor(cursor_factory=self.DictCursor)
        except (Exception, self.psycopg2.DataselfError) as error:
            print(error)
        
        self.get_class_labels()
        self.get_herd_units()
        self.get_models()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def get_auto_increment_column(self) -> str:
        return 'SERIAL NOT NULL PRIMARY KEY'

    def get_placeholder(self) -> str:
        return '%s'
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    def lastrowid(self) -> int:
        self._cursor.execute('SELECT LASTVAL()')
        return self._cursor.fetchone()[0]
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    #TODO: Make abstract function in base class   
    def get_pred_and_images(self, batch_size: int, desired_class: int, min_confidence: float, herd_unit_id: str, model_id: str) -> dict:
        ''' Query batch_size Images and associated predictions above a minimum score from the dataself
        
        Args:
            batch_size: number of images that will consist a batch 
            desired_class: integer id of desired class object derived from labelbox ontology
            min_confidence: minimum confidence for fetched predictions
            herd
            
        Returns true if image_name is origin of one of the training images.
        '''

       
        print('Querying dataself...')
        query = '''
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
                    GROUP BY I.ImageId, I.Name, I.InTraining, P.Score
                    ORDER BY P.Score
                ) AS img_preds;
        '''
        rows = self.query(query, (herd_unit_id, 0, desired_class, min_confidence, batch_size, desired_class, min_confidence, model_id,)) #type: ignore
        
        if type(rows) == 'None':
            # TODO: Raise an error here
            print('No results returned, try lowering min confidence!')
        else:
            return rows[0][0]

#---------------------------------------------------------------------------------------------------------------------------#

