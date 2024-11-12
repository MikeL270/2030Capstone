import sqlite3
conn = sqlite3.connect('testing.db')
cursor = conn.cursor()
cursor.execute('PRAGMA foreign_keys = ON;')

def create_tables():
    cursor.execute('''CREATE TABLE IF NOT EXISTS images (
                        ImageId INTEGER PRIMARY KEY,
                        Name TEXT NOT NULL UNIQUE,
                        inTraining INTEGER NOT NULL CHECK (inTraining IN (0, 1)),
                        reviewed INTEGER NOT NULL CHECK (reviewed IN (0, 1)),
                        cropsGen INTEGER,
                        Status INTEGER
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
                        PredId INTEGER PRIMARY KEY,
                        ImageId INTEGER,
                        boxes_name TEXT,
                        scores_name TEXT,
                        labels_name TEXT,
                        FOREIGN KEY (ImageId) REFERENCES Images (ImageId)
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS crops (
                        CropId INTEGER PRIMARY KEY,
                        PredId INTEGER,
                        inLabelBox INTEGER NOT NULL CHECK (inLabelBox IN (0, 1)),
                        x_max INTEGER,
                        x_min INTEGER,
                        y_max INTEGER,
                        y_min INTEGER,
                        FOREIGN KEY (PredId) REFERENCES Predictions (PredId)
                    )''')

    conn.commit()
