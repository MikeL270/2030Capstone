# Database testing script
# Author: Michael B. Lance
# Created: June 30, 2025
# Updated: July 9, 2025
#---------------------------------------------------------------------------------------------------------------------------#

import unittest
from database import Database
import cropgenerator.generatorobjects as gen_objs
import os
from dotenv import load_dotenv 
import uuid

#---------------------------------------------------------------------------------------------------------------------------#
load_dotenv()

db_config = {
    'dbname': 'testing',
    'user': os.environ.get('DB_USER'),              
    'password': os.environ.get('DB_PASS'),    
    'host': os.environ.get('DB_HOST'),           
    'port': '5432',  
}

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(db_config)
        self.db.create_pool(2, 4)
    
    def test_bootstrap(self):
        print('testing bootstrap')
        result = self.db.bootstrap()
        self.assertTrue(result)

    def test_project_crud(self):
        print('testing project lifecycle...')
        project = self.db.create_project('test_project_og')
        self.assertIsInstance(project, gen_objs.Project)

        # get project by id
        project_1 = self.db.get_project(project.project_id)
        self.assertIsInstance(project_1, gen_objs.Project)

        # get project by uuid
        project_2 = self.db.get_project(project.uuid)
        self.assertIsInstance(project_2, gen_objs.Project)

        # Ensure all 3 projects are identical
        self.assertEqual(project_1, project_2)
        self.assertEqual(project_2, project)

        # modify project
        self.assertTrue(self.db.update_project(project.project_id, 'New_Name'))

        # retrieve modified project to verify change
        project_check = self.db.get_project(project.project_id)
        self.assertEqual(project_check.name, 'New_Name')

        # delete project
        self.assertTrue(self.db.delete_project(project))
    
        # attempt to retrive project to verify deletion
        deleted_project = self.db.get_project(project.project_id)
        self.assertNotIsInstance(deleted_project, gen_objs.Project)

    def test_schema_crud(self):
        print('testing scehma lifecycle...')
        schema = self.db.create_schema('pronghorn-census')
        self.assertIsInstance(schema, gen_objs.Schema)

        # get schema by id
        schema_1 = self.db.get_schema(schema.schema_id)

        # get schema by uuid
        schema_2 = self.db.get_schema(schema.uuid)

        # Ensure all 3 schemas are identical
        self.assertEqual(schema_1, schema_2)
        self.assertEqual(schema_2, schema)

        # modify schema
        self.assertTrue(self.db.update_schema(schema.schema_id, 'New Name'))

        # retrieve modifid schema
        schema_check = self.db.get_schema(schema.schema_id)
        self.assertEqual(schema_check.name, 'New Name')

        # delete schema
        self.assertTrue(self.db.delete_schema(schema))

        # attempt to retrieve schema to verify deletion
        deleted_schema = self.db.get_schema(schema.schema_id)
        self.assertNotIsInstance(deleted_schema, gen_objs.Schema)

    def test_label_crud(self):
        print('testing label lifecycle...')
        label = self.db.create_label('label', 110, 'iamge.com')

        self.assertIsInstance(label, gen_objs.Label)
        
        #get label by id 
        label_1 = self.db.get_label(label.label_id)
        self.assertIsInstance(label_1, gen_objs.Label)

        # get label by uuid
        label_2 = self.db.get_label(label.uuid)
        self.assertIsInstance(label_2, gen_objs.Label)

        # Ensure all 3 labels are identical 
        self.assertEqual(label_1, label_2)
        self.assertEqual(label_2, label)

        # modify the label -- change name

        self.assertTrue(self.db.update_label(label.label_id, name='Marshal'))

        new_name_label = self.db.get_label(label.label_id)

        self.assertEqual(new_name_label.name, 'Marshal')

        self.assertTrue(self.db.update_label(label.uuid,name = 'Eduardo'))
        new_name_label_2 = self.db.get_label(label.uuid)
        self.assertEqual(new_name_label_2.name, 'Eduardo')

        # delete label
        self.assertTrue(self.db.delete_label(label))

        # attempt to retrive label to verify deletion
        deleted_label = self.db.get_label(label.label_id)
        self.assertNotIsInstance(deleted_label, gen_objs.Label)

    

    def tearDown(self):
        self.db.close_pool()


if __name__ == "__main__":
    unittest.main()