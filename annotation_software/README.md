# Computer Vision 

This project relies on the koger_detection package available [here](https://github.com/benkoger/detection-projects).

If existing model exists, useful notebooks are notebooks/detection/inference.ipynb for processing many images and saving the results and notebooks/detection/examine_results.ipynb for visualizing detections.

# Assisted Labeling & Census Software

This project contains an SPA (Single Page Application) written in VueJS designed to assist in the production of labeled training data by implementing a method known as model assisted labeling with a few creative twists. In a greater scope, this tool is envisioned to be a ubiquitous tool for managing wildlife census projects using computer vision models. The goal is to create an intuitive interface that allows for the rapid scalining of specialized models capable of accurately tracking herd populations with minimal human oversight. 

## Deployment

This tool is designed to be easily and rapidly scaleable using containerization tools such as podman or docker. The included compose and contianer files are compatabile with any containerization service that implements the [OCI](https://opencontainers.org/) (Open Contianer Initiative) standards. It is reccomended to deploy this project to a linux system, primarily as a windows based deployment has not currently been tested. This project was designed with modularity at its core, meaning each component in the stack can be used in issolation. For example, one could take the API and the database and write their own front end. 

## Tech Stack

* Postgresql
* Flask
* Gunicorn
* Valkey
* VueJS with Typescript
* Nginx

### Major Components

1. **API:** The glue that holds this project together is its flask-based restful API built ontop of a  custom database abstraction layer built with the psycopg3 package.

2. **Auto Cropper:** The auto cropper python package automates the process of creating cropped training data by leveraging machine learning predictions and human verification to dramatically increase the rate at which data can be prepared. 

3. **Database:** This project makes use of the SQL relational database Postgresql, which enables the rapid management of structured relational data (such as machine learning predictions and annotations).

4. **Frontend** The frontend is a lazily loaded SPA (Single Page Application) built with VueJS and typescript, allowing for a feature rich, high performance front end that enables a seamless user experience.

### Database Abstraction

In the interest of performance and scaleability we opted not to use an ORM (Object Relational Mapper), and instead write our own SQL queries to be executed using the excellent [psycopg3](https://pypi.org/project/psycopg/) package. Our abstraction layer is a semi typed OOP module that makes use of a decorated private interface wraped into a context manager that handles the connection pool. Effectively the entire context of the conection is abstracted away from the API layer. The database layer also automatically associates rows from Postgres to their class defined in the crop generator, effectively emulating one of the benefits of an ORM while avoiding the performance related drawbacks. 

```python

	import database as db

	db_config = {
		'dbname': x,
		'user': y,
		'password': z,
		...
	}

	base = db.Database(db_config) # Instantiate with config dictionary

	project = base.create_project('example') # object is created in the database and python

	print(project.name)

	project.name = 'example_2'

	base.update_project(project) # database is informed of the change

	# objects can also be modified directly

	base.update_project(project, 'example_3')

```

To ensure high performance and rapid elasticity our abstraction layer implements connection pooling to avoid the network based constraint associated with creating connections on as needed basis. This is handeled entirely on the 