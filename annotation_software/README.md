# Assisted Labeling & Census Software

The annotation software is an SPA (Single Page Application) written in VueJS designed to assist in the production of labeled training data by implementing a method known as model assisted labeling with a few creative twists. In a greater scope, this tool is envisioned to be a ubiquitous tool for managing wildlife census projects using computer vision models. The goal is to create an intuitive interface that allows for the rapid scalining of specialized models capable of accurately tracking herd populations with minimal human oversight. 

## Deployment

This tool is designed to be easily and rapidly scalable using containerization tools such as podman or docker. The included compose and container files are compatible with any containerization service that implements the [OCI](https://opencontainers.org/) (Open Container Initiative) standards. It is recommended to deploy this project to a linux system, primarily as a windows based deployment has not currently been tested. This project was designed with modularity at its core, meaning each component in the stack can be used in isolation. For example, one could take the API and the database and write their own front end.

## Tech Stack



* Postgresql [logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"

* Flask
* Gunicorn
* Valkey
* VueJS with Typescript
* Nginx

### Major Components

1. **API:** The glue that holds this project together is its flask-based restful API built on top of a  custom database abstraction layer built with the psycopg3 package.

2. **Auto Cropper:** The auto cropper python package automates the process of creating cropped training data by leveraging machine learning predictions and human verification to dramatically increase the rate at which data can be prepared. 

3. **Database:** This project makes use of the SQL relational database Postgresql, which enables the rapid management of structured relational data (such as machine learning predictions and annotations).

4. **Frontend** The frontend is a lazily loaded SPA (Single Page Application) built with VueJS and typescript, allowing for a feature rich, high performance front end that enables a seamless user experience.

### Database Abstraction

In the interest of performance and scalability we opted not to use an ORM (Object Relational Mapper), and instead write our own SQL queries to be executed using the excellent [psycopg3](https://pypi.org/project/psycopg/) package. Our abstraction layer is a semi typed OOP module that makes use of a decorated private interface wrapped into a context manager that handles the connection pool. Effectively the entire context of the connection is abstracted away from the API layer. The database layer also automatically associates rows from Postgres to their class defined in the crop generator, effectively emulating one of the benefits of an ORM while avoiding the performance related drawbacks.

```python

	import database as db # Generic name for increased performance

	db_config = {
		'dbname': x,
		'user': y,
		'password': z,
		...
	}

	base = db.Database(db_config) # Instantiate with config dictionary

	project = base.create_project('example') # Object is created in the database and python, connection is automatically handeled by the package.

	print(project.name)

	project.name = 'example_2'

	base.update_project(project) # Database is informed of the change

	# Objects can also be modified directly by passing kwargs to to the update_x() method for the object. Valid keywords are parsed and safely converted using psycopg's built in SQL library and used to construct the appropriate query. This is NOT generated sql per se. 
	base.update_project(project, name='example_3')
```

The choice to write our own abstraction layer was very deliberate; there are well documented issues with ORMs such as sqlAlchemy when considering complex relationships and performance scaling for complex multi-user applications. The goal was to as closely emulate the ease of use of an ORM while avoiding the massive overhead and inefficient generated SQL statements. We did not make a better ORM, we made a high performance specialized abstraction layer specifically for this project.

