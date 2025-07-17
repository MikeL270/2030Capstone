# Database testing script
# Author: Michael B. Lance, Mohammed A. Alshemary
# Created: June 30, 2025
# Updated: July 10, 2025
#---------------------------------------------------------------------------------------------------------------------------#

import unittest
from database import Database
import cropgenerator.generatorobjects as gen_objs
import os
from dotenv import load_dotenv 

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
        print('''                            
        ▄▄▄▄▄▄▄▄ ..▄▄ · ▄▄▄▄▄▪   ▐ ▄  ▄▄ •         
        •██  ▀▄.▀·▐█ ▀. •██  ██ •█▌▐█▐█ ▀ ▪        
        ▐█.▪▐▀▀▪▄▄▀▀▀█▄ ▐█.▪▐█·▐█▐▐▌▄█ ▀█▄        
        ▐█▌·▐█▄▄▌▐█▄▪▐█ ▐█▌·▐█▌██▐█▌▐█▄▪▐█        
        ▀▀▀  ▀▀▀  ▀▀▀▀  ▀▀▀ ▀▀▀▀▀ █▪·▀▀▀▀ ▀ ▀ ▀ ▀               
        ''')
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    def test_bootstrap(self):
        print('testing bootstrap...')
        result = self.db.bootstrap()
        self.assertTrue(result)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    def test_organization_crud(self):
        print('testing organization lifecycle...')

        # create an organization object
        org = self.db.create_organizaztion('Uwyo', 'images.com/image')
        self.assertIsInstance(org, gen_objs.Organization)

        # request an (the) organization from the database by its id
        org_1 = self.db.get_organization(org.organization_id)
        self.assertIsInstance(org_1, gen_objs.Organization)

        # request an (the) organization from the database by its uuid
        org_2 = self.db.get_organization(org.uuid)
        self.assertIsInstance(org_2, gen_objs.Organization)

        # ensure all 3 organization objects are identical (if A = B, & B = C, then A = C)
        self.assertEqual(org_1, org_2)
        self.assertEqual(org_2, org)

        # modify organization -- change logo
        self.assertTrue(self.db.update_organization(org.organization_id, logo_url='otherimages.com/new-image'))

        # precipitate changes from db
        org = self.db.get_organization(org.organization_id)
        
        # modify organization -- change name
        org.name = 'other org'
        self.assertTrue(self.db.update_organization(org)) # update can take a modified object, basically the reverse of providing an id with parameters

        # verify org is no longer identical to the other two
        self.assertNotEqual(org_1, org)

        # delete the organization
        self.assertTrue(self.db.delete_organization(org))

        # attempt to request the organization from the database to verify its deletion
        org_3 = self.db.get_organization(org.organization_id)
        self.assertNotIsInstance(org_3, gen_objs.Organization)

        # cleanup memory (not needed expressly in python, but I want you to keep this concept in mind - ML)
        del org, org_1, org_2, org_3

    def test_role_crud(self):
        print('testing role lifecycle...')

        # create a role object 
        role = self.db.create_role('Annotator')
        self.assertIsInstance(role, gen_objs.Role)

        # request an (the) role from the database by its id
        role_1 = self.db.get_role(role.role_id)
        self.assertIsInstance(role_1, gen_objs.Role)

        # request an (the) role formt he database by its uuid
        role_2 = self.db.get_role(role.uuid)
        self.assertIsInstance(role_2, gen_objs.Role)

        # enusre all 3 roles are identical (if A = B, & B = C, Then A = C)
        self.assertEqual(role_1, role_2)
        self.assertEqual(role_2, role)

        # modify role -- change name
        self.assertTrue(self.db.update_role(role.role_id, role='Tester'))

        # precipitate changes from db
        role = self.db.get_role(role.role_id)

        # verify role is no longer identical to the other two
        self.assertNotEqual(role_1, role)

        # delete the role 
        self.assertTrue(self.db.delete_role(role))

        # attempt to request the role from the database to verify its deletion
        role_3 = self.db.get_organization(role.role_id)
        self.assertNotIsInstance(role_3, gen_objs.Role)

        # cleanup memory (not needed expressly in python, but I want you to keep this concept in mind - ML)
        del role, role_1, role_2, role_3

    def test_user_crud(self): 
        print('testing user lifecycle...')

        # create an organization that our user will belong to
        org = self.db.create_organizaztion(name='Uwyo', logo_url='images.com/uwyo-logo.webp')

        # create two roles that our user will belong to
        role_1 = self.db.create_role('Annotator')
        role_2 = self.db.create_role('Administrator')

        # create a user object 
        user = self.db.create_user(
            username = 'mlance', 
            external_auth_id = '12345678', 
            external_auth_provider = 'manual-token', 
            locale = 'en-us', 
            roles = [role_1, role_2], # could be a list of role objects, or of ids, or uuids that correspond to role objects in the databasea
            organizations = [org] # could be a list of organization objects, or of ids, or uuids that correspond to organization objects
            
        )
        self.assertIsInstance(user, gen_objs.User)

        # request a (the) user from the database by its id
        user_1 = self.db.get_user(int(user.id)) # pay attention to the typecasting, as flask-login requires a user id to be stored as a string, but we primarily use integer ids - ML
        
        # request a (the) user from the database by its uuid
        user_2 = self.db.get_user(user.uuid)

        # ensure all 3 users are identical (if A = B, & B = C, Then A = C)
        self.assertEqual(user_1, user_2)
        self.assertEqual(user_2, user)

        # modif user -- change user name
        self.assertTrue(self.db.update_user(int(user.id), username='Tuser')) # Be sure to use kwargs as users have several valid paramaters that can be changed

        # precipate changes from db
        user = self.db.get_user(int(user.id))

        # verify user is no longer identical to the other two
        self.assertNotEqual(user_1.username, user.username)

        # delete the user 
        self.assertTrue(self.db.delete_user(user)) # note that the user object itself IS a valid parameter 

        # attempt to request the user from the database to verify its deletion
        user_3 = self.db.get_user(int(user.id)) # even though the delete method was called for the database, the user object IS still in memory
        self.assertNotIsInstance(user_3, gen_objs.User)

        # delete roles and organizations
        self.db.delete_role(role_1)
        self.db.delete_role(role_2)
        self.db.delete_organization(org)

        # cleanup memory (not needed expressly in python, but I want you to keep this concept in mind - ML)
        del user, user_1, user_2, user_3, role_1, role_2, org

    def tearDown(self):
        self.db.close_pool()

