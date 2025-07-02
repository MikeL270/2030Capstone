# Database testing script
# Author: Michael B. Lance
# Created: June 30, 2025
# Updated: June 30, 2025
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

        del project_1
        del project_2

        # modify project
        
        self.assertTrue(self.db.update_project(project, 'New_Name'))

        # retrieve modified project to verify change
        project_check = self.db.get_project(project.project_id)
        self.assertEqual(project_check.name, 'New_Name')

        # delete project
        self.assertTrue(self.db.delete_project(project))

        # attempt to retrive project to verify deletion
        deleted_project = self.db.get_project(project.project_id)
        self.assertNotIsInstance(deleted_project, gen_objs.Project)

    def tearDown(self):
        self.db.close_pool()


if __name__ == "__main__":
    unittest.main()