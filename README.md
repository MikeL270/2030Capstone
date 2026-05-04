## Capstone Milestone 2: ETL Prototype
This repo holds my submission for the SDEV-2030 Capstone Milestone 2 assignment. This repo is a fork from the pronghorn-census repo becuase the submission is reliant on the greateer context of the project. I am not attempting to submit the entire repo as the pipeline, I will clearly list the relevant new code in this readme. 

## Data Source & Transform Notice (important)
In order to assist you in finding what to grade, I have outlined my thinking. I worked as close to the letter of the assignment as I could. **The reflection is found at the end of this file.**

### Data Source
The data source is described as either:
* CSV file(s)
* API
* Multiple files or _generated data_

**Important:** User generated data (input) qualifies as 'generated' data. The data caputured in the forms found in the wizard satisfy the non-trivial requirement, please keep in mind that not all complexity is immediately evident when simply interacting with the wizard.

### Transformation
If it is not immediately obvious, the data is **NOT** just pushed into the respective tables. The pipeline flows **through the whole stack**, from user input -> validation -> authorization -> insertion -> response. This requires multiple complex steps to process / fetch required data in order to construct the final objects. For instance, the organization_id and role_ids found in the createUserOptions interface are used to make separate requests to fetch data from the database needed to create the user object. 

#### Where to find transformation
Start with _'/generator_web_app/src/pages/intialSetup.vue'_, this file provides a paper trail to the various typescript modules and pinia stores used in the transformation of input. The following is a list of notable examples for transormation: 
* **User Store:** _'/generator_web_app/src/modules/stores/userSTore.ts'_ Acts as a seam between front end components and is the central repository for data relating to users in the context of this prototype. The store resturctures data from the API, such as organizations and roles, and exposes an api contract used to interact with that data.
* **create<object>.vue"** _'/generator_web_app/src/components/templates/create<object>.vue'_ Are vue components that take user input, validate it, then kick it back to the store in order to be sent asynchronously to the API.
* **API Routers:** _'airial_api/app/routers/<object>.py'_ Are flask blueprints that expose the api routes used by the userStore from the front end. They call methods from _database.py_.
* **Database.py:** _'airial_api/database/database.py'_ Is a database abstraction layer built with psycopg3 that interacts with a postgres database defined in the various compose options. This file is 3,648 lines long, I suggest you find the relevant methods by insepcting the routers and then using 'go to definition'.
* **Data classes and Pydantic classes:** _'/airial_api/database/ojbect_models/*'_ Are a set of python scripts containing definitions for objects from the database and definitions for request bodies and query parameters. 
 
## Running the prototype 
Since my prototype is directly integrated into Airial, this repo is a fork of the original project. 

### Requirements

* **Some Computer, Somewhere:** Thanks to our microservice architecture, this tool can be hosted on one big computer, or a few smaller computers. This guide assumes you will be using one big computer. It will be up to you to alter the compose files if they wish to alter the configuration. We do not want your custom compose files, so please do not commit them back to us.
  
* **Podman and Podman-Compose **OR** Docker and Compose Version:**
	* *podman: 5.7.1*
  	* *podman-compose: 1.5.0*
  	* *docker: 28.3.3* 
  	* *docker compose: 2.39.1* 

### Secrets

Below is a list of *secrets* that must be provided to the application in order for it work correctly. These secrets should be placed inside of a *.env* file in the same directory as the compose files. These secrets must either sourced or produced by the end user for their instance of the application. Note that the entirety of this application can be hosted on-prem, in the cloud, or in a hybrid structure, where you choose to host components will determine how you source quite a few of these secrets. 

* **APPLICATION_URL** -- This is the url the application will be served from. 

* **SECRET_KEY** -- The secret key is used by *flask_session* to cryptographically sign user session tokens to protect against common types of attacks such as Cross Site Request Forgery (CSRF) and ensure *cookie* integrity. This key is simply a unique, random string with a high degree of *entropy* that should not be reused between deployments. Reccomending a source to generate this key would be counter productive, and eventually we will implement a system for auto-generating this key for you.
  
* **VALKEY_HOST** -- The valkey host secret stores the URL for the valkey instance. If your database is one of the containers then you can simply use the name of the container. 

* **VALKEY_PASS** -- The valkey pass is used to control access to the cache server. Even if your valkey cache is on-prem it is still important to keep it secure.

* **AWS_ENDPOINT_S3** -- This secret stores the URL for your S3 compliant object storage provider of choice. Note that you are not required to use AWS, but you can if you want to.

* **DB_HOST** -- This secret stores the URL for the postgres database. If your database is one of the containers then you can simply use the name of the container.

* **DB_USER** -- This is the user in the database that will be used by the API to access data.

* **DB_PASS** -- This is the password associated with the above user.

* **DB_NAME** -- This is the name of the database.

* **AWS_ACCESS_KEY_ID** -- This is a key provided by your S3 compliant storage provider.

* **AWS_SECRET_ACCESS_KEY** -- This is another key provided by your S3 compliant storage provider. 

## Local development mode set up

Airial is designed to be ran in an enterprise environment consisting of multiple servers, this is largely due to the sheer volume of data its designed to handle. In order to scale out who can test and contribute to our software we have produced a set of containers built to be ran on a single host. Note that an internet connection is still required as we determined virtualizing a ceph cluster on the average laptop would somewhat- entirely futile. To get around this we have made a publicly accessible sampleset of imagery and a directory archive of a database relevant to those images available publicly. 

To run the local dev environment you must have a container orchestration tool installed on your system. The reccomended container orchestration platform is Podman with Podman-Compose. However, note that there currently is an issue on intel based macbooks that cause the podman machine to hang indefinitey, so intel mac users are reccomended to use docker. The commands are the same for both tool. Note that for both windows and macOS users a virtualization capable computer is required since those operating systems still do not support native containerization. 

After cloning down the repository, **you must create and populate a .env file in the root of the directory. Failrue to do so will result in a non functional prototype due to user error.** 

Once you have a propperly populated .env file standing up the system should go off without a hitch. 

### Linux & Applie Silicon Mac systems running Podman

```sh
	podman compose --f bootstrap-dev.compose.yml up -d
```

### Intel based Mac systems running Docker

```sh
	docker compose --f bootstrap-dev.compose.yml up -d
```

### Windows system 

**Important:** _Windows may automatically convert the restore.sh script in the local_db directory to use **CRLF** insead of **LF** ensure that this file is restored to use **LF** or never converted at all. Additional for some reason Windows podman's file flag uses one dash instead of two._

```powershell
	podman compose -f bootstrap-dev.compose.yml up -d
```

## Reflection

### What part of your pipeline is currently working?
The first few steps of the initial set up wizard, creating a super user, creating an organization, and then creating an admin for that organization. The whole pipeline for these steps is fully integrated.

### What parts are incomplete or simplified?
Right now the wizard is not fully complete. This is because of assignments like this that force us to rush our work and rob us of our weekends. The rest of the wizard will be completed for the full submission. 

### What challenges did you encounter?
Tight deadlines. This assignment being given alongside the regular weekend slogfest made it incredibly difficult with long hours to build anything. I am sure this assignment is justified as being "for my benefit," but the amount of caffiene I had to consume to meet this deadline had a non trivial impact on my health. The fact that working a national lab this summer feels relaxxing compared to these stress-tumor inducing weekend crams is seriously disturbing. 

### What are your next steps before the final submission?
Next steps include polishing the existing steps as well as creating the last few steps in the wizard. After that I will create the data manager interface that must be graded in the traditional development mode with propper access ARCC s3. The multi org structure of the system makes this a challenging, multifaceted task.
