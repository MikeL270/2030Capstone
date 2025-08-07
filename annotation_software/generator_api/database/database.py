# Psycopg3 database abstraction layer for crop generator_api
# Author: Michael B. Lance
# Created: November 17, 2024
# Updated: August 2, 2025
#---------------------------------------------------------------------------------------------------------------------------#

import os 
from uuid import UUID
from cropgenerator.generatorobjects import *
import psycopg
import psycopg.sql as sql
from psycopg_pool import ConnectionPool
from psycopg.rows import class_row, scalar_row
from functools import wraps
from typing import Callable, Any
import datetime

#---------------------------------------------------------------------------------------------------------------------------#

class Database:
    def __init__(self, db_config: dict[str, str]):
        self._config = db_config
        self._pool = None
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    def create_pool(self, min_size: int=2, max_size: int=4):
        self._pool = ConnectionPool(
            kwargs = self._config,
            min_size= min_size,
            max_size= max_size,
            open = True,
        )

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    def close_pool(self):
        self._pool.close()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    def connect(fn: Callable[..., Any]) -> Callable[..., Any]:
        ''' Wrapper function for handling connection context
        
        Args: 
            fn: method of Database class that needs to interact with the database
        '''
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            if not self._pool:
                self.create_pool()
            with self._pool.connection() as conn:
                with conn.cursor() as cursor:    
                    return fn(self, cursor, *args, **kwargs)
        return wrapper

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    @connect
    def _bootstrap(self, cursor: psycopg.cursor) -> bool:
            try:
                with open(os.path.join(os.path.dirname(__file__), 'db_definitions.sql')) as script:
                    cursor.execute(script.read())
            except Exception as e: 
                print(e)
                return False
            finally:
                return True

    def bootstrap(self) -> bool:
        ''' Create tables detailed in sql file
         
        '''
        return self._bootstrap()
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    # Project Management - Organizations
    @connect
    def _create_organization(self, cursor: psycopg.Cursor[Organization], name: str, logo_url: str | None = None) -> Organization | None:
        ''' Internal helper function, do not call directly
        
        ''' 
        cursor.row_factory = class_row(Organization)
        cursor.execute(sql.SQL('INSERT INTO usermanagement.organizations (name, logo_url) VALUES (%s, %s) RETURNING *; '), (name, logo_url))
        org = cursor.fetchone()
        return org
    
    def create_organizaztion(self, name: str, logo_url: str | None = None) -> Organization | None:
       
        return self._create_organization(name = name, logo_url = logo_url)
        

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_organization(self, cursor: psycopg.Cursor[Organization], organization_ids: int | UUID | list[int | UUID]) -> list[Organization] | Organization | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Organization)
        query = sql.SQL('SELECT * FROM usermanagement.organizations WHERE {id_field} = %s; ')
        match organization_ids:
            case list() if isinstance(organization_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('organization_id')), organization_ids)
            case list() if isinstance(organization_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), organization_ids)
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('organization_id')), (organization_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (organization_ids,))
            case _:
                raise TypeError('organization_ids must be an int, or uuid or a list')
        organizations = cursor.fetchall()
        return organizations if organizations and cursor.rowcount > 1 else organizations[0] if organizations else None

    def get_organization(self, organization_ids: int | UUID) -> list[Organization] | Organization | None:
        ''' Request an organization, or organizations object(S) from the database

        Args:
            organization_ids: an integer, uuid, or role name, or a list consisting entirely of one of those 3 types
        '''
        return self._get_organization(organization_ids = organization_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _update_organization(self, cursor: psycopg.Cursor[Organization], organization_id: Organization | int | UUID,
                             name: str | None = None, logo_url: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(''' UPDATE usermanagement.organizations SET {augmented_field}, modified = CURRENT_TIMESTAMP
                            WHERE {id_field} = %s; ''')
        kw_augmented_field = sql.SQL(',').join([sql.SQL("{} = '%s'" % (value)).format(sql.Identifier(key)) for key, value in locals().items() if key in set(['name', 'logo_url']) and value is not None])
        match organization_id:
            case Organization():
                cursor.execute(query.format(
                    augmented_field = sql.SQL(f"name = '{organization_id.name}', logo_url = '{organization_id.logo_url}'"),
                    id_field = sql.Identifier('organization_id')
                ), (organization_id.organization_id,))
            case int():
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('organization_id')
                ), (organization_id,))
            case UUID():
                cursor.execute(query.format(
                    kw_augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('uuid')
                ), (organization_id,))
            case _:
                raise TypeError('organization_id must be an Organization, int, uuid, string')
        return True if cursor.rowcount > 0 else False
    
    def update_organization(self,  organization_id: Organization | int | UUID,
                             name: str | None = None, logo_url: str | None = None) -> bool:
        ''' Augment an organization in the database by providing either a modified Organization object or a valid id and a new name and or a new logo_url
        
        Args:
            organization_id: either an Organization object, a database id, or a universally unique identifier 
            name: the new name for the organization
            logo_url: a url for the organization's logo image
        '''
        return self._update_organization(organization_id = organization_id, name = name, logo_url = logo_url)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect 
    def _delete_organization(self, cursor: psycopg.Cursor[Organization], organization_ids: Organization | int | UUID | list[int | UUID]) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM usermanagement.organizations WHERE {id_field} = %s ')
        match organization_ids:
            case list() if isinstance(organization_ids[0], Organization):
                cursor.executemany(query.format(id_field = sql.Identifier('organization_id')), [org.organization_id for org in organization_ids])
            case list() if isinstance(organization_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('organization_id')), organization_ids)
            case list() if isinstance(organization_ids[0], UUID):
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), organization_ids)
            case Organization():
                cursor.execute(query.format(id_field = sql.Identifier('organization_id')), (organization_ids.organization_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('organization_id')), (organization_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (organization_ids,))
            case _:
                raise TypeError('organization_ids must be an Organization, int, uuid, string, or a list consisting of ONE of the three')
        return True if cursor.rowcount > 0 else False
       
    def delete_organization(self, organization_ids: Organization | int | UUID | list[int | UUID]) -> bool:
        ''' Delete an organization object from the database
        
        Args:
             organization_id: either an Organization object, a database id, or a universally unique identifier
        '''
        return self._delete_organization(organization_ids = organization_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Project Management - Roles

    @connect
    def _create_role(self, cursor: psycopg.Cursor[Role], name: str) -> Role | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Role)
        cursor.execute(sql.SQL(' INSERT INTO usermanagement.roles (name) VALUES (%s) RETURNING *; '), (name,))
        role = cursor.fetchone()
        return role
    
    def create_role(self, name: str) -> Role | None:
        ''' Insert a new role object into the database

        Args:
            role: The human readable role version
        '''
        return self._create_role(name = name)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_role(self, cursor: psycopg.Cursor[Role], role_ids: int | UUID | str | list[int | UUID | str]) -> Role | list[Role] | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Role)
        query = sql.SQL(' SELECT * FROM usermanagement.roles WHERE {id_field} = %s; ')
        match role_ids:
            case list() if isinstance(role_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('role_id')), role_ids)
            case list() if isinstance(role_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), role_ids)
            case list() if isinstance(role_ids[0], str):
                cursor.executemany(query.format(id_field = sql.Identifier('name')), role_ids)
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('role_id')), (role_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (role_ids,))
            case str():
                cursor.execute(query.format(id_field = sql.Identifier('name')), (role_ids,))
            case _:
                raise TypeError('role_id must be a Role, int, uuid, string, or a list consisting of ONE of the three')
        roles = cursor.fetchall() 
        return roles if cursor.rowcount > 1 else roles[0] 

    def get_role(self, role_ids: int | UUID) -> Role | None:
        ''' Request a role, or roles object(s) from the database

        Args:
            role_ids: an integer, uuid, or role name, or a list consisting entirely of one of those 3 types
        '''
        return self._get_role(role_ids = role_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    @connect
    def _update_role(self, cursor: psycopg.Cursor[Role], role_id: Role | int | UUID | str, name: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(''' UPDATE usermanagement.roles SET name = %s, modified = CURRENT_TIMESTAMP
                            WHERE {id_field} = %s; ''')
        match role_id:
            case Role():
                cursor.execute(query.format(id_field = sql.Identifier('role_id')), (role_id.name, role_id.role_id))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('role_id')), (name, role_id))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (name, role_id))
            case str():
                cursor.execute(query.format(id_field = sql.Identifier('name')), (name, role_id))
            case _:
                raise TypeError('role_id must be a Role, int, uuid, string, or a list consisting of ONE of the three')
        return True if cursor.rowcount > 0 else False
    
    def update_role(self, role_id: Role | int | UUID, name: str | None = None) -> Role:
        return self._update_role(role_id = role_id, name = name)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _delete_role(self, cursor: psycopg.Cursor[Role], role_ids: Role | int | UUID | str | list[int | UUID | str]) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM usermanagement.roles WHERE {id_field} = %s; ') 
        match role_ids:
            case list() if isinstance(role_ids[0], Role):
                cursor.executemany(query.format(id_field = sql.Identifier('role_id')), [role.role_id for role in role_ids])
            case list() if isinstance(role_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('role_id')), role_ids)
            case list() if isinstance(role_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), role_ids)
            case list() if isinstance(role_ids[0], str):
                cursor.executemany(query.format(id_field = sql.Identifier('role')), role_ids)
            case Role():
                cursor.execute(query.format(id_field = sql.Identifier('role_id')), (role_ids.role_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('role_id')), (role_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (role_ids,))
            case str():
                cursor.execute(query.format(id_field = sql.Composable('role')), (role_ids,))
            case _:
                raise TypeError('role_id must be a Role, int, uuid, string, or a list consisting of ONE of the three')
        return True if cursor.rowcount > 0 else False
    
    def delete_role(self, role_ids: Role | int | UUID) -> bool:
        ''' Delete a role object from the database
        
        Args:
             role_id: either a Role object, a database id, or a universally unique identifier
        
        '''
        return self._delete_role(role_ids = role_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # User Management - Users

    @connect
    def _create_user(self, cursor: psycopg.Cursor[User], username: str, external_auth_id: str, external_auth_provider, locale: str) -> User | None:
        ''' Internal helper function, do not call directly
        
        '''  
        cursor.row_factory = class_row(User)
        cursor.execute(sql.SQL(''' INSERT INTO usermanagement.users (username, external_auth_id, external_auth_provider, locale)
                                   VALUES (%s, %s, %s, %s) RETURNING *; '''), (username, external_auth_id, external_auth_provider, locale))
        user = cursor.fetchone()    
        return user if isinstance(user, User) else None
    
    def create_user(self, username: str, external_auth_id: str, external_auth_provider, locale: str, 
                     roles: list[ Role | str | int | UUID] | None = None, organizations: list[Organization | int | UUID] | None = None) -> User | None:
        ''' Insert a new user object into the database
        
        Args:
            username: the human readable identifier
            external_auth_id: unique key used to verify the user with an identity provider
            external_auth_provider: name of the identity service provider
            locale: the user's locale (ex: en_us)
            roles: a list of either role objects, names, ids, or uuids
            organizations: a list of eith organization objects, names, ids, or uuids
        '''
        user = self._create_user(username = username, external_auth_id = external_auth_id, external_auth_provider = external_auth_provider, locale = locale)
        if isinstance(user, User):
            if roles:
                self._add_roles_user(user, roles)
                role_objs = self._get_user_roles(user)
                user.roles = [role for role in role_objs] if isinstance(role_objs, list) else [role_objs] if isinstance(role_objs, Role) else None
            if organizations:
                self._add_user_organizations(user.user_id, organizations)
        return user

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_user(self, cursor: psycopg.Cursor[User], user_ids: int | UUID | str | list[int | UUID | str]) -> User | None:
        ''' Internal helper function, do not call directly
        
        '''  
        cursor.row_factory = class_row(User)
        query = sql.SQL("SELECT * FROM usermanagement.users WHERE {id_field} = %s")
        match user_ids:
            case list() if isinstance(user_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('user_id')), user_ids)
            case list() if isinstance(user_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), user_ids)
            case list() if isinstance(user_ids[0], str):
                cursor.executemany(query.format(id_field = sql.Identifier('external_auth_id')), user_ids)
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('user_id')), (user_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (user_ids,))
            case str():
                cursor.execute(query.format(id_field = sql.Identifier('external_auth_id')), (user_ids,))
        try:
            users = cursor.fetchall() if cursor.rowcount > 1 else cursor.fetchone() 
        except psycopg.errors.ProgrammingError as e:
            return None
        return users if isinstance(users, list) and all(isinstance(user, User) for user in users) else users if isinstance(users, User) else None
        
    def get_user(self, user_ids: int | UUID | str | list[int | UUID | str]) -> User | None:
        ''' Query the database for a user
        
        Args:
            user_id: The user's unique database id 
        '''
        print('get_user was called')
        user = self._get_user(user_ids = user_ids)
        if isinstance(user, User):
            role_objs = self._get_user_roles(user)
            user.roles = [role for role in role_objs] if isinstance(role_objs, list) else [role_objs] if isinstance(role_objs, Role) else None
            return user
        else:
            return None
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _login_user(self, cursor: psycopg.Cursor[datetime.datetime], user_id: User | int | UUID) -> datetime.datetime | None:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' UPDATE usermanagement.users SET last_login = CURRENT_TIMESTAMP WHERE {id_field} = %s RETURNING last_login')
        match user_id:
            case User():
                cursor.execute(query.format(id_field = sql.Identifier('user_id')), (user_id.user_id,))
            case int():
                cursor.execute(query.format(id_field = sql.identifier('user_id')), (user_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (user_id,))
            case _:
                raise TypeError('user_id must be a User, int, uuid, or a list consisting of ONE of the two')
        last_login: datetime.datetime = cursor.fetchone()[0]
        return last_login if isinstance(last_login, datetime.datetime) else None
    
    def login_user(self, user_id: User | int | UUID) -> datetime.datetime | None:
        ''' Set a user's last login 
        
        '''
        return self._login_user(user_id = user_id)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect 
    def _update_user(self, cursor: psycopg.Cursor[User], user_id: User | int | UUID, username: str | None = None, 
                     external_auth_id: str | None = None, external_auth_provider: str | None = None,
                     status: str | None = None, locale: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' UPDATE usermanagement.users SET {augmented_field}, modified = CURRENT_TIMESTAMP WHERE {id_field} = %s; ')
        kw_augmented_field = sql.SQL(',').join([sql.SQL("{} = '%s'" % (value)).format(sql.Identifier(key)) for key, value in locals().items() if key in set(['username', 'external_auth_id', 'external_auth_provider', 'status', 'locale']) and value is not None])
        match user_id:
            case User():
                cursor.execute(query.format(
                    augmented_field = sql.SQL(f"username = '{user_id.username}', external_auth_id = '{user_id.external_auth_id}', external_auth_provider = '{user_id.external_auth_provider}', status = '{user_id.status}', locale = '{user_id.locale}'"),
                    id_field = sql.Identifier('user_id')
                ), (user_id.user_id,))
            case int():
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('user_id')
                ), (user_id,))
            case UUID():
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('uuid')
                ), (user_id,))
            case _:
                raise TypeError('user_id must be a User, int, uuid, or a list consisting of ONE of the two')
        return True if cursor.rowcount > 0 else False
    
    def update_user(self, user_id: User | int | UUID, username: str | None = None, 
                     external_auth_id: str | None = None, external_auth_provider: str | None = None,
                     status: str | None = None, locale: str | None = None) -> bool:
        ''' Augment a user in the database by providing a modified User object or a valid id and a new username, and or external_auth_id, and or external_auth_provider, and or status, and or locale
        
        Args:
            user_id: either a User object, a database id, or a universally unique identifier 
            username: the user's human readable name
            external_auth_id: the identifier key provided by an oauth2 provider
            external_auth_provider: The oauth2 provider
        '''
        return self._update_user(user_id = user_id, username = username, external_auth_id = external_auth_id, external_auth_provider = external_auth_provider, status = status, locale = locale)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _delete_user(self, cursor: psycopg.Cursor[User], user_ids: User | int | UUID |list[User | int | UUID]) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM usermanagement.users WHERE {id_field} = %s')
        match user_ids:
            case list() if isinstance(user_ids[0], User):
                cursor.executemany(query.format(id_field = sql.Identifier('user_id')), [user.user_id for user in user_ids])
            case list() if isinstance(user_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('user_id')), user_ids)
            case list() if isinstance(user_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), user_ids)
            case User():
                cursor.execute(query.format(id_field = sql.Identifier('user_id')), (user_ids.user_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('user_id')), (user_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (user_ids,))
            case _:
                raise TypeError('user_ids must be a User, int, uuid, , or a list consisting of ONE of the two')
        return True if cursor.rowcount > 0 else False

    def delete_user(self, user_ids: User | int | UUID) -> bool:
        ''' Delete a user object from the database
        
        Args:
             user_ids: either a user object, a database id, or a universally unique identifier or a list consisting of ONE of the two
        '''
        return self._delete_user(user_ids = user_ids)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    # Project Management - Projects
    @connect
    def _create_project(self, cursor: psycopg.Cursor[Project], name: str, ) -> Project | None:
        ''' Internal helper function, do not call directly
        
        '''   
        cursor.row_factory = class_row(Project)        
        cursor.execute(sql.SQL(' INSERT INTO projectmanagement.projects (name) VALUES (%s) RETURNING *; '), (name,))
        project = cursor.fetchone()
        return project if isinstance(project, Project) else None
    
    def create_project(self, name:str) -> Project | None:
        ''' Insert a new project object into the database

        Args:
            name: The name of the project you want to create
        '''
        return self._create_project(name = name)
        
       
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# 

    @connect
    def _get_project(self, cursor: psycopg.Cursor[Project], project_id: int | UUID) -> Project | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Project)
        query = sql.SQL(' SELECT * FROM projectmanagement.projects WHERE {id_field} = %s ')
        match project_id:
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('project_id')), (project_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (project_id,))
            case _:
                raise TypeError('project_id MUST be an integer or a UUID')
        project = cursor.fetchone()
        return project if isinstance(project, Project) else None
        
    def get_project(self, project_id: int | UUID) -> Project | None:
        ''' Query the database for a project 
        
        Args:
            project_id: either the project's internal database id or its universally unique identifier
        '''
        return self._get_project(project_id=project_id)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    @connect
    def _update_project(self, cursor: psycopg.Cursor[Project], project_id: Project | int | UUID, name: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' UPDATE projectmanagement.projects SET name = %s, modified = CURRENT_TIMESTAMP WHERE {id_field} = %s; ')
        match project_id:
            case Project():
                cursor.execute(query.format(id_field = sql.Identifier('project_id')), (project_id.name, project_id.project_id))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('project_id')), (name, project_id))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (name, project_id))
            case _:
                 raise TypeError('project_id MUST be an integer, UUID or Project type, and name must be a string')
        return True if cursor.rowcount > 0 else False

    def update_project(self, project_id: Project | int | UUID, name: str=None) -> bool:
        ''' Augment a project in the database by providing either a modified Project object or a valid id and a new name
        
        Args:
            project_id: either a project object, a database id, or a universally unique identifier 
            name: the new name for the project
        '''
        return self._update_project(project_id=project_id, name=name)


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    @connect
    def _delete_project(self, cursor: psycopg.Cursor[Project], project_id: Project | int | UUID) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM projectmanagement.projects WHERE {id_field} = %s; ')
        match project_id:
            case Project():
                cursor.execute(query.format(id_field = sql.Identifier('project_id')), (project_id.project_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('project_id')), (project_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (project_id,))
            case _:
                raise TypeError('project_id MUST be an integer, UUID or Project type')
        return True if cursor.rowcount > 0 else False    

    def delete_project(self, project_id: Project | int | UUID) -> bool:
        ''' Delete a project object from the database
        
        Args:
             project_id: either a project object, a database id, or a universally unique identifier
        '''
        return self._delete_project(project_id = project_id)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Project Management - Schemas

    @connect
    def _create_schema(self, cursor: psycopg.Cursor[Schema], name: str) -> Schema | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Schema)
        cursor.execute(sql.SQL(' INSERT INTO projectmanagement.schemas (name) VALUES (%s) RETURNING *; '), (name,))
        schema = cursor.fetchone()
        return schema if isinstance(schema, Schema) else None

    def create_schema(self, name: str) -> Schema | None:
        ''' Insert a new schema object into the database

        Args:
            name: the schema name 
        '''
        return self._create_schema(name=name)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    @connect 
    def _get_schema(self, cursor: psycopg.Cursor[Schema], schema_id: int | UUID) -> Schema | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Schema)
        query = sql.SQL('  SELECT * FROM projectmanagement.schemas WHERE {id_field} = %s ')
        match schema_id:
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('schema_id')), (schema_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (schema_id,))
            case _:
                raise TypeError('schema_id MUST be an integer or a UUID')
        schema = cursor.fetchone()
        return schema if isinstance(schema, Schema) else None

    def get_schema(self, schema_id: int | UUID):
        ''' Query the database for a schema 
        
        Args:
            schema_id: either the schema's internal database id or its universally unique identifier
        '''
        return self._get_schema(schema_id=schema_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _update_schema(self, cursor: psycopg.Cursor[Schema], schema_id: Schema | int | UUID, name: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' UPDATE projectmanagement.schemas SET name =%s, modified = CURRENT_TIMESTAMP WHERE {id_field} = %s; ')
        match schema_id:
            case Schema():
                cursor.execute(query.format(id_field = sql.Identifier('shcema_id')), (schema_id.name, schema_id.schema_id))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('schema_id')), (name, schema_id))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (name, schema_id))
            case _:
                raise TypeError('schema_id MUST be an integer, UUID or Project type, and name must be a string')
        return True if cursor.rowcount > 0 else False

    def update_schema(self, schema_id: Schema | int | UUID, name: str):
        ''' Augment a schema in the database by providing a modified Project object
        
        Args:
            schema: A schema object
        '''
        return self._update_schema(schema_id=schema_id, name=name)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    @connect
    def _delete_schema(self, cursor: psycopg.Cursor[Schema], schema_id: Schema | int | UUID) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM projectmanagement.schemas WHERE {id_field} = %s; ')
        match schema_id:
            case Schema():
                cursor.execute(query.format(id_field = sql.Identifier('schema_id')), (schema_id.schema_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('schema_id')), (schema_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (schema_id,))
            case _:
                raise TypeError('schema_id MUST be an integer, UUID or Project type')
        return True if cursor.rowcount > 0 else False 
    
    def delete_schema(self, schema_id: Schema | int | UUID):
        ''' Delete a scehma object from the database
        
        Args:
            schema: A schema object
        '''
        return self._delete_schema(schema_id=schema_id)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    # Project Management - labels
    @connect 
    def _create_label(self, cursor: psycopg.Cursor[Label], name: str, label: int, image_link: str | None = None) -> Label | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Label)
        cursor.execute(sql.SQL(' INSERT INTO projectmanagement.labels (name, label, image_link) VALUES (%s, %s, %s) RETURNING *; '), (name, label, image_link))
        lbl = cursor.fetchone()
        return  lbl if isinstance(lbl, Label) else None 
    
    def create_label(self, name: str, label: int, image_link: str) -> Label | None:
        ''' Insert a new label object into the database

        Args:
            name: The name of the label you want to create
            label: the integer value associated to the class being labeled
            image_link: optional parameter for the generator to grab an image representing the class
        '''
        return self._create_label(name=name, label=label, image_link=image_link)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_label(self, cursor: psycopg.Cursor[Label], label_id: int | UUID) -> Label | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Label)
        query = sql.SQL(' SELECT * FROM projectmanagement.labels WHERE {id_field} = %s; ')
        match label_id:
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('label_id')), (label_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (label_id,))
            case _:
                raise TypeError('label_id MUST be an integer or a UUID')
        label = cursor.fetchone()
        return label if isinstance(label, Label) else None
    
    def get_label(self, label_id: int | UUID):
        ''' Query the database for a label  
        
        Args:
            label_id: either the label's internal database id or its universally unique identifier
        '''
        return self._get_label(label_id=label_id)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _update_label(self, cursor: psycopg.Cursor[Label], label_id: Label | int | UUID, name: str | None = None, 
                      label: int | None = None, image_link: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(''' UPDATE projectmanagement.labels SET {augmented_field}, modified = CURRENT_TIMESTAMP  
                            WHERE {id_field} = %s; ''')
        kw_augmented_field = sql.SQL(',').join([sql.SQL("{} = '%s'" % (value)).format(sql.Identifier(key)) for key, value in locals().items() if key in set(['name', 'label,' 'image_link']) and value is not None])
        match label_id:
            case Label():
                cursor.execute(query.format(
                    augmented_field = sql.SQL(f"label = '{label_id.label}', name = '{label_id.name}', image_link = '{label_id.image_link}'"),
                    id_field = sql.Identifier('label_id')
                ), (label_id.label_id))
            case int():
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('label_id')
                ), (label_id,))
            case UUID():
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('uuid')
                ), (label_id,))
            case _:
                raise TypeError('label_id must be a Label, int, or UUID')
        return True if cursor.rowcount > 0 else False
            
    def update_label(self, label_id: Label | int | UUID, name: str | None = None, 
                      label: int | None = None, image_link: str | None = None, **kwargs) -> bool:
        ''' Augment a label in the database by providing a modified Label object or a valid id and a new name, and or label, and or image_link
        
        Args:
            label_id: either a Label object, a database id, or a universally unique identifier 
            label: the integer value representing the label in models
            name: the new name for the label
            image_link: a link to an example image of the object the label represents
        '''
        return self._update_label(label_id=label_id, name=name, label=label, image_link=image_link)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _delete_label(self, cursor: psycopg.Cursor[Label], label_ids: Label | int | UUID | list[int | UUID | str]) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM projectmanagement.labels WHERE {id_field} = %s; ')
        match label_ids:
            case list() if isinstance(label_ids[0], Label):
                cursor.executemany(query.format(id_field = sql.Identifier('label_id')), [label.label_id for label in label_ids])
            case list() if isinstance(label_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('label_id')), label_ids)
            case list() if isinstance(label_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), label_ids)
            case Label():
                cursor.execute(query.format(id_field = sql.Identifier('label_id')), (label_ids.label_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('label_id')), (label_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (label_ids,))
            case _:
                raise TypeError('label_id must be a Label, int, uuid, string')
        return True if cursor.rowcount > 0 else False
    
    def delete_label(self, label_ids: Label | int | UUID) -> bool:
        ''' Delete a label object from the database
        
        Args:
             label: either a label object, a database id, or a universally unique identifier 
        '''

        return self._delete_label(label_ids = label_ids)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Project Management - Herd Units

    @connect
    def _create_herd_unit(self, cursor: psycopg.Cursor[HerdUnit], name: str) -> HerdUnit | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(HerdUnit)
        cursor.execute(sql.SQL(' INSERT INTO projectmanagement.herd_units (name) VALUES (%s) RETURNING *; '), (name,))
        herd_unit = cursor.fetchone()
        return herd_unit if isinstance(herd_unit, HerdUnit) else None
    
    def create_herd_unit(self, name: str):
        ''' Insert a new herd unit object into the database

        Args:
            name: the herd unit name 
        '''
        return self._create_herd_unit(name=name)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_herd_unit(self, cursor: psycopg.Cursor[HerdUnit], herd_unit_id: int | UUID) -> HerdUnit | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(HerdUnit)
        query = sql.SQL(' SELECT * FROM projectmanagement.herd_units WHERE {id_field} = %s; ')
        match herd_unit_id:
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('herd_unit_id')), (herd_unit_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (herd_unit_id,))
            case _:
                raise TypeError('herd_unit_id MUST be an integer or a UUID')
        herd_unit = cursor.fetchone()
        return herd_unit if isinstance(herd_unit, HerdUnit) else None
    
    def get_herd_unit(self, herd_unit_id: int | UUID) -> HerdUnit | None:
         ''' Query the database for a herd unit 
        
        Args:
            herd_unit_id: either the herd unit's internal database id or its universally unique identifier
        '''
         return self._get_herd_unit(herd_unit_id=herd_unit_id)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect 
    def _update_herd_unit(self, cursor: psycopg.Cursor[HerdUnit], herd_unit_id: HerdUnit | int | UUID, name: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(''' UPDATE projectmanagement.herd_units SET name = %s, modified = CURRENT_TIMESTAMP
                            WHERE {id_field} = %s; ''')
        match herd_unit_id:
            case HerdUnit():
                cursor.execute(query.format(id_field = sql.Identifier('herd_unit_id')), (herd_unit_id.name, herd_unit_id.herd_unit_id))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('herd_unit_id')), (name, herd_unit_id))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (name, herd_unit_id))
            case _:
                raise TypeError('herd_unit MUST be an integer, UUID or Herd_Unit type, and name must be a string')
        return True if cursor.rowcount > 0 else False

    def update_herd_unit(self, herd_unit_id: HerdUnit | int | UUID, name: str | None = None) -> bool:
        ''' Augment a herd unit in the database by providing a modified HerdUnit object or a valid id and a new name
        
        Args:
            herd_unit_id: either a HerdUnit object, a database id, or a universally unique identifier 
            name: the new name for the herd unit
        '''
        return self._update_herd_unit(herd_unit_id = herd_unit_id, name=name)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _delete_herd_unit(self, cursor: psycopg.Cursor[HerdUnit], herd_unit_ids: HerdUnit | int | UUID) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM projectmanagement.herd_units WHERE {id_field} = %s; ')
        match herd_unit_ids:
            case list() if isinstance(herd_unit_ids[0], HerdUnit):
                cursor.executemany(query.format(id_field = sql.Identifier('herd_unit_id')), [herd_unit.herd_unit_id for herd_unit in herd_unit_ids])
            case list() if isinstance(herd_unit_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('herd_unit_id')), herd_unit_ids)
            case list() if isinstance(herd_unit_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), herd_unit_ids)
            case HerdUnit():
                cursor.execute(query.format(id_field = sql.Identifier('herd_unit_id')), (herd_unit_ids.herd_unit_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('herd_unit_id')), (herd_unit_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (herd_unit_ids,))
            case _:
                raise TypeError('herd_unit_id must be a Label, int, uuid, string')
        return True if cursor.rowcount > 0 else False

    def delete_herd_unit(self, herd_unit_ids: HerdUnit | int | UUID) -> bool:
        ''' Delete a herd unit object from the database
        
        Args:
             herd_unit_id: either a herd unit object, a database id, or a universally unique identifier
        '''
        return self._delete_herd_unit(herd_unit_ids = herd_unit_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    # Project Management - Models
    
    @connect
    def _create_model(self, cursor: psycopg.Cursor[Model], name: str) -> Model | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory=class_row(Model)
        cursor.execute(' INSERT into projectmanagement.models (name) VALUES (%s)  RETURNING *; ', (name,))
        model = cursor.fetchone()
        return model if isinstance(model, Model) else None

    def create_model(self, name: str) -> Model | None:
        ''' Insert a new model object into the database

        Args:
            name: the model name 
        '''
        return self._create_model(name = name)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect 
    def _get_model(self, cursor: psycopg.Cursor[Model], model_id: int | UUID) -> Model | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Model)
        query = sql.SQL(' SELECT * FROM projectmanagement.models WHERE {id_field} = %s; ')
        match model_id:
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('model_id')), (model_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (model_id,))
            case _:
                raise TypeError('model_id MUST be an integer or a UUID')
        model = cursor.fetchone()
        return model if isinstance(model, Model) else None    
    
    def get_model(self, model_id: int | UUID):
        ''' Query the database for a model
        
        Args:
            model_id: either the models's internal database id or its universally unique identifier
        '''
        return self._get_model(model_id = model_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _update_model(self, cursor: psycopg.Cursor[Model], model_id: Model | int | UUID, name: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(''' UPDATE projectmanagement.models SET name = %s, modified = CURRENT_TIMESTAMP 
                            WHERE {id_field} = %s; ''')
        match model_id:
            case Model():
                cursor.execute(query.format(id_field = sql.Identifier('model_id')), (model_id.name, model_id.model_id))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('model_id')), (name, model_id))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (name, model_id))
            case _:
                raise TypeError('model_id MUST be an integer, UUID or Herd_Unit type, and name must be a string')
        return True if cursor.rowcount > 0 else False
    
    def update_model(self, model_id: Model | int | UUID, name: str | None = None) -> bool:
        ''' Augment a model in the database by providing a modified Model object or a valid id and a new name
        
        Args:
            model: either a Model object, a database id, or a universally unique identifier 
            name: the new name for the model
        '''
        return self._update_model(model_id = model_id, name = name)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _delete_model(self, cursor: psycopg.Cursor[Model], model_ids: Model | int | UUID) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM projectmanagement.models WHERE {id_field} = %s; ')
        match model_ids:
            case list() if isinstance(model_ids[0], HerdUnit):
                cursor.executemany(query.format(id_field = sql.Identifier('model_id')), [model.model_id for model in herd_unit_ids])
            case list() if isinstance(model_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('model_id')), model_ids)
            case list() if isinstance(model_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), model_ids)
            case Model():
                cursor.execute(query.format(id_field = sql.Identifier('model_id')), (model_ids.model_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('model_id')), (model_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (model_ids,))
            case _:
                raise TypeError('model_id must be a Label, int, or uuid')
        return True if cursor.rowcount > 0 else False


    def delete_model(self, model_ids: Model | int | UUID) -> bool:
        ''' Delete a model object from the database
        
        Args:
             model_id: either a model object, a database id, or a universally unique identifier
        '''
        return self._delete_model(model_ids = model_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Project Management - Surveys

    @connect
    def _create_survey(self, cursor: psycopg.Cursor[Survey], survey_year: int, name: str, additional_info: str) -> Survey | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Survey)
        cursor.execute(sql.SQL(' INSERT into projectmanagement.surveys (survey_year, name, additional_info) VALUES (%s, %s, %s) RETURNING *; '), (survey_year, name, additional_info))
        survey = cursor.fetchone()
        return survey if isinstance(survey, Survey) else None
    
    def create_survey(self, survey_year: int, name: str, additional_info: str | None = None) -> Survey | None:
        ''' Insert a new survey object into the database

        Args:
            survey_year: the year of the survey
            name: the survey name 
            additional_info: any information that may be important regarding the survey (can be null)
        '''
        return self._create_survey(survey_year=survey_year, name=name, additional_info=additional_info)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_survey(self, cursor: psycopg.Cursor[Survey], survey_id: int | UUID) -> Survey | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Survey)
        query = sql.SQL(' SELECT * FROM projectmanagement.surveys WHERE {id_field} = %s; ')
        match survey_id:
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('survey_id')), (survey_id,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (survey_id,))
            case _:
                raise TypeError('survey_id MUST be an integer or a UUID')
        survey = cursor.fetchone()
        return survey if isinstance(survey, Survey) else None

    def get_survey(self, survey_id: int | UUID) -> Survey | None:
        ''' Query the database for a survey
        
        Args:
            survey_id: either the survey's internal database id or its universally unique identifier
        '''
        return self._get_survey(survey_id = survey_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _update_survey(self, cursor: psycopg.Cursor[Survey], survey_id: Survey | int | UUID, survey_year: int | None = None, name: str | None = None, additional_info: str | None = None) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(''' UPDATE projectmanagement.surveys SET {augmented_field}, modified = CURRENT_TIMESTAMP
                            WHERE {id_field} = %s; ''')
        kw_augmented_field = sql.SQL(',').join([sql.SQL("{} = '%s'" % (value)).format(sql.Identifier(key)) for key, value in locals().items() if key in set(['survey_year', 'name', 'additional_info',]) and value is not None])
        match survey_id:
            case Survey():
                cursor.execute(query.format(
                    augmented_field = sql.SQL(f"survey_year = '{survey_id.survey_year}', name = '{survey_id.name}', additional_info = '{survey_id.additional_info}'"),
                    id_field = sql.Identifier('survey_id')
                ), (survey_id.survey_id))
            case int():
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('survey_id')
                ), (survey_id,))
            case UUID():
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('uuid')
                ), (survey_id,))
            case _:
                raise TypeError('survey_id must be a Label, int, uuid, string')
        return True if cursor.rowcount > 0 else False
        

    def update_survey(self, survey_id: Survey | int | UUID, survey_year: int | None = None, name: str | None = None, additional_info: str | None = None):
        ''' Augment a survey in the database by providing a modified Survey object or a valid id and a new name, and or survey_year, and or additional_info
        
        Args:
            survey_id: either a Survey object, a database id, or a universally unique identifier 
            survey_year: the integer value representing the survey in models
            name: the new name for the survey
            additional_info: a link to an additional info regarding the survey
        '''
        return self._update_survey(survey_id = survey_id, survey_year = survey_year, name = name, additional_info = additional_info)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect 
    def _delete_survey(self, cursor: psycopg.Cursor[Survey], survey_ids: Survey | int | UUID) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM projectmanagement.surveys WHERE {id_field} = %s; ')
        match survey_ids:
            case list() if isinstance(survey_ids[0], Survey):
                cursor.executemany(query.format(id_field = sql.Identifier('survey_id')), [survey.survey_id for survey in survey_ids])
            case list() if isinstance(survey_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('survey_id')), survey_ids)
            case list() if isinstance(survey_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), survey_ids)
            case Survey():
                cursor.execute(query.format(id_field = sql.Identifier('survey_id')), (survey_ids.survey_id,))
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('survey_id')), (survey_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (survey_ids,))
            case _:
                raise TypeError('survey_id must be a Survey, int, uuid')
        return True if cursor.rowcount > 0 else False
    
    def delete_survey(self, survey_ids: Survey | int | UUID) -> bool:
        ''' Delete a survey object from the database
        
        Args:
             survey_id: either a survey object, a database id, or a universally unique identifier
        '''
        return self._delete_survey(survey_ids = survey_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Core - Images

    @connect
    def _create_image(self, cursor: psycopg.Cursor, name: str, herd_unit_id: int | UUID, image_length: int, image_width: int) -> Image | None:
        '''
        
        '''
        cursor.row_factory = class_row(Image)
        herd_unit_id = herd_unit_id if isinstance(herd_unit_id, int) else self._get_herd_unit(herd_unit_id).herd_unit_id
        cursor.execute(sql.SQL(' INSERT INTO core.images (herd_unit_id, name, image_length_px, image_width_px) VALUES (%s, %s, %s, %s) RETURNING *; '), (herd_unit_id, name, image_length, image_width))
        image = cursor.fetchone()
        return image if isinstance(image, Image) else None 

    def create_image(self, name: str, herd_unit_id: int | UUID, image_length: int, image_width: int) -> Image | None:
        '''
        
        '''
        return self._create_image(name = name, herd_unit_id = herd_unit_id, image_length = image_length, image_width = image_width)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_image(self, cursor: psycopg.Cursor, image_ids: int | UUID | list[int | UUID]) -> list[Image] | Image | None:
        '''
        
        '''
        cursor.row_factory = class_row(Image)
        query = sql.SQL(' SELECT * FROM core.images WHERE {id_field} = %s; ')
        match image_ids:
            case list() if isinstance(image_ids[0], int):
                cursor.executemany(query.format(id_field = sql.Identifier('image_id')), image_ids)
            case list() if isinstance(image_ids[0], UUID):
                cursor.executemany(query.format(id_field = sql.Identifier('uuid')), image_ids)
            case int():
                cursor.execute(query.format(id_field = sql.Identifier('image_id')), (image_ids,))
            case UUID():
                cursor.execute(query.format(id_field = sql.Identifier('uuid')), (image_ids,))
            case _:
                raise TypeError('image_ids must be an int, or uuid or a list')
        images = cursor.fetchall()
        return images if isinstance(images, list) and all(isinstance(image, Image) for image in images) else images if isinstance(images, Image) else None
    
    def get_image(self, image_ids: int | UUID | list[int | UUID]) -> list[Image] | Image | None:
        '''
        
        '''
        return self._get_image(image_ids = image_ids)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect 
    def _update_image(self, cursor: psycopg.Cursor, image_id: Image | int | UUID) -> bool:
        '''
        
        '''
        query = sql.SQL(''' UPDATE core.images SET {augmented_field}, modified = CURRENT_TIMESTAMP
                            WHERE {id_field} = %s; ''')
        kw_augmented_field = sql.SQL(',').join([sql.SQL("{} = '%s'" % (value).format(sql.Identifier(key)) for key, value, in locals().items() if key in set(['name', 'image_length_px', 'image_width_px', 'herd_unit_id']) and value is not None)])
        match image_id:
            case Image():
                cursor.execute(query.format(
                    augmented_field = sql.SQL(f"name = '{image_id.name}', herd_unit_id = '{image_id.herd_unit_id}', image_length_px = '{image_id.image_length_px}', image_width_px = '{image_id.image_width_px}'"),
                    id_field = sql.Identifier('image_id')
                ), (image_id.image_id))
            case int():
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('image_id')
                ), (image_id,))
            case UUID():   
                cursor.execute(query.format(
                    augmented_field = kw_augmented_field,
                    id_field = sql.Identifier('uuid')
                ), (image_id))
            case _:
                raise TypeError('image_id must be an Image, int, or UUID')
        return True if cursor.rowcount > 0 else False
    
    def update_image(self, image_id: Image | int | UUID) -> bool:
        '''
        
        '''
        return self._update_image(image_id = image_id)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Relationship Management - usermanagement <-> usermanagement: users <-> roles

    @connect
    def _add_roles_user(self, cursor: psycopg.Cursor, user_id: User | int | UUID, role_ids: Role | int | UUID | str | list[Role | int | UUID | str]) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL('''INSERT INTO usermanagement.users_roles (user_id, role_id) VALUES (%s, %s); ''')
        roles_objs = role_ids if isinstance(role_ids, Role) or (isinstance(role_ids, list) and isinstance(role_ids[0], Role)) else self._get_role(role_ids)
        match user_id:
            case User():
                cursor.executemany(query, [(user_id.user_id, role.role_id) for role in roles_objs]) if isinstance(roles_objs, list) else cursor.execute(query, (user_id.user_id, roles_objs.role_id))
            case int():
                cursor.executemany(query, [(int(user_id), role.role_id) for role in roles_objs]) if isinstance(roles_objs, list) else cursor.execute(query, (user_id, roles_objs.role_id))
            case UUID():
                user = self.get_user(user_id)
                cursor.executemany(query, [(user.user_id, role.role_id) for role in roles_objs]) if isinstance(roles_objs, list) else cursor.execute(query, (user.user_id, roles_objs.role_id))
            case _:
                raise TypeError('user_id must be a User object, int, or uuidm, and role_ids must be a Role object, int, UUID, str, or a list consisting entirely of ONE of the four ')
        return True if cursor.rowcount > 0 else False

    def add_roles_user(self, user_id: User | int | UUID, role_ids: list[Role | int | UUID ] | Role | int | UUID) -> bool:
        ''' Grant a user a role

        Args:
            user_id: either a User object, a database id, or a universally unique identifier 
            role_ids: either a Role object, a database id, or a universally unique identifier or a list consisting of ONE of the three
        '''
        return self._relate_user_roles(user_id = user_id, role_ids = role_ids)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_user_roles(self, cursor: psycopg.Cursor[Role], user_id: User| int | UUID) -> list[Role] | Role | None:
        ''' Internal helper function, do not call directly
        
        '''
        cursor.row_factory = class_row(Role)
        query = sql.SQL(''' 
            SELECT roles.role_id, name, created, modified, uuid FROM usermanagement.roles AS roles JOIN usermanagement.users_roles AS users_roles 
            ON users_roles.role_id = roles.role_id WHERE users_roles.user_id = %s; ''')
        match user_id:
            case User():
                cursor.execute(query, (user_id.user_id,))
            case int():
                cursor.execute(query, (user_id,))
            case _:
                user = self._get_user(user_id)
                cursor.execute(query, (user_id.user_id,))
        roles = cursor.fetchall()
        return roles[0] if len(roles) == 1 and isinstance(roles[0], Role) else roles if all(isinstance(role, Role) for role in roles) else None

    def get_user_roles(self, user_id: User| int | UUID) -> list[Role] | Role | None:
        ''' Request all roles associated with a user 

        Args:
            user_id: The user's unique database id 
        '''
        return self._get_user_roles(user_id = user_id)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _remove_roles_user(self, cursor: psycopg.Cursor, user_id: User | int | UUID, role_ids: Role | int | UUID | str | list[Role | int | UUID | str]) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM usermanagement.users_roles WHERE user_id = %s AND role_id = %s; ')
        roles_objs = role_ids if isinstance(role_ids[0], Role) else self._get_role(role_ids)
        match user_id:
            case User():
                cursor.executemany(query, [(user_id.user_id, role.role_id) for role in roles_objs]) if isinstance(roles_objs, list) else cursor.execute(query, (user_id.user_id, roles_objs.role_id))
            case int():
                cursor.executemany(query, [(user_id, role.role_id) for role in roles_objs]) if isinstance(roles_objs, list) else cursor.execute(query, (user_id, roles_objs.role_id))
            case _:
                user = self._get_user(user_id)
                cursor.executemany(query, [(user_id.user_id, role.role_id) for role in roles_objs]) if isinstance(roles_objs, list) else cursor.execute(query, (user_id.user_id, roles_objs.role_id))
        return True if cursor.rowcount > 0 else False
                
    def remove_roles_user(self, user_id: User | int | UUID, role_ids: Role | int | UUID | str | list[Role | int | UUID | str]) -> bool:
        ''' Remove a user from a role 
        
        '''
        self._remove_roles_user(user_id = user_id, role_ids = role_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Relationship Management - usermanagement <-> usermanagement: users <-> organizations

    @connect
    def _add_user_organizations(self, cursor: psycopg.Cursor, user_id: User | int | UUID, orgs: list[Role | int | UUID ] | Role | int | UUID) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL("INSERT INTO usermanagement.organizations_users (user_id, organization_id) VALUES (%s, %s)")
       
        match orgs:
            case list() if all(isinstance(org, Organization) for org in orgs):
                org_objs = orgs
            case _:
                org_objs = self.get_organization(orgs)
        match user_id:
            case User():
                cursor.executemany(query, [(user_id.user_id, org.organization_id) for org in org_objs]) if isinstance(org_objs, list) else cursor.execute(query, (user_id.user_id, org_objs.organization_id))
            case int():
                cursor.executemany(query, [(user_id, org.organization_id) for org in org_objs]) if isinstance(org_objs, list) else cursor.execute(query, (user_id, org_objs.organization_id))
            case _:
                user = self.get_user(user_id)
                cursor.executemany(query, [(user_id.user_id, org.organization_id) for org in org_objs]) if isinstance(org_objs, list) else cursor.execute(query, (user_id.user_id, org_objs.organization_id))
        return True if cursor.rowcount > 0 else False
    
    def add_user_organizations(self, user_id: User | int | UUID, orgs: list[Role | int | UUID ] | Role | int | UUID) -> bool:
        '''
        
        '''
        return self._add_user_organizations(user_id = user_id, orgs = orgs)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_organization_users(self, cursor: psycopg.Cursor[Organization], organization_id: Organization | int | UUID ) -> list[User] | User | None:
        ''' Internal helper function, do not call directly
        
        ''' 
        cursor.row_factory = class_row(User)
        query = sql.SQL(''' 
            SELECT users.user_id, username, external_auth_id, external_auth_provider, status, created, 
            modified, last_login, locale, uuid FROM usermanagement.users AS users JOIN usermanagement.organizations_users 
            as orgs_users ON orgs_users.user_id = users.user_id WHERE orgs_users.organization_id = %s; ''')
        match organization_id:
            case Organization():
                cursor.execute(query, (organization_id.organization_id,))
            case int():
                cursor.execute(query, (organization_id,))
            case _:
                org = self._get_organization(organization_id)
                cursor.execute(query, (org.organization_id))
        users = cursor.fetchall()
        return users[0] if len(users) == 1 and isinstance(users[0], User) else users if all(isinstance(user, User) for user in users) else None
    
    def get_organization_users(self, organization_id: Organization | int | UUID ) -> list[User] | User | None:
        '''
        
        '''
        return self._get_organization_users(organization_id = organization_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_user_organizations(self, cursor: psycopg.Cursor, user_id: User | int | UUID) -> list[Organization] | Organization | None:
        '''
        
        '''
        query = sql.SQL('''
            SELECT organizations.organization_id, name, created, modified, logo_url, uuid FROM usermanagement.organizations 
            AS organizations JOIN usermanagement.organization_users as org_users on org_users.organization_id = organizations.organization_id
            WHERE org_users.user_id = %s; ''')
        match user_id:
            case User():
                cursor.execute(query, (user_id.user_id,))
            case int():
                cursor.execute(query, (user_id,))
            case _:
                user = self._get_user(user_id)
                cursor.execute(query, (user_id.user_id))
        orgs = cursor.fetchall()
        return orgs[0] if len(orgs) == 1 and isinstance(orgs[0], Organization) else orgs if all(isinstance(org, Organization) for org in orgs) else None
    
    def get_user_organizations(self, user_id: User | int | UUID) -> list[Organization] | Organization | None:
        '''
        
        '''
        return self._get_user_organizations(user_id = user_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _remove_organization_users(self, cursor: psycopg.Cursor, organization_id: Organization | int | UUID, user_ids: User | int | UUID | list[int | UUID]) -> bool:
        ''' Internal helper function, do not call directly
        
        '''
        query = sql.SQL(' DELETE FROM usermanagement.organizations_users where organization_id = %s AND user_id = %s ')
        users_objs = user_ids if isinstance(user_ids[0], User) else self._get_user(user_ids)
        match organization_id:
            case Organization():
                cursor.executemany(query, [(organization_id.organization_id, user.user_id) for user in users_objs]) if isinstance(users_objs, list) else cursor.execute(query, (organization_id.organization_id, users_objs.user_id))
            case int():
                cursor.executemany(query, [(organization_id, user.user_id) for user in users_objs]) if isinstance(users_objs, list) else cursor.execute(query, (organization_id, users_objs.user_id))
            case _:
                org = self._get_organization(organization_id)
                cursor.executemany(query, [(org.organization_id, user.user_id) for user in users_objs]) if isinstance(users_objs, list) else  cursor.execute(query, (org.organization_id, users_objs.user_id))
        return True if cursor.rowcount > 0 else False 

    def remove_organization_users(self, organization_id: Organization | int | UUID, user_ids: User | int | UUID | list[int | UUID]) -> bool:
        '''
        
        '''
        self._remove_organization_users(organization_id = organization_id, user_ids = user_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Relationship Management - projectmanagement <-> usermanagement: projects <-> users

    @connect
    def _add_user_project(self, cursor: psycopg.Cursor, project_id: Project | int | UUID, user_ids: User | int | UUID | list[User | int | UUID]) -> bool:
        '''
        
        '''
        query = sql.SQL(''' INSERT INTO projectmanagement.projects_users (project_id, user_id) VALUES (%s, %s); ''')
        user_objs = user_ids if isinstance(user_ids, User) or (isinstance(user_ids, list) and isinstance(user_ids[0], User)) else self._get_user(user_ids)
        match project_id:
            case Project():
                cursor.executemany(query, [(project_id.project_id, user.user_id) for user in user_ids]) if isinstance(user_objs, list) else cursor.execute(query, (project_id.project_id, user_objs.user_id))
            case int():
                cursor.executemany(query, [(project_id, user.user_id) for user in user_ids]) if isinstance(user_objs, list) else cursor.execute(query, (project_id, user_objs.user_id))
            case _:
                project = self._get_project(project_id)
                cursor.execute(query, [(project.project_id, user.user_id) for user in user_ids]) if isinstance(user_objs, list) else cursor.execute(query, (project.project_id, user_objs.user_id))
        return True if cursor.rowcount > 0 else None
    
    def add_user_project(self, project_id: Project | int | UUID, user_ids: User | int | UUID | list[User | int | UUID]) -> bool:
        '''
        
        '''
        return self._add_user_project(project_id = project_id, user_ids = user_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect 
    def _get_project_users(self, cursor: psycopg.Cursor[User], project_id: Project | int | UUID) -> list[User] | User | None:
        '''
        
        '''
        cursor.row_factory = class_row(User)
        query = sql.SQL('''
            SELECT users.user_id, username, external_auth_id, external_auth_provider, status, created, 
            modified, last_login, locale, uuid FROM usermanagement.users AS users JOIN projectmanagement.projects_users
            as projects_users ON projects_users.user_id = users.user_id WHERE projects_users.project_id = %s; ''')
        match project_id:
            case Project():
                cursor.execute(query, (project_id.project_id,))
            case int():
                cursor.execute(query, (project_id,))
            case _:
                project = self._get_project(project_id)
                cursor.execute(query, (project.project_id,))
        users = cursor.fetchall()
        return users[0] if len(users) == 1 and isinstance(users[0], User) else users if all(isinstance(user, User) for user in users) else None
    
    def get_project_users(self, project_id: Project | int | UUID) -> list[User] | User | None:
        '''
        
        '''
        return self._get_project_users(project_id = project_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_user_projects(self, cursor: psycopg.Cursor, user_id: User | int | UUID) -> list[Project] | None:
        '''
        
        '''
        cursor.row_factory = class_row(Project)
        query = sql.SQL(''' 
            SELECT projects.project_id, name, created, modified, uuid FROM projectmanagement.projects as projects JOIN 
            projectmanagement.projects_users AS projects_users ON projects_users.project_id = projects.project_id
            WHERE projects_users.user_id = %s; ''')
        match user_id:
            case User():
                cursor.execute(query, (user_id.user_id,))
            case int():
                cursor.execute(query, (user_id,))
            case _:
                user = self._get_user(user_id)
                cursor.execute(query, (user.user_id,))
        projects = cursor.fetchall()
        return projects 

    def get_user_projects(self, user_id: User | int | UUID) -> list[Project] | None:
        '''
        
        '''
        return self._get_user_projects(user_id = user_id)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect 
    def _remove_project_users(self, cursor: psycopg.Cursor, project_id: Project | int | UUID, user_ids: User | int | UUID | list[int | UUID]) -> bool:
        '''
        
        '''
        query = sql.SQL(' DELETE FROM projectmanagement.projects_users where project_id = %s AND user_id = %s ')
        users_objs = user_ids if isinstance(user_ids[0], User) else self._get_user(user_ids)
        match project_id:
            case Project():
                cursor.executemany(query, [(project_id.project_id, user.user_id) for user in users_objs]) if isinstance(users_objs, list) else cursor.execute(query, (project_id.project_id, users_objs.user_id))
            case int():
                cursor.executemany(query, [(project_id, user.user_id) for user in users_objs]) if isinstance(users_objs, list) else cursor.execute(query, (project_id, users_objs.user_id))
            case _:
                project = self._get_project(project_id)
                cursor.executemany(query, [(project.project_id, user.user_id) for user in users_objs]) if isinstance(users_objs, list) else  cursor.execute(query, (project.project_id, users_objs.user_id))
        return True if cursor.rowcount > 0 else False 

    def remove_project_users(self, project_id: Project | int | UUID, user_ids: User | int | UUID | list[int | UUID]) -> bool:
        '''
        
        '''
        self._remove_project_users(project_id = project_id, user_ids = user_ids)
    
     #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Relationship Management - projectmanagement <-> projectmanagement: projects <-> schemas

    @connect
    def _add_schema_project(self, cursor: psycopg.Cursor, project_id: Project | int | UUID, schema_ids: Schema | int | UUID | list[int | UUID]) -> bool:
        '''
        
        '''
        query = sql.SQL(''' INSERT INTO projectmanagement.projects_schemas (project_id, schema_id) VALUES (%s, %s); ''')
        schema_objs = schema_ids if isinstance(schema_ids, Schema) or (isinstance(schema_ids, list) and isinstance(schema_ids[0], Schema)) else self._get_schema()
        match project_id:
            case Project():
                cursor.executemany(query, [(project_id.project_id, schema.schema_id) for schema in schema_ids]) if isinstance(schema_objs, list) else cursor.execute(query, (project_id.project_id, schema_objs.schema_id))
            case int():
                cursor.executemany(query, [(project_id, schema.schema_id) for schema in schema_ids]) if isinstance(schema_objs, list) else cursor.execute(query, (project_id, schema_objs.schema_id))
            case _:
                project = self._get_project(project_id)
                cursor.execute(query, [(project.project_id, schema.schema_id) for schema in schema_ids]) if isinstance(schema_objs, list) else cursor.execute(query, (project.project_id, schema_objs.user_id))
        return True if cursor.rowcount > 0 else None

    def add_schema_project(self, project_id: Project | int | UUID, schema_ids: Schema | int | UUID | list[int | UUID]) -> bool:
        '''
        
        '''
        return self._add_schema_project(project_id = project_id, schema_ids = schema_ids)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    @connect
    def _get_project_schemas(self, cursor: psycopg.Cursor, project_id: Project | int | UUID) -> list[Schema] | None:
        '''
        
        '''
        cursor.row_factory = class_row(Schema)
        query = sql.SQL('''
            SELECT schemas.schema_id, name, created, modified, uuid FROM projectmanagement.schemas AS schemas 
            JOIN projectmanagement.projects_schemas AS projects_schemas ON projects_schemas.schema_id = schemas.schema_id 
            WHERE projects_schemas.project_id =  %s; ''')
        match project_id:
            case Project():
                cursor.execute(query, (project_id.project_id))
            case int():
                cursor.execute(query, (project_id,))
            case _:
                project = self._get_project(project_id)
                cursor.execute(query, (project.project_id,))
        schemas = cursor.fetchall()
        return schemas
    
    def get_project_schemas(self, project_id: Project | int | UUID) -> list[Schema] | None:
        '''
        
        '''
        return self._get_project_schemas(project_id = project_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Relationship Management - projectmanagement <-> projectmanagement: projects <-> herdunits
    
    @connect 
    def _get_project_herd_units(self, cursor: psycopg.Cursor, project_id: Project | int | UUID) -> list[HerdUnit] | None:
        '''
        
        '''
        cursor.row_factory = class_row(HerdUnit)
        query = sql.SQL('''
            SELECT herd_units.herd_unit_id, name, created, modified, uuid FROM projectmanagement.herd_units as herd_units JOIN
            projectmanagement.projects_herd_units AS projects_herd_units ON projects_herd_units.herd_unit_id = herd_units.herd_unit_id
            WHERE projects_herd_units.project_id = %s; ''')
        match project_id:
            case Project():
                cursor.execute(query, (project_id.project_id,))
            case int():
                cursor.execute(query, (project_id,))
            case _:
                project = self._get_project(project_id)
                cursor.execute(query, (project.project_id,))
        herd_units = cursor.fetchall()
        return herd_units

    def get_project_herd_units(self, project_id: Project | int | UUID) -> list[HerdUnit] | None:
        '''
        
        '''
        return self._get_project_herd_units(project_id = project_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Relationship Management - projectmanagement <-> projectmanagement: projects <-> surveys

    @connect 
    def _get_project_surveys(self, cursor: psycopg.Cursor, project_id: Project | int | UUID) -> list[Survey] | None:
        '''
        
        '''
        cursor.row_factory = class_row(Survey)
        query = sql.SQL('''
            SELECT surveys.survey_id, survey_year, name, additional_info, created, modified, uuid from projectmanagement.surveys AS surveys
            JOIN projectmanagement.projects_surveys AS projects_surveys ON projects_surveys.survey_id = surveys.survey_id 
            WHERE projects_surveys.project_id = %s; ''')
        match project_id:
            case Project():
                cursor.execute(query, (project_id.project_id,))
            case int():
                cursor.execute(query, (project_id,))
            case _:
                project = self._get_project(project_id)
                cursor.execute(query, (project.project_id,))
        surveys = cursor.fetchall()
        return surveys
                
    def get_projects_surveys(self, project_id: Project | int | UUID) -> list[Survey] | None:
        '''
        
        '''
        return self._get_project_surveys(project_id = project_id)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Relationship Management - projectmanagement <-> projectmanagement: projects <-> models
    
    @connect
    def _get_project_models(self, cursor: psycopg.Cursor, project_id: Project | int | UUID) -> list[Model] | None:
        '''
        
        '''
        cursor.row_factory = class_row(Model)
        query = sql.SQL(''' SELECT models.model_id, name, created, modified, uuid FROM projectmanagement.models AS models
                            JOIN projectmanagement.projects_models AS projects_models ON projects_models.model_id = models.model_id
                            WHERE projects_models.project_id = %s; ''')
        match project_id:
            case Project():
                cursor.execute(query, (project_id.project_id,))
            case int():
                cursor.execute(query, (project_id,))
            case _:
                project = self._get_project(project_id)
                cursor.execute(query, (project.project_id,))
        models = cursor.fetchall()
        return models
    
    def get_project_models(self, project_id: Project | int | UUID) -> list[Model] | None:
        '''
        
        '''
        return self._get_project_models(project_id = project_id)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Relationship Management - projectmanagement <-> projectmanagement: schemas <-> labels

    @connect
    def _get_schema_labels(self, cursor: psycopg.Cursor, schema_id: Schema | int | UUID) -> list[Label] | None:
        '''
        
        '''
        cursor.row_factory = class_row(Label)
        query = sql.SQL(' SELECT * FROM projectmanagement.labels WHERE schema_id = %s; ')
        match schema_id:
            case Schema():
                cursor.execute(query (schema_id.schema_id,))
            case int():
                cursor.execute(query, (schema_id,))
            case _:
                schema = self._get_schema(schema_id)
                cursor.execute(query, (schema.schema_id,))
        labels = cursor.fetchall() 
        return labels 

    def get_schema_labels(self, schema_id: Project | int | UUID) -> list[Label] | None:
        '''
        
        '''
        return self._get_schema_labels(schema_id = schema_id)
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Access Control - User Can Access

    @connect
    def _check_user_can_access_project(self, cursor: psycopg.Cursor, user_id: User |int | UUID, project_id: Project | int | UUID) -> bool:
        '''
        
        '''
        query = sql.SQL(' SELECT EXISTS (SELECT * FROM projectmanagement.projects_users WHERE user_id = %s AND project_id = %s); ')
        user = self._get_user(user_id) if not isinstance(user_id, User) else user_id
        project = self._get_project(project_id) if not isinstance(project_id, Project) else project_id
        if not user or not project:
            return False # A user cannot access a project that does not exist
        cursor.execute(query, (user.user_id, project.project_id))
        response = cursor.fetchone()
        return response[0]
    
    def check_user_can_access_project(self, user_id: User |int | UUID, project_id: Project | int | UUID) -> bool:
        '''
        
        '''
        return self._check_user_in_project(user_id = user_id, project_id = project_id)
            
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# class Database(ABC): # Abstract class for all database types
#     _conn: Any
#     _cursor: Any
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def __init__(self, root: os.PathLike):
#         self.schema = {}
#         # TODO: rework how this works
#         self.herd_units_forward = {}
#         self.herd_units_reverse = {}
#         self.models_forward = {}
#         self.models_reverse = {}
#         self.root = root

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     @abstractmethod 
#     def connect(self):
#         pass
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     @abstractmethod
#     def get_auto_increment_column(self):
#         pass
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def get_placeholder(self):
#         pass
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def create_tables(self):
#         if self._conn is None:
#             self.connect()
#         auto_increment_column = self.get_auto_increment_column()
    
#         # Create Models table
#         self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Models (
#                         ModelId {auto_increment_column},
#                         ModelName CHAR(19) NOT NULL UNIQUE
#                     )''')

#          # Create HerdUnit table
#         self._cursor.execute(f''' CREATE TABLE IF NOT EXISTS HerdUnits (
#                         HerdUnitID SERIAL NOT NULL PRIMARY KEY,
#                         HerdUnitName VARCHAR(6) NOT NULL UNIQUE
#                     )''')

#         # Create Images table
#         self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Images ( 
#                         ImageId {auto_increment_column},
#                         HerdUnitID INT,
#                         Name CHAR(50) NOT NULL UNIQUE,
#                         InTraining SMALLINT NOT NULL CHECK (InTraining IN (0, 1)),
#                         Reviewed SMALLINT NOT NULL CHECK (Reviewed IN (0, 1)),
#                         'Error' SMALLINT NOT NULL CHECK ('Error' IN (0, 1)),
#                         OPEN SMALLINT NOT NULL CHECK (OPEN IN (0, 1)),
#                         CropsGen INTEGER,
#                         FOREIGN KEY (HerdUnitID) REFERENCES HerdUnits (HerdUnitID)
#                     )''')

#         # Create Predictions table
#         self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Predictions (
#                         PredId {auto_increment_column},
#                         ModelId INTEGER,
#                         ImageId INTEGER,
#                         BoxTx SMALLINT,
#                         BoxTy SMALLINT,
#                         BoxBx SMALLINT,
#                         BoxBy SMALLINT, 
#                         Score FLOAT,
#                         Label SMALLINT,
#                         FOREIGN KEY (ImageId) REFERENCES Images (ImageId),
#                         FOREIGN KEY (ModelId) REFERENCES Models (ModelId)
#                     )''')

#         # Create Crops table
#         self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Crops (
#                         CropId {auto_increment_column},
#                         ImageId INTEGER NOT NULL,
#                         ModelId INTEGER NOT NULL,
#                         CropName VARCHAR(58) NOT NULL UNIQUE,
#                         InLabelBox INTEGER NOT NULL CHECK (InLabelBox IN (0, 1)),
#                         CropTx SMALLINT,
#                         CropTy SMALLINT,
#                         CropBx SMALLINT,
#                         CropBy SMALLINT,
#                         Created DATE,
#                         globalKey CHAR(36) UNIQUE,
#                         FOREIGN KEY (ImageId) REFERENCES Images (ImageId),
#                         FOREIGN KEY (ModelId) REFERENCES Models (ModelId)
#                     )''')

#         # Create CropPredictions table
#         self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS CropPredictions (
#                         CropPredId {auto_increment_column},
#                         CropId INTEGER,
#                         PredId INTEGER,
#                         ImageId INTEGER,
#                         BoxTx INTEGER,
#                         BoxTy INTEGER,
#                         BoxBx INTEGER,
#                         BoxBy INTEGER,
#                         FOREIGN KEY (CropId) REFERENCES Crops (CropId),
#                         FOREIGN KEY (PredId) REFERENCES Predictions (PredId),
#                         FOREIGN KEY (ImageId) REFERENCES Images (ImageId)
#                     )''') 

#         # Create Annotations table
#         self._cursor.execute(f'''CREATE TABLE IF NOT EXISTS Annotations (
#                         AnnotationId {auto_increment_column},
#                         CropID INT,
#                         BoxTx SMALLINT,
#                         BoxTy SMALLINT,
#                         BoxBx SMALLINT,
#                         BoxBy SMALLINT,
#                         FOREIGN KEY (CropID) REFERENCES Crops (CropID)
#                     )''')

#         # Create Training table
#         self._cursor.execute(f''' CREATE TABLE IF NOT EXISTS Training (
#                         ModelId INT,
#                         CropID INT,
#                         FOREIGN KEY (ModelId) REFERENCES Models (ModelId),
#                         FOREIGN KEY (CropId) REFERENCES CROPS (CropId),
#                         PRIMARY KEY (Modelid, Cropid)
#                     )''')
        
#         # Crete Schema table
#         self._cursor.execute(f''' CREATE TABLE IF NOT EXISTS Schema (
#                              SchemaId {auto_increment_column},
#                              label INT NOT NULL,
#                              name VARCHAR(30) NOT NULL,
#                              imagelink VARCHAR(1000)
#                     )''')

#         # Create user management schema
#         self._cursor.execute('''CREATE SCHEMA IF NOT EXISTS UserManagement;''')

#         #Create user table
#         self._cursor.execute(f''' CREATE TABLE IF NOT EXISTS UserManagement.Users (
#                              UserId {auto_increment_column},
#                             uuid UUID UNIQUE NOT NULL,
#                             userName VARCHAR(20) UNIQUE NOT NULL,
#                              ExternalAuthId VARCHAR(255) UNIQUE NOT NULL,
#                              ExternalAuthProvider VARCHAR(50) NOT NULL,
#                              Status VARCHAR(20) NOT NULL DEFAULT 'active',
#                              Role VARCHAR(50) NOT NULL DEFAULT 'user',
#                              Created date,
#                              Updated date,
#                              LastLogin TIMESTAMP WITHOUT TIME ZONE,
#                              locale VARCHAR(10)
#                              )''')
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#  
#     def create_indexes(self):
#         self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_reviewed ON Images (ReviewLed);')
#         self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_imageid ON Predictions (ImageId);')
#         self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_crops_imageid ON Crops (ImageId);')
#         self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_croppreds_cropid ON CropPredictions (CropId)')
#         self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_herdunit_herdunitid ON HerdUnits (herdunitid)')
#         self._cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_modelid on Models (modelid)')
        
#         self.commit()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def commit(self):
#         self.close()
#         self._conn.commit()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def query(self, query: str, params=None):
#         if not self._cursor:
#             print('no cursor')
#             self.connect()
#         query = query.replace('?', self.get_placeholder()) #type: ignore
#         self._cursor.execute(query, params or ())
#         if 'select' in query.strip().lower():
#             return self._cursor.fetchall()
#         else:
#             return self._cursor.rowcount
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     #User management methods
#     def get_user(self, external_id: str):
#         print("I was called")
#         query = '''
#             SELECT UserId, ExternalAuthId, Status, Role, Created, Updated, Locale, uuid, userName 
#             FROM usermanagement.users
#             WHERE ExternalAuthId = ?
#         '''

#         rows = self.query(query, (external_id,))
#         if len(rows) == 0:
#             return
#         return {
#             'db_id': rows[0][0],
#             'external_auth_id': rows[0][1],
#             'status': rows[0][2],
#             'role': rows[0][3],
#             'created': rows[0][4],
#             'updated': rows[0][5],
#             'locale' : rows[0][6],
#             'uuid' : rows[0][7],
#             'userName': rows[0][8]
#         }

#     def set_last_login(self, db_id: int):
#         query = '''
#             UPDATE usermanagement.users
#             SET LastLogin =  ?
#             WHERE userid = ?'''
#         self.query(query, (datetime.now().strftime('%Y%m%d %H%M%S'), db_id))
#         self.commit()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def lastrowid(self) -> int:
#         return self._cursor.lastrowid
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def rollback(self):
#         self._conn.rollback()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def close(self):
#         if self._conn:
#             self._conn.close
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def get_herd_units(self):
#         query = '''
#             SELECT * FROM herdunits
#         '''
#         rows = self.query(query,())

#         for id, name in rows:
#             self.herd_units_forward[id] = name
#             self.herd_units_reverse[name] = id
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def insert_herd_unit(self, herd_unit_name):
#         query = '''
#             INSERT INTO HerdUnits (HerdUnitName)
#             VALUES (?)
#             ON CONFLICT(HerdUnitName) DO NOTHING
#         '''      
#         self.query(query, (herd_unit_name,))
#         self.commit()
#         self.get_herd_units()
#  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#   
#     def get_models(self):
#         query = '''
#             SELECT * FROM models
#         '''
#         rows = self.query(query,())
#         for id, name in rows:
#             self.models_forward[id] = name
#             self.models_reverse[name] = id
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def insert_model(self, model_name):
#         query = '''
#             INSERT INTO Models (ModelName)
#             VALUES (?)
#             ON CONFLICT(ModelName) DO NOTHING
#         ''' 
#         self.query(query, (model_name,))   
#         self.commit()
#         self.get_models()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def resolve_herd_unit(self, herd_unit: int | str):
#         return self.herd_units_forward[herd_unit] if type(herd_unit) is int else self.herd_units_reverse[herd_unit]

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def resolve_model(self, model: int | str):
#         return self.models_forward[model] if type(model) is int else self.models_reverse[model]

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def resolve_label(self, label: int | str):
#         return self.labels_forward[label] if type(label) is int else self.labels_reverse[label]

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def set_open(self, image_id: int):
#         query = '''
#             UPDATE Images
#             SET Open = 1
#             WHERE ImageId = ?
#         '''
#         self.query(query, (image_id,))
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def set_closed(self, image_id: int):
#         query = '''
#             UPDATE Images
#             SET Open = 0
#             WHERE ImageId = ?
#         '''
#         self.query(query, (image_id,))
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def set_all_closed(self):
#         query = '''
#             UPDATE Images
#             Set Open = 0
#             WHERE Open = 1'''
#         self.query(query, ())
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def set_reviewed(self, image_id: int):
#         query = '''
#             UPDATE Images
#             SET Reviewed = 1
#             WHERE ImageId = ?
#         '''
#         self.query(query, (image_id,))
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def get_schema(self):
#         query = '''SELECT * FROM Schema'''
#         rows = self.query(query, ())
#         for row in rows:
#             self.schema[row[2]] = {
#                 'label': row[1],
#                 'image_link': row[3]
#             }

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def update_training(self, image_names: list, modelId):
#         for name in image_names:
#             query = '''
#                 SELECT CropId, imageID
#                 FROM Crops
#                 WHERE CropName = ?
#             '''
#             ids = self.query(query, (name,))
#             if len(ids) == 0:
#                 continue
#             query = ''' 
#                 INSERT INTO TRAINING (CropId, ModelId)
#                 VALUES (?, ?)
#                 ON CONFLICT (CropId, ModelId) DO NOTHING
#             '''
#             self.query(query, (ids[0][0], modelId))
#             query = '''
#                     UPDATE Images
#                     SET intraining = 1 
#                     WHERE Imageid = ?
#             '''
#             self.query(query, (ids[0][1],))
#             self.commit()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def insert_manual_crops(self, train_json_path: str, model_id: int):
#         prefix = len('high-altitude-pronghorn-survey-')
#         suffix = len('_crop_xx')
#         CURRENT_TIMESTAMP = datetime.date.today().strftime('%Y-%m-%d')

#         with open(train_json_path) as f:
#             train_json = json.load(f)

#         for image_info in train_json['images']:
#             query = '''
#                 SELECT ImageId 
#                 FROM Images
#                 WHERE Name = ?
#             '''
#             image_id = self.query(query, (os.path.splitext(image_info['file_name'])[0][prefix:-suffix],))[0][0]
#             query = '''
#                 INSERT INTO Crops (ImageId, modelId, CropName, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created, GlobalKey)
#                 Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                 ON CONFLICT(CropName) DO NOTHING
#             '''
#             self.query(query, (image_id, model_id, os.path.splitext(image_info['file_name'])[0][prefix:], 1, 0, 0, 0, 0, CURRENT_TIMESTAMP, str(uuid4()),))
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def populate_images(self, images: dict['str', Image], model_id: int, 
#                                    herd_id: int, insert_images: bool, insert_predictions: bool):  
        
      
#         image_count = len(images)
    
#         for num, image_dict in enumerate(images):
#             # add max score to image table, insert score based on prediction values
#             # /\ I have no clue what this talking about -ML 4/22/2025
#             print(f'inserting image {num}/{image_count}')
#             if insert_images:   
#                 query = '''
#                     INSERT INTO Images (Name, HerdUnitID, InTraining, Reviewed, "Error", CropsGen, Open)
#                     VALUES (?, ?, ?, ?, ?, ?, ?)
#                 '''
#                 try:
#                     self.query(query, (image_dict['image'].name, image_dict['image'].herd_unit.id, 1 if image_dict['image'].in_training == True else 0, 0, 0, 0, 0))
#                 except Exception as e: #TODO: Replace with generic exception
#                     print(e)
#                     continue
#             image_id = self.lastrowid()
    
#             if insert_predictions:
#                 print(f'inserting {len(image_dict['predictions'])} predictions...')
#                 for pred in image_dict['predictions']:
                    
#                     # Prediction level IOU would most likely be less efficient than comparing individual crops
#                     points = pred.dimensions.get_points()
#                     query = '''
#                         INSERT INTO Predictions (ImageId, ModelId, BoxTx, BoxTy, BoxBx, BoxBy, Score, Label)
#                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#                     '''
#                     try: 
#                         self.query(query, (image_id, pred.model.id, points[0], points[1], points[2], points[3], pred.score, pred.label)) #type: ignore
#                     except Exception as e: #TODO: replace with more generic catch
#                         print('Prediction Already in database...')
                    
#         # Async await commit from other workers 
#         self.commit() 
#         self.close() 
#         print("done")
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def insert_to_database(self, images: dict[Image, Prediction], herd_unit: HerdUnit, model: Model, bootstrap: bool=False, 
#                            insert_images: bool=True, insert_predictions: bool=True):
        
#         # Cache the model_id and herd_unit_id
#         model_id = model.id
#         herd_unit_id = herd_unit.id
        
#         self.populate_images(images,model_id, herd_unit_id, insert_images, insert_predictions)

#         # # Actual row insertion uses multiple processes to greatly speed up data insertion
#         # process_count = max(1, cpu_count())
#         # print(f'Inserting into the database on {process_count} threads...')
#         # total_images = len(images)
#         # chunk_size = (total_images + process_count - 1) // process_count # Size of each block of
#         # pool = Pool(processes = process_count)
#         # tasks = []

#         # # delegate chunks of total images to threads evenly
#         # for i in range(process_count):
#         #     start = i * chunk_size
#         #     end = (i + 1) * chunk_size if i != process_count - 1 else total_images
            
#         #     tasks.append((images[start:end], model_id, herd_unit_id, insert_images, insert_predictions))
            
#         # pool.starmap(self.concurrent_populate_images, tasks)
#         # pool.close()
#         # pool.join()

#         # #TODO: Go and update these methods BEFORE TESTING 
#         # if bootstrap:
#         #     self.insert_manual_crops(model_id)
#         # #self.update_training(model_id)
#         # #self.create_indexes()
#         # self.commit()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def insert_full(self, images: dict[Image, Prediction], herd_unit: HerdUnit, model: Model):
#         self.insert_to_database(images, herd_unit, model, bootstrap=False, insert_images=True, insert_predictions=True,)
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def insert_new_images(self):
#         self.insert_to_database(bootstrap=False, insert_images=True, insert_predictions=False)
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def insert_new_preds(self):
#         self.insert_to_database(bootstrap=False, insert_images=False, insert_predictions=False)
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def bootstrap_database(self):
#         ''' Populate a SQL database with image names and predictions

#             Returns None, populate tables in a database
#         '''
#         # First part is single threaded for simplicity purposes
#         self.create_tables()     
#         self.insert_to_database(bootstrap=True, insert_images=True, insert_predictions=True)
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def retrieve_batch(self, batch_size: int, desired_class: int, min_confidence: float,
#                     herd_unit_id: str, model_id: str) -> dict[Image, list[Prediction]]:
        
#         batch = {}
    
#         rows = self.get_pred_and_images(batch_size, desired_class, min_confidence, herd_unit_id, model_id)

#         for img in rows:
#             img_id =img['imageid']
#             self.set_open(img_id)
        
#             batch[img_id] = {}
#             image = Image(
#                 db_id = img_id,
#                 name = img['name'],
#                 herd_unit = HerdUnit(herd_unit_id, self.resolve_herd_unit(herd_unit_id), '2024'), #TODO: change with parameter passed with function cal,l
#                 in_training = True if img['intraining'] == 1 else False,
#                 local_path = os.path.join(self.root, 'Images', self.resolve_herd_unit(herd_unit_id)),
#                 )
#             batch[img_id]['image'] = image
#             batch[img_id]['predictions'] = []

#             for pred in img['predictions']:
#                 batch[img_id]['predictions'].append(
#                     Prediction(
#                         db_id = pred['PredId'],
#                         dimensions = Box(
#                             top_left = (pred['BoxTx'], pred['BoxTy']),
#                             bottom_right = (pred['BoxBx'], pred['BoxBy'])
#                         ),
#                         score = pred['Score'],
#                         label = pred['Label'],
#                         model = Model(model_id, self.resolve_model(model_id))
#                         )
#                 )
#         self.commit()
#         return batch
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def close_batch(self, batch: Dict[str, Union[Image, List[Prediction]]]):
#         for image_id in batch.keys():
#             self.set_closed(image_id)
#         self.commit()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def interrupt_handler(self, signum, frame):
#         usr_input = input(f"Interrupt signal: {signum} in {frame} recieved | IMPORTANT DON'T SAVE IF THERE WAS A PROBLEM | Save work? (Y or N): ")
#         if usr_input in set(['y', 'Y', 'yes', 'Yes', 's', 'S', 'Save', 'save']):
#             try:
#                 self.commit() 
#                 self.close() 
#             except Exception as e:
#                 print(f'Exception {e} encountered')
#                 os.exit()
#         else:    
#             self.rollback() 
#             self.close() 
#             os.exit()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def setup_interrupt_handler(self):
#         ''' Gracefully handle ^C interrupts regarding the database
        
#         '''
#         signal.signal(signal.SIGINT, self.interrupt_handler)
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def upload_crops(self, crops: dict[str, Union[Crop, list[Prediction]]]) -> int:
#         CURRENT_TIMESTAMP = datetime.now()
#         for crop_id in crops:
#             num_crops = 0
#             model_id = crops[crop_id]['predictions'][0].model.id
#             crop = crops[crop_id]['crop']
#             predictions = crops[crop_id]['predictions']
#             points = crop.crop_dimensions.get_points()
#             query = '''
#                 INSERT INTO Crops (ModelID, ImageId, CropName, InLabelBox, CropTx, CropTy, CropBx, CropBy, Created, GlobalKey)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             '''

#             self.query(query, (model_id, crop.image_id, crop.name, 0, points[0], points[1], points[2], points[3], CURRENT_TIMESTAMP, str(uuid4()))) 
#             num_crops += 1

#             for pred in predictions:
#                 points = pred.dimensions.get_points()
#                 query = '''
#                     INSERT INTO CropPredictions (CropId, PredId, ImageId, BoxTx, BoxTy, BoxBx, BoxBy)
#                     VALUES (?, ?, ?, ?, ?, ?, ?)
#                 '''
#                 self.query(query, (crop.id, pred.id, crop.image_id, points[0], points[1], points[2], points[3])) #type: ignore
            
#         self.commit() 

#  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def upload_to_labelbox(self, batch_size, desired_class: int, save_folder: str):
#         #TODO: update to use new data structures and derive save folder from image object to reduce number of args because you 
#         # (michael lance) are terrible at python
#         global uploading
#         if uploading:
#             return 
#         uploading = True
#         client = lb.Client(os.environ.get('API_KEY'))
#         project = client.get_project(os.environ.get('PROJECT_ID'))
#         dataset = client.get_dataset(os.environ.get('DATASET_ID'))

#         data_rows = []
#         global_keys = []
#         row_ids = []
#         labels = []

#         query = '''
#             SELECT C.CropId, C.CropName, C.GlobalKey
#             FROM Crops C 
#             WHERE C.InLabelBox = 0
#             LIMIT 50
#             '''
#         crops = base.query(query,(batch_size,)) #type: ignore
        
#         if len(crops) == 0: #type: ignore
#             print('No valid crops to upload, please approve predictions first!') #type: ignore
#             return
#         else:
#             print(f'\n{len(crops)} valid crops not yet uploaded to labelbox, working!') #type: ignore

#         for crop_info in crops: #type: ignore
#             data_rows.append({
#                 'row_data': f'{save_folder}/{crop_info[1]}.jpg',
#                 'global_key': crop_info[2],
#                 'external_id': crop_info[1]
#             })
#             query = '''
#                 UPDATE Crops 
#                 SET InLabelBox = 1 
#                 WHERE CropId = ?
#                 '''
#             self.query(query, (crop_info[0],))
#             global_keys.append(crop_info[2])
#             query = '''
#                 SELECT CP.BoxTx, BoxTy, BoxBx, BoxBy
#                 FROM CropPredictions CP
#                 WHERE ? = CP.CropId
#             '''
#             crop_preds = self.query(query,(crop_info[0],)) 
#             for pred_info in crop_preds: #type: ignore 
#                 labels.append(
#                     Label(
#                         data = {'global_key': crop_info[2]}, #type: ignore
#                         annotations = [
#                             ObjectAnnotation(
#                                 name = self.class_labels_forward[desired_class],
#                                 value = Rectangle(
#                                     start = Point(x = pred_info[0], y = pred_info[1]),
#                                     end = Point( x = pred_info[2], y = pred_info[3])
#                                 )
#                             )
#                         ]
#                     ) 
#                 )
#         # determine chunk_size from number of data_rows
#         num_data_rows = len(data_rows)
#         # Multiprocessing configuration
#         process_count = max(1, cpu_count())

#         if num_data_rows < process_count:
#             process_count = num_data_rows

#         print(f'Uploading to labelbox on {process_count} threads...')

#         chunk_size = (num_data_rows + process_count - 1) // process_count 
#         pool = Pool(processes = process_count)
#         tasks = []

#         for i in range(process_count):
#             start = i * chunk_size
#             end = (i + 1) * chunk_size if i != process_count - 1 else num_data_rows

#             tasks.append((data_rows, start, end, dataset))

#         pool.starmap(self.concurrent_upload, tasks)
#         print('got here')
#         pool.close()
#         pool.join()
#         base.commit() #type: ignore
#         # Request data rows associated with global_ids we generated for labelbox shenannigans
#         res = client.get_data_row_ids_for_global_keys(global_keys)
        
#         # loop over the dict to append the actual ids to a list that is useful to us
#         for id in res['results']:
#             row_ids.append(id)
        
#         project.create_batch(
#             name = f'high-altitude-pronghorn-survey-{str(uuid4())}', # add model name to batch
#             data_rows = row_ids, #type_ignore
#             priority = 5,
#         )
#     # Upload MAL label for this data row in project
#         lb.MALPredictionImport.create_from_objects(
#             client = client, 
#             project_id = project.uid, #type: ignore 
#             name='mal_job'+str(uuid4()), 
#             predictions=labels
#         )
#         print('Upload complete!')
#         uploading = False
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def concurrent_upload(data_rows, start, end, dataset):
#         task = dataset.create_data_rows(data_rows[start:end])
#         task.wait_until_done()
#         if task.errors:
#             print(task.errors)

# #---------------------------------------------------------------------------------------------------------------------------#
#     #TODO: Update sqlite class to work with updated features, eg: write get_pred_and_images method
# class SQLite(Database):
#     def __init__(self, db_config: dict):
#         try: 
#             import sqlite3
#             self._sqlite3 = sqlite3
#         except ImportError:
#             raise RuntimeError("sqlite3 module missing.")
        
#         self._db_name = db_config['database']
#         self._conn = None
#         self._cursor = None
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#             
#     def connect(self):
#         self._conn = self.sqlite3.connect(self._db_name)
#         self._cursor = self._conn.cursor()
#         self._cursor.execute('PRAGMA journal_mode = WAL;')
#         self._cursor.execute('PRAGMA cache_size = -20000;')
#         self._cursor.execute('PRAGMA synchronous = NORMAL;')
#         self._cursor.execute('PRAGMA temp_store = MEMORY;')
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def get_auto_increment_column(self) -> str:
#         return 'INTEGER PRIMARY KEY'
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#    
#     def get_placeholder(self) -> str:
#         return '?'
    
# #---------------------------------------------------------------------------------------------------------------------------#

# class Postgres(Database):
#     def __init__(self, db_config: dict, root: os.PathLike):
#         try: 
#             import psycopg
#             self._psycopg = psycopg
#         except ImportError:
#             raise RuntimeError("psycopg not installed. Please install it with 'pip install psycopg[binary]'")

#         super().__init__(root)
#         self._config = db_config
#         self._conn = None
#         self._cursor = None
#         self._dict_cursor = None
#         self._pooled_conn = None

#         self.connect()
#         self.get_herd_units()
#         self.get_models()
#         #self.get_schema()
#         self.close()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def connect(self):
#         try:
#             self._conn = self._psycopg.connect(**self._config) #type: ignore
#             self._cursor = self._conn.cursor()
#             self._dict_cursor = self._conn.cursor(row_factory=self._psycopg.rows.dict_row)
#         except (Exception, self._psycopg.DatabaseError) as error:
#             print(error)
        
        
#         #self.set_all_closed()
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def get_auto_increment_column(self) -> str:
#         return 'SERIAL NOT NULL PRIMARY KEY'

#     def get_placeholder(self) -> str:
#         return '%s'
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     def lastrowid(self) -> int:
#         self._cursor.execute('SELECT LASTVAL()')
#         return self._cursor.fetchone()[0]
#  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#     #TODO: Make abstract function in base class   
#     def get_pred_and_images(self, batch_size: int, desired_class: int, min_confidence: float, herd_unit_id: str, model_id: str) -> dict:
#         ''' Query batch_size Images and associated predictions above a minimum score from the database
        
#         Args:
#             batch_size: number of images that will consist a batch 
#             desired_class: integer id of desired class object derived from labelbox ontology
#             min_confidence: minimum confidence for fetched predictions
#             herd
            
#         Returns true if image_name is origin of one of the training images.
#         '''

       
#         print('Querying database...')
#         query = '''
#             WITH SelectedImageIds AS (
#                 SELECT DISTINCT I.ImageId
#                 FROM Images I
#                 INNER JOIN Predictions P ON I.ImageId = P.ImageId
#                 WHERE I.HerdUnitId = %s
#                     AND I.Reviewed = %s
#                     AND I.Open = 0
#                     AND P.Label = %s
#                     AND P.Score > %s
#                 LIMIT ?
#             )
#             SELECT json_agg(row_to_json(img_preds))
#             FROM (
#                 SELECT
#                     I.ImageId,
#                     I.Name,
#                     I.InTraining,
#                     json_agg(
#                         json_build_object(
#                             'PredId', P.PredId,
#                             'BoxTx', P.BoxTx,
#                             'BoxTy', P.BoxTy,
#                             'BoxBx', P.BoxBx,
#                             'BoxBy', P.BoxBy,
#                             'Score', P.Score,
#                             'Label', P.Label
#                         )
#                         ORDER BY P.Score DESC
#                     ) AS predictions
#                 FROM Images I
#                 INNER JOIN Predictions P ON I.ImageId = P.ImageId
#                 WHERE I.ImageId IN (SELECT ImageId FROM SelectedImageIds)
#                     AND P.Label = %s
#                     AND P.Score > %s
#                     AND P.ModelId = %s
#                 GROUP BY I.ImageId, I.Name, I.InTraining
#             ) AS img_preds;
#         '''
#         rows = self.query(query, (herd_unit_id, 0, desired_class, min_confidence, batch_size, desired_class, min_confidence, model_id,)) #type: ignore
        
#         if type(rows) == 'None':
#             raise BatchError("Database returned empty, please adjust your parameters!")
#         else:
#             return rows[0][0]

# #---------------------------------------------------------------------------------------------------------------------------#
# # Custom Exceptions

# class  BatchError(Exception):
#     def __init__(self, message):
#         self.message = message
#         super().__init__(self.message)