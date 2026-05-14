# Storage Selection Memo: Airial Software Tools

---

## 1. Storage Decisions



### Relational Database Management System (RDBMS)

For this project, a **relational database** was selected as the primary data store. The inherent interconnectivity of the data—characterized by complex relationships between users, organizations, and project assets—requires the strong consistency and ACID compliance that an RDBMS provides. This architecture is particularly well-suited for a **multi-tenant system**, ensuring strict data isolation and integrity across different organizations.



### Object Storage (CEPH RADOS GW S3)

For image assets and binary data, **S3 Object Storage** was chosen. This offloads heavy binary large objects (BLOBs) from the database, ensuring:

* **Scalability:** Independent scaling of storage and compute.

* **Availability:** High durability and rapid retrieval across distributed environments.

* **Performance:** Reduced database backup sizes and improved query performance by keeping the database focused on metadata.



---



## 2. Schema & Data Modeling



### Data Structure

The system architecture is organized into three distinct logical schemas to maintain a clean separation of concerns:

* **`core`**: Contains the primary domain data (e.g., images, model predictions, and human made annotations).

* **`projectmanagement`**: Manages the grouping of resources, project lifecycle, and organizational boundaries.

* **`usermanagement`**: Handles user identities, authentication metadata, and role-based and access control (RBAC).



### Key Relationships

The **`core` schema** serves as the heartbeat of the application. The design relies heavily on **Foreign Key (FK) constraints** to maintain referential integrity. These relationships allow for complex traversals, such as tracing an image back to its parent project, its contributing user, or its associated organization.



### Query Support

The types of potential queries informed the structure of the schemas. An example of designing for a query is the foreign key reference to images in the annotations table despite the existence of a in inderect relationship through predictions.

---



## 3. Pipeline Behavior & Orchestration



### Pipeline Overview

The system utilizes three distinct orchestration workflows:

1.  **Demo Pipeline:** A pre-populated environment orchestrated via `podman compose` that supports feature development and impromptu demonstrations.

2.  **Initial Setup Workflow:** A dedicated `podman compose` workflow that handles the "Setup Wizard," initializing schemas and seeding empty state data.

3.  **Bulk Ingestion Pipeline:** A Jupyter notebook capable of importing 5,000+ user objects. 

    * *Note:* This workflow is external to the API system because of the large processing overhead. This notebook makes use of parallelism to quickly ingest the system. In order to efficiently support such a feature at production scale the API would require the use of redis dispatch to effectively push large workloads to the background. This a planned feature but exists outside of the scope of the project.

### Dependencies & Failure States

A critical dependency exists between **PostgreSQL** and **SpiceDB**.

* **Success Path:** Objects are inserted into Postgres, and corresponding relationship tuples are created in SpiceDB to grant access.

* **Failure Scenarios:**

    * If SpiceDB fails: The object exists in Postgres but remains inaccessible (Access Denied).

    * If Postgres fails: SpiceDB may hold a permission for a non-existent object which would result in access granted, but a (404 Error). ACL checks are performed before computation for performance reasons.

    * *Mitigation:* Spicedb operations are included inside of the transactional context of each database operation, which means that if their is a failure in either piece the entire operation is discarded.



---



## 4. Analytical Perspective



### Support for Analysis & Reporting

The schema follows a **domain-driven design**, where tables are focused on specific objects. This normalization allows for efficient cross-table joins, enabling users to generate reports across different organizational silos without data redundancy.



### Design Complexity & Trade-offs

While the submission focuses on simple queries, the design supports highly complex analytical requests (e.g., *“Rank the top 50 images based on prediction scores and label confidence”*). Database design and query design are in part informed by each other. A design that supports queries of group A will nessacarily hurt a deisgn that focuses on group B. 



### Future Restructuring

Current analytical performance is robust. This is evidenced by the successful integration of data for **pronghorn abundance estimates** (supporting the work of Dr. Martin). Future iterations will focus on expanding the schema to further automate these specialist-led computations for non-expert users.



---



## 5. Performance & Scale Considerations



### Bottlenecks & Growth

Currently, the primary single point of failure for scaling is the central database instance. However, **PostgreSQL** offers several paths for horizontal expansion:


* **Distributed Database system:** Future-proofing via distributed PostgreSQL clusters behind a load balancer and deploying to the cloud.
* **Regional Availability:** Eventually the data center itself will become the bottleneck, especially for users that are located further away from the datacenter. The system architecture should make it fairly trivial to create availability zones across different cloud instances that support to the greater software.

### 10x to 100x Scalability (and 1000x)

The design is proven to scale. The production environment already handles **100x the volume** of the demo dataset while maintaining high performance. This is attributed to:

* **Efficient Indexing:** Strategic use of B-Tree and GIN indexes.

* **Optimized Hardware:** Utilizing high-performance infrastructure provided by **ARCC**.

* **Clean Design:** The schema utilizes the features of Postgresql and avoids common anti patterns like "everything" tables.



### Future Optimizations

* **Refining Indexes:** Index choice should be informed by the nature of common queries, in the form of what commonly is looked up against. Right now the system uses a wide spread of indexes, and future work will analyze if certain indexes need added or dropped.

* **Storage Throughput:** As ARCC continues to improve their systems our software performance will improve with it.

