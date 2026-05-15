# SDEV2030 Capstone 

This repository contains the ETL Prototype submission for the SDEV-2030 Capstone Milestone 2 assignment. It is a fork of the `pronghorn-census` repository, as the prototype is integrated into the broader Airial project architecture.

---

## Project Overview
The goal of this project is to provide a repeatable process for deploying the AIrial software suite, and tooling for managing the data inside the system. Due to the size of the schema involved, and the scale of a fully featured system, currently the system only supports basic operations. The API supports full CRUD across most object domains, and the UI implements a sligthly smaller set of those operations. The goal is to strategically provide functionality as the need is encountered to ensure that important work is not bottlenecked by unfocused development. 

This submission includes three components.
 1. An explicit ETL pipeline for ingesting user records from a `csv` file. The rest of the system relies on data restored from a Postgresql directory backup. This enables the system to use a hybrid of real and generated data. THis is optimal compared to attempting to demo an entire computer vision pipeline, which is the real world implementation developed by Drs Koger, and Martin, which makes use of my API to populate predictions in real time. This requries significant compute resources and time due to the complexity of convolutional neural networks. 
 2. An empty initial setup first run wizard that configures the system properly for use.
 3. A comparatively `basic` datamanagement system that supports manaing container types present in the schema. This is the core of the management system where query outputs will be most visible. This serves as a solid starting point for a more advanced implementation in the future, and addresses a common pain point found in the current production version of Airial.

### Data Source
The ETL pipeline is primarily detailed in a Juptyer notebook that ingests user data into the system, this goes beyond basic insert statements, and uses generated fields like Universally Unique Identifiers to tie into SpiceDB to enable the Relational Based Access Control that enables this project to support a number of agencies. 

### Transformation Logic
The data is transformed in several ways during ingest. Transformations include reshaping query output into more processing friendly forms, and the inclusion of derived fields like UUIDs and password hashes. The system also handles potentially invalid data, like a username that is too long. 

---

## Deployment & Setup

The primary system is ran by a set of compose files, depending on the intended workflow. The compose `development.compose.yml` is used for development and demonstration of a system that is already populated with data. The compose `bootstrap-dev.compose.yml` is a special compose used for testing the empty initialization flow, which includes a startup wizard that walks a user through software set up. 

The ETL pipeline for ingesting user data is ran with a jupyter kernel. There is a requirement.txt file included with the notebook for building a virtual environment to be used as a juptyer kernel. The `development.compose.yml` compose group should be running. You can also run this pipeline with `bootstrap-dev.compose.yml`, but only after initial set up has been completed.

### System Requirements
* **Hardware:** This tool is designed with a microservice architecture and can be hosted on a single machine or distributed across multiple nodes.
* **Container Orchestration:**
    * **Podman:** version 5.7.1+ (with Podman-Compose 1.5.0+)
    * **Docker:** version 28.3.3+ (with Docker Compose 2.39.1+)

### Environment Configuration (Secrets)
Create a `.env` file in the root directory with the following variables:

* `APPLICATION_URL`: The base URL for the application.
* `ORIGIN_URL`: This key determies the allowed host for `CORS`.
* `SECRET_KEY`: A unique, high-entropy string used for cryptographic signing and CSRF protection.
* `VALKEY_HOST`: The URL or container name for the Valkey instance.
* `VALKEY_PASS`: Access password for the Valkey cache.
* `DB_HOST`: The URL or container name for the PostgreSQL database.
* `DB_USER`: Database username for API access.
* `DB_PASS`: Password for the database user.
* `DB_NAME`: Name of the PostgreSQL database.
* `AWS_ENDPOINT_URL_S3`: URL for the S3-compliant object storage provider.
* `AWS_ACCESS_KEY_ID`: Storage provider access key.
* `AWS_SECRET_ACCESS_KEY`: Storage provider secret key.
* `SESSION_COOKIE_SAMESITE`: Should be `Lax` for testing, and `Strict` for production.
* `SESSION_COOKIE_SECURE`: Should be `false` for development mode, and `true` in production.
* `SESSION_PERMANENT`: Ultimately up to your organizations policy.
* `SPICEDB_GRPC_LOGLEVEL`: Set to 'debug' for testing.
* `SPICEDB_DATASTORE_ENGINE`: This project uses postgres for spicedb's datastore.
* `SPICEDB_DATASTORE_CONN_URI`: The URI for spicedb to be able to talk to its datastore.
* `SPICEDB_GRPC_PRESHARED_KEY`: Do not share this with anyone. This key is used to authorize access to spicedb.
* `SPICE_URL`: Usually `localhost:50051` is sufficient. Spicedb should not be accessible external to the server, unless you are deploying across several different computers. 

---

## Local Development Setup

To facilitate testing and contributions, a containerized environment is provided that simulates the enterprise architecture on a single host. An internet connection is required to access the sample imagery dataset. 

> **Note for Windows/macOS Users:** A virtualization-capable system is required. Intel-based Mac users are encouraged to use Docker due to known compatibility issues with Podman machine stability on those platforms.

### Running the Environment
Ensure your `.env` file is populated before running these commands.

**Linux & Apple Silicon (Podman):**
```sh
podman compose -f bootstrap-dev.compose.yml up -d
```

**Intel-based Mac (Docker):**
```sh
docker compose -f bootstrap-dev.compose.yml up -d
```

**Windows (Podman):**
*Note: Ensure the `restore.sh` script in `local_db` uses **LF** line endings.*
```powershell
podman compose -f bootstrap-dev.compose.yml up -d
```

---

## Sample Output
The following is a collection of screenshots from pgadmin4 and the front end datamanagement system that shows query output and the results of transformation.

### Results of ETL pipeline 
<img width="1651" height="882" alt="Screenshot_20260514_175745" src="https://github.com/user-attachments/assets/7da2aa6c-8d37-45bf-b47a-8973b66456b4" />
_A lot of users_

### Example Query output

## Project Reflection

### Current Status
I am submitting a "good enough" version of my datamanagement vision that still falls short of complete. It is missing a number of featues that will greatly improve front end performance and development experience. 

### Incomplete or Simplified Elements
The data management interface is missing elements like update controls, and searching. I would additionaly like to explore data dependence via a graph visualization using D3, and retrofit my frotend stores to improve performance and decrease memory usage. `ProjectStore.ts` has become bloated in comparison to the more simple and much faster and much newer `cropVerifierStore.ts`. I would like to create a universal framework to support undo and redo behavior across the different layers of my system.  

### Challenges Encountered
The primary challenge came from reconciling the state of the database with SpiceDB for authorization. This applies to the ETL pipeline present in this submission, and to the other pipelines such as prediction creation. An API that can keep up with a GH200 GPU is not an easy feat. My future work at Argonne National Laboratory will see me attempting to better "feed the beast" to the point that my API becomes the bottleneck.