if __name__ == "__main__":
    unittest.main()

    # def test_project_crud(self):
    #     print('testing project lifecycle...')

    #     user = self.db.create_user('tuser', '4623ghjk234g6uihklg4123jkl56', 'none', 'en-us')

    #     project = self.db.create_project(user = user, name ='test_project_og')
    #     self.assertIsInstance(project, gen_objs.Project)

    #     # get project by id
    #     project_1 = self.db.get_project(project.project_id)
    #     self.assertIsInstance(project_1, gen_objs.Project)

    #     # get project by uuid
    #     project_2 = self.db.get_project(project.uuid)
    #     self.assertIsInstance(project_2, gen_objs.Project)

    #     # Ensure all 3 projects are identical
    #     self.assertEqual(project_1, project_2)
    #     self.assertEqual(project_2, project)

    #     # modify project
    #     self.assertTrue(self.db.update_project(project.project_id, 'New_Name'))

    #     # retrieve modified project to verify change
    #     project_check = self.db.get_project(project.project_id)
    #     self.assertEqual(project_check.name, 'New_Name')

    #     # delete project
    #     self.assertTrue(self.db.delete_project(project))
    
    #     # attempt to retrive project to verify deletion
    #     deleted_project = self.db.get_project(project.project_id)
    #     self.assertNotIsInstance(deleted_project, gen_objs.Project)

    # def test_schema_crud(self):
    #     print('testing scehma lifecycle...')
    #     schema = self.db.create_schema('pronghorn-census')
    #     self.assertIsInstance(schema, gen_objs.Schema)

    #     # get schema by id
    #     schema_1 = self.db.get_schema(schema.schema_id)

    #     # get schema by uuid
    #     schema_2 = self.db.get_schema(schema.uuid)

    #     # Ensure all 3 schemas are identical
    #     self.assertEqual(schema_1, schema_2)
    #     self.assertEqual(schema_2, schema)

    #     # modify schema
    #     self.assertTrue(self.db.update_schema(schema.schema_id, 'New Name'))

    #     # retrieve modifid schema
    #     schema_check = self.db.get_schema(schema.schema_id)
    #     self.assertEqual(schema_check.name, 'New Name')

    #     # delete schema
    #     self.assertTrue(self.db.delete_schema(schema))

    #     # attempt to retrieve schema to verify deletion
    #     deleted_schema = self.db.get_schema(schema.schema_id)
    #     self.assertNotIsInstance(deleted_schema, gen_objs.Schema)

    # def test_label_crud(self):
    #     print('testing label lifecycle...')
    #     label = self.db.create_label('label', 110, 'image.com')

    #     self.assertIsInstance(label, gen_objs.Label)
        
    #     # get label by id 
    #     label_1 = self.db.get_label(label.label_id)
    #     self.assertIsInstance(label_1, gen_objs.Label)

    #     # get label by uuid
    #     label_2 = self.db.get_label(label.uuid)
    #     self.assertIsInstance(label_2, gen_objs.Label)

    #     # Ensure all 3 labels are identical 
    #     self.assertEqual(label_1, label_2)
    #     self.assertEqual(label_2, label)

    #     # modify the label -- change name

    #     self.assertTrue(self.db.update_label(label.label_id, name='label_1'))

    #     new_name_label = self.db.get_label(label.label_id)

    #     self.assertEqual(new_name_label.name, 'label_1')

    #     self.assertTrue(self.db.update_label(label.uuid,name = 'label_2'))
    #     new_name_label_2 = self.db.get_label(label.uuid)
    #     self.assertEqual(new_name_label_2.name, 'label_2')

    #     # delete label
    #     self.assertTrue(self.db.delete_label(label))

    #     # attempt to retrive label to verify deletion
    #     deleted_label = self.db.get_label(label.label_id)
    #     self.assertNotIsInstance(deleted_label, gen_objs.Label)

    # def test_herd_unit_crud(self):
    #     print('testing herd unit lifecycle...')
    #     herd_unit = self.db.create_herd_unit('pr420')

    #     self.assertIsInstance(herd_unit, gen_objs.HerdUnit)

    #     # get herd unit by id
    #     herd_unit_1 = self.db.get_herd_unit(herd_unit.herd_unit_id)

    #     # get herd unit by uuid
    #     herd_unit_2 = self.db.get_herd_unit(herd_unit.uuid)

    #     # Ensure all 3 herd units are identical
    #     self.assertEqual(herd_unit_1, herd_unit_2)
    #     self.assertEqual(herd_unit_2, herd_unit)

    #     # modify herd unit
    #     self.assertTrue(self.db.update_herd_unit(herd_unit.herd_unit_id, 'New Name'))

    #     # retrieve modified herd unit
    #     herd_unit_check = self.db.get_herd_unit(herd_unit.herd_unit_id)
    #     self.assertEqual(herd_unit_check.name, 'New Name')

    #     # delete herd unit
    #     self.assertTrue(self.db.delete_herd_unit(herd_unit))

    #     # attempt to retrieve herd unit to verify deletion
    #     deleted_herd_unit = self.db.get_herd_unit(herd_unit.herd_unit_id)
    #     self.assertNotIsInstance(deleted_herd_unit, gen_objs.HerdUnit)

    # def test_model_crud(self):
    #     print('testing model lifecycle...')
    #     model = self.db.create_model('model_1')

    #     self.assertIsInstance(model, gen_objs.Model)

    #     # get model by id
    #     model_1 = self.db.get_model(model.model_id)
    #     self.assertIsInstance(model_1, gen_objs.Model)

    #     # get model by uuid
    #     model_2 = self.db.get_model(model.uuid)
    #     self.assertIsInstance(model_2, gen_objs.Model)

    #     # Ensure all 3 models are identical
    #     self.assertEqual(model_1, model_2)
    #     self.assertEqual(model_2, model)

    #     # modify the model -- change name

    #     self.assertTrue(self.db.update_model(model.model_id, name='model_1'))

    #     new_name_model = self.db.get_model(model.model_id)

    #     self.assertEqual(new_name_model.name, 'model_1')

    #     self.assertTrue(self.db.update_model(model.uuid,name = 'model_2'))
    #     new_name_model_2 = self.db.get_model(model.uuid)
    #     self.assertEqual(new_name_model_2.name, 'model_2')

    #     # delete model
    #     self.assertTrue(self.db.delete_model(model))

    #     # attempt to retrieve model to verify deletion
    #     deleted_model = self.db.get_model(model.model_id)
    #     self.assertNotIsInstance(deleted_model, gen_objs.Model)

    # def test_survey_crud(self):
    #     print('testing survey lifecycle...')
    #     survey = self.db.create_survey(2025, 'name', 'additional_info')

    #     self.assertIsInstance(survey, gen_objs.Survey)

    #     # get survey by id
    #     survey_1 = self.db.get_survey(survey.survey_id)
    #     self.assertIsInstance(survey_1, gen_objs.Survey)

    #     # get survey by uuid
    #     survey_2 = self.db.get_survey(survey.uuid)
    #     self.assertIsInstance(survey_2, gen_objs.Survey)

    #     # Ensure all 3 surveys are identical
    #     self.assertEqual(survey_1, survey_2)
    #     self.assertEqual(survey_2, survey)

    #     # modify the survey -- change name

    #     self.assertTrue(self.db.update_survey(survey.survey_id, survey_year = 1996, name='survey_1', additional_info='nothing of note'))

    #     new_name_survey = self.db.get_survey(survey.survey_id)

    #     self.assertEqual(new_name_survey.name, 'survey_1')

    #     self.assertTrue(self.db.update_survey(survey.uuid,  survey_year = 1996, name='survey_2', additional_info='nothing of note'))
    #     new_name_survey_2 = self.db.get_survey(survey.uuid)
    #     self.assertEqual(new_name_survey_2.name, 'survey_2')

    #     # delete survey
    #     self.assertTrue(self.db.delete_survey(survey))

    #     # attempt to retrieve survey to verify deletion
    #     deleted_survey = self.db.get_survey(survey.survey_id)
    #     self.assertNotIsInstance(deleted_survey, gen_objs.Survey)
