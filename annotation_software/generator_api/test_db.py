# Database testing script
# Author: Michael B. Lance, Mohammed A. Alshemary
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
        label = self.db.create_label('label', 110, 'image.com')

        self.assertIsInstance(label, gen_objs.Label)
        
        # get label by id 
        label_1 = self.db.get_label(label.label_id)
        self.assertIsInstance(label_1, gen_objs.Label)

        # get label by uuid
        label_2 = self.db.get_label(label.uuid)
        self.assertIsInstance(label_2, gen_objs.Label)

        # Ensure all 3 labels are identical 
        self.assertEqual(label_1, label_2)
        self.assertEqual(label_2, label)

        # modify the label -- change name

        self.assertTrue(self.db.update_label(label.label_id, name='label_1'))

        new_name_label = self.db.get_label(label.label_id)

        self.assertEqual(new_name_label.name, 'label_1')

        self.assertTrue(self.db.update_label(label.uuid,name = 'label_2'))
        new_name_label_2 = self.db.get_label(label.uuid)
        self.assertEqual(new_name_label_2.name, 'label_2')

        # delete label
        self.assertTrue(self.db.delete_label(label))

        # attempt to retrive label to verify deletion
        deleted_label = self.db.get_label(label.label_id)
        self.assertNotIsInstance(deleted_label, gen_objs.Label)

    def test_herd_unit_crud(self):
        print('testing herd unit lifecycle...')
        herd_unit = self.db.create_herd_unit('pr420')

        self.assertIsInstance(herd_unit, gen_objs.HerdUnit)

        # get herd unit by id
        herd_unit_1 = self.db.get_herd_unit(herd_unit.herd_unit_id)

        # get herd unit by uuid
        herd_unit_2 = self.db.get_herd_unit(herd_unit.uuid)

        # Ensure all 3 herd units are identical
        self.assertEqual(herd_unit_1, herd_unit_2)
        self.assertEqual(herd_unit_2, herd_unit)

        # modify herd unit
        self.assertTrue(self.db.update_herd_unit(herd_unit.herd_unit_id, 'New Name'))

        # retrieve modified herd unit
        herd_unit_check = self.db.get_herd_unit(herd_unit.herd_unit_id)
        self.assertEqual(herd_unit_check.name, 'New Name')

        # delete herd unit
        self.assertTrue(self.db.delete_herd_unit(herd_unit))

        # attempt to retrieve herd unit to verify deletion
        deleted_herd_unit = self.db.get_herd_unit(herd_unit.herd_unit_id)
        self.assertNotIsInstance(deleted_herd_unit, gen_objs.herd_unit)

    def test_model_crud(self):
        print('testing model lifecycle...')
        model = self.db.create_model('model_1')

        self.assertIsInstance(model, gen_objs.Model)

        # get model by id
        model_1 = self.db.get_model(model.model_id)
        self.assertIsInstance(model_1, gen_objs.Model)

        # get model by uuid
        model_2 = self.db.get_model(model.uuid)
        self.assertIsInstance(model_2, gen_objs.Model)

        # Ensure all 3 models are identical
        self.assertEqual(model_1, model_2)
        self.assertEqual(model_2, model)

        # modify the model -- change name

        self.assertTrue(self.db.update_model(model.model_id, name='model_1'))

        new_name_model = self.db.get_model(model.model.id)

        self.assertEqual(new_name_model.name, 'model_1')

        self.assertTrue(self.db.update_label(model.uuid,name = 'model_2'))
        new_name_label_2 = self.db.get_label(model.uuid)
        self.assertEqual(new_name_label_2.name, 'model_2')

        # delete model
        self.assertTrue(self.db.delete_model(model))

        # attempt to retrieve model to verify deletion
        deleted_model = self.db.get_model(model.model_id)
        self.assertNotIsInstance(deleted_model, gen_objs.Model)
        
















    def tearDown(self):
        self.db.close_pool()


if __name__ == "__main__":
    unittest.main()