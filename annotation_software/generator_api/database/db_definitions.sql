-- UUID default: DEFAULT gen_random_uuid()
-- Date default: DEFAULT CURRENT_DATE

-- Drop all user-defined schemas (excluding system schemas like public, pg_catalog, information_schema)
DO $$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT nspname FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname != 'information_schema' AND nspname != 'public') LOOP
        EXECUTE 'DROP SCHEMA IF EXISTS ' || quote_ident(r.nspname) || ' CASCADE;';
    END LOOP;
END $$;

CREATE SCHEMA core;

CREATE SCHEMA usermanagement;

CREATE SCHEMA projectmanagement;

CREATE TABLE core.images (
  image_id serial PRIMARY KEY,
  herd_unit_id integer NOT NULL DEFAULT 0,
  name varchar(50) NOT NULL,
  in_training boolean DEFAULT false,
  crops_generated smallint DEFAULT 0,
  reviewd_by_user_id integer NOT NULL DEFAULT 0,
  opened_by_user_id integer NOT NULL DEFAULT 0,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  image_length_px integer NOT NULL,
  image_width_px integer NOT NULL,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE core.predictions (
  pred_id bigserial PRIMARY KEY,
  image_id integer NOT NULL,
  model_id integer NOT NULL DEFAULT 0,
  score double precision NOT NULL,
  label_id integer NOT NULL DEFAULT 0,
  box_tx integer NOT NULL,
  box_ty integer NOT NULL,
  box_bx integer NOT NULL,
  box_by integer NOT NULL,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE core.reviewed_area (
  reviewed_area_id serial PRIMARY KEY,
  image_id integer NOT NULL,
  area_tx integer NOT NULL,
  area_ty integer NOT NULL,
  area_bx integer NOT NULL,
  area_by integer NOT NULL,
  reviewed_areaLengthPx integer NOT NULL DEFAULT 2100,
  reviewed_areaWidthPx integer NOT NULL DEFAULT 2100,
  reviewd_by_user_id integer NOT NULL DEFAULT 0,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE core.annotations (
  annotation_id serial PRIMARY KEY,
  label_id integer NOT NULL DEFAULT 0,
  image_id integer NOT NULL,
  herd_unit_id integer NOT NULL DEFAULT 0,
  box_tx integer NOT NULL,
  box_ty integer NOT NULL,
  box_bx integer NOT NULL,
  box_by integer NOT NULL,
  created_by_user_id integer NOT NULL,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE core.reviewed_area_predictions (
  pred_id bigint,
  reviewed_area_id integer,
  PRIMARY KEY (pred_id, reviewed_area_id)
);

CREATE TABLE core.training (
  reviewed_area_id integer,
  model_id integer,
  PRIMARY KEY (reviewed_area_id, model_id)
);

CREATE TABLE core.annotations_reviewed_area (
  annotation_id integer,
  reviewed_area_id integer,
  PRIMARY KEY (annotation_id, reviewed_area_id)
);

CREATE TABLE usermanagement.users (
  user_id serial PRIMARY KEY,
  username varchar(20) NOT NULL,
  external_auth_id varchar(255),
  external_auith_provider varchar(50),
  status varchar(20) NOT NULL DEFAULT 'active',
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  last_login timestamptz,
  locale varchar(10),
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE usermanagement.roles (
  role_id serial PRIMARY KEY,
  role varchar(25) NOT NULL,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE usermanagement.organizations (
  organization_id serial PRIMARY KEY,
  name varchar(50),
  logo_url varchar(200),
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE usermanagement.users_roles (
  user_id integer,
  role_id integer,
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE usermanagement.organizations_projects (
  project_id integer,
  organization_id integer,
  PRIMARY KEY (project_id, organization_id)
);

CREATE TABLE usermanagement.organizations_users (
  user_id integer,
  organization_id integer,
  PRIMARY KEY (user_id, organization_id)
);

CREATE TABLE projectmanagement.projects (
  project_id serial PRIMARY KEY,
  name varchar(50) NOT NULL,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE projectmanagement.schemas (
  schema_id serial PRIMARY KEY,
  name varchar(30) NOT NULL,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE projectmanagement.labels (
  label_id serial PRIMARY KEY,
  schema_id integer NOT NULL DEFAULT 0,
  label smallint NOT NULL,
  name varchar(50) NOT NULL,
  image_link varchar(200),
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE projectmanagement.herd_units (
  herd_unit_id serial PRIMARY KEY,
  name varchar(30) NOT NULL,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE projectmanagement.models (
  model_id serial PRIMARY KEY,
  name varchar(30) NOT NULL,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE projectmanagement.surveys (
  survey_id serial PRIMARY KEY,
  survey_year integer NOT NULL,
  name varchar(50),
  additional_info text,
  created date NOT NULL DEFAULT CURRENT_DATE,
  modified date NOT NULL DEFAULT CURRENT_DATE,
  uuid uuid UNIQUE NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE projectmanagement.projects_users (
  project_id integer,
  user_id integer,
  PRIMARY KEY (project_id, user_id)
);

CREATE TABLE projectmanagement.projects_schemas (
  project_id integer,
  schema_id integer,
  PRIMARY KEY (project_id, schema_id)
);

CREATE TABLE projectmanagement.herd_units_projects (
  project_id integer,
  herd_unit_id integer,
  PRIMARY KEY (project_id, herd_unit_id)
);

CREATE TABLE projectmanagement.models_projects (
  project_id integer,
  model_id integer,
  PRIMARY KEY (project_id, model_id)
);

CREATE TABLE projectmanagement.surveys_projects (
  survey_id integer,
  project_id integer,
  PRIMARY KEY (survey_id, project_id)
);

CREATE TABLE projectmanagement.surveys_herd_units (
  survey_id integer,
  herd_unit_id integer,
  PRIMARY KEY (survey_id, herd_unit_id)
);

CREATE INDEX ON core.images (herd_unit_id);

CREATE INDEX ON core.images (created);

CREATE INDEX ON core.images (uuid);

CREATE INDEX ON core.predictions (label_id);

CREATE INDEX ON core.predictions (score);

CREATE INDEX ON core.predictions (image_id);

CREATE INDEX ON core.predictions (created);

CREATE INDEX ON core.predictions (uuid);

CREATE INDEX ON core.reviewed_area (image_id);

CREATE INDEX ON core.reviewed_area (created);

CREATE INDEX ON core.reviewed_area (reviewed_areaLengthPx, reviewed_areaWidthPx);

CREATE INDEX ON core.reviewed_area (uuid);

CREATE INDEX ON core.annotations (label_id);

CREATE INDEX ON core.annotations (image_id);

CREATE INDEX ON core.annotations (uuid);

CREATE INDEX ON core.annotations (created);

CREATE INDEX ON usermanagement.users (status);

CREATE INDEX ON usermanagement.users (modified);

CREATE INDEX ON usermanagement.users (last_login);

CREATE INDEX ON usermanagement.users (locale);

CREATE INDEX ON usermanagement.users (uuid);

CREATE INDEX ON usermanagement.roles (role);

CREATE INDEX ON usermanagement.roles (created);

CREATE INDEX ON usermanagement.roles (uuid);

CREATE INDEX ON projectmanagement.projects (name);

CREATE INDEX ON projectmanagement.projects (created);

CREATE INDEX ON projectmanagement.projects (uuid);

CREATE INDEX ON projectmanagement.schemas (name);

CREATE INDEX ON projectmanagement.schemas (created);

CREATE INDEX ON projectmanagement.schemas (uuid);

CREATE INDEX ON projectmanagement.labels (schema_id, label);

CREATE INDEX ON projectmanagement.labels (uuid);

CREATE INDEX ON projectmanagement.labels (created);

CREATE INDEX ON projectmanagement.herd_units (name);

CREATE INDEX ON projectmanagement.herd_units (uuid);

CREATE INDEX ON projectmanagement.herd_units (created);

CREATE INDEX ON projectmanagement.models (name);

CREATE INDEX ON projectmanagement.models (uuid);

CREATE INDEX ON projectmanagement.models (created);

CREATE INDEX ON projectmanagement.surveys (name);

CREATE INDEX ON projectmanagement.surveys (uuid);

CREATE INDEX ON projectmanagement.surveys (created);

ALTER TABLE core.images ADD FOREIGN KEY (herd_unit_id) REFERENCES projectmanagement.herd_units (herd_unit_id) ON DELETE SET DEFAULT ON UPDATE CASCADE;

ALTER TABLE core.images ADD FOREIGN KEY (opened_by_user_id) REFERENCES usermanagement.users (user_id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE core.images ADD FOREIGN KEY (reviewd_by_user_id) REFERENCES usermanagement.users (user_id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE core.predictions ADD FOREIGN KEY (image_id) REFERENCES core.images (image_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE core.predictions ADD FOREIGN KEY (label_id) REFERENCES projectmanagement.labels (label_id) ON DELETE SET DEFAULT ON UPDATE CASCADE;

ALTER TABLE core.predictions ADD FOREIGN KEY (model_id) REFERENCES projectmanagement.models (model_id) ON DELETE SET DEFAULT ON UPDATE CASCADE;

ALTER TABLE core.reviewed_area ADD FOREIGN KEY (image_id) REFERENCES core.images (image_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE core.reviewed_area ADD FOREIGN KEY (reviewd_by_user_id) REFERENCES usermanagement.users (user_id);

ALTER TABLE core.annotations ADD FOREIGN KEY (image_id) REFERENCES core.images (image_id) ON DELETE SET DEFAULT ON UPDATE CASCADE;

ALTER TABLE core.annotations ADD FOREIGN KEY (label_id) REFERENCES projectmanagement.labels (label_id) ON DELETE SET DEFAULT ON UPDATE CASCADE;

ALTER TABLE projectmanagement.labels ADD FOREIGN KEY (schema_id) REFERENCES projectmanagement.schemas (schema_id) ON DELETE SET DEFAULT ON UPDATE CASCADE;

ALTER TABLE core.reviewed_area_predictions ADD FOREIGN KEY (pred_id) REFERENCES core.predictions (pred_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE core.reviewed_area_predictions ADD FOREIGN KEY (reviewed_area_id) REFERENCES core.reviewed_area (reviewed_area_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE core.training ADD FOREIGN KEY (model_id) REFERENCES projectmanagement.models (model_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE core.training ADD FOREIGN KEY (reviewed_area_id) REFERENCES core.reviewed_area (reviewed_area_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE core.annotations_reviewed_area ADD FOREIGN KEY (annotation_id) REFERENCES core.annotations (annotation_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE core.annotations_reviewed_area ADD FOREIGN KEY (reviewed_area_id) REFERENCES core.reviewed_area (reviewed_area_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE usermanagement.users_roles ADD FOREIGN KEY (role_id) REFERENCES usermanagement.roles (role_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE usermanagement.users_roles ADD FOREIGN KEY (user_id) REFERENCES usermanagement.users (user_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE usermanagement.organizations_projects ADD FOREIGN KEY (project_id) REFERENCES projectmanagement.projects (project_id);

ALTER TABLE usermanagement.organizations_projects ADD FOREIGN KEY (organization_id) REFERENCES usermanagement.organizations (organization_id);

ALTER TABLE usermanagement.organizations_users ADD FOREIGN KEY (user_id) REFERENCES usermanagement.users (user_id);

ALTER TABLE usermanagement.organizations_users ADD FOREIGN KEY (organization_id) REFERENCES usermanagement.organizations (organization_id);

ALTER TABLE projectmanagement.projects_users ADD FOREIGN KEY (user_id) REFERENCES usermanagement.users (user_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.projects_users ADD FOREIGN KEY (project_id) REFERENCES projectmanagement.projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.projects_schemas ADD FOREIGN KEY (schema_id) REFERENCES projectmanagement.schemas (schema_id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE projectmanagement.projects_schemas ADD FOREIGN KEY (project_id) REFERENCES projectmanagement.projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.herd_units_projects ADD FOREIGN KEY (herd_unit_id) REFERENCES projectmanagement.herd_units (herd_unit_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.herd_units_projects ADD FOREIGN KEY (project_id) REFERENCES projectmanagement.projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.models_projects ADD FOREIGN KEY (project_id) REFERENCES projectmanagement.projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.models_projects ADD FOREIGN KEY (model_id) REFERENCES projectmanagement.models (model_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.surveys_projects ADD FOREIGN KEY (survey_id) REFERENCES projectmanagement.surveys (survey_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.surveys_projects ADD FOREIGN KEY (project_id) REFERENCES projectmanagement.projects (project_id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE projectmanagement.surveys_herd_units ADD FOREIGN KEY (survey_id) REFERENCES projectmanagement.surveys (survey_id);

ALTER TABLE projectmanagement.surveys_herd_units ADD FOREIGN KEY (herd_unit_id) REFERENCES projectmanagement.herd_units (herd_unit_id);


-- NOT AUTO GENERATED, DEFAULT ENTRIES -- DO NOT DELETE

INSERT INTO usermanagement.users (user_id, username, Status) VALUES (0, 'NO_USER', 'DISABLED');

INSERT INTO usermanagement.roles (role_id, role) VALUES (0, 'NO_ROLE');

INSERT INTO usermanagement.organizations (organization_id, name) VALUES (0, 'NO_ORGANIZATION');

INSERT INTO projectmanagement.herd_units (herd_unit_id, name) VALUES (0, 'NO_HERD_UNIT');

INSERT INTO projectmanagement.models (model_id, name) VALUES (0, 'NO_MODEL');

INSERT INTO projectmanagement.schemas (schema_id, name) VALUES (0, 'NO_SCHEMA');

INSERT INTO projectmanagement.labels (label_id, label, name) VALUES (0, -9999, 'NO_label');

INSERT INTO projectmanagement.projects (project_id, name) VALUES (0, 'NO_PROJECT');

INSERT INTO projectmanagement.surveys (survey_id, survey_year) VALUES (0, 1900);

INSERT INTO usermanagement.users_roles (user_id, role_id) VALUES (0, 0);

INSERT INTO usermanagement.organizations_users (user_id, organization_id) VALUES (0, 0);

INSERT INTO usermanagement.organizations_projects (project_id, organization_id) VALUES (0, 0);

INSERT INTO projectmanagement.projects_users (project_id, user_id) VALUES (0, 0);

INSERT INTO projectmanagement.projects_schemas (project_id, schema_id) VALUES (0, 0);

INSERT INTO projectmanagement.herd_units_projects (herd_unit_id, project_id) VALUES (0, 0);

INSERT INTO projectmanagement.models_projects(model_id, project_id) VALUES (0, 0);

INSERT INTO projectmanagement.surveys_projects(survey_id, project_id) VALUES (0, 0);

INSERT INTO projectmanagement.surveys_herd_units(survey_id, herd_unit_id) VALUES (0, 0);