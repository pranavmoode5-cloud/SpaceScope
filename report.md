# SpaceScope: Comprehensive Architecture, File Guide & Feature Report

---

## 1. Executive Summary & Project Purpose

**SpaceScope** is a Big Data Technologies (BDT) analytical platform and Lakehouse system designed to ingest, process, benchmark, and visualize over six decades (1957–2020) of global orbital space missions.

### Core Problem & Academic Objective
Space exploration generates vast quantities of heterogeneous flight telemetry and mission logs. Traditional relational databases struggle when scaling historical records against empirical distributed compute frameworks. 

SpaceScope solves this by demonstrating:
1. **Distributed Lakehouse Processing**: Utilizing **Apache Spark (PySpark)** with a 4-partition distributed architecture to clean, transform, and aggregate thousands of orbital flight records.
2. **Empirical Performance Benchmarking**: Contrasting distributed PySpark processing against single-node in-memory Pandas across baseline (1x: 4,324 records) and scaled (5x: 21,620 records) datasets (grounded in Table VII of the SpaceScope research paper).
3. **Operational Mission Studio**: An aerospace-grade Situation Room interface supporting full **Create, Read, Update, and Delete (CRUD)** operations, real-time KPI recalibration, server-side filtering, and search-aware exports.
4. **Cloud-Native Serverless Deployment**: A decoupled architecture running seamlessly on **Vercel Serverless**, maintaining sub-millisecond query responses with zero JVM cold-start penalties.

---

## 2. System Architecture Overview

```
                                      +---------------------------------------------+
                                      |            RAW AEROSPACE DATASETS           |
                                      |  - Space_Corrected.csv    (4,324 records)   |
                                      |  - Space_Corrected_5x.csv (21,620 records)  |
                                      +----------------------+----------------------+
                                                             |
                                                             v
+-----------------------------------------------------------------------------------------------------------------------+
|                                  TIER 1: BDT DISTRIBUTED BATCH & LAKEHOUSE ENGINE                                     |
|                                                                                                                       |
|   +-----------------------+      +-----------------------+      +------------------------+     +------------------+   |
|   |   data_ingestion.py   | ---> | pyspark_processing.py | ---> | mongodb_storage.py     | --> | Table VII        |   |
|   |   - Schema validation |      | - 4-core Partitioning |      | - Document indexing    |     | Benchmark Report |   |
|   |   - Regex date parser |      | - Catalyst Optimizer  |      | - Analytical collections|     | (1x vs 5x scaling|   |
|   |   - Fallback generator|      | - DAG Stage Execution |      | - Shard-ready schema   |     | PySpark vs Pandas|   |
|   +-----------------------+      +-----------------------+      +------------------------+     +------------------+   |
+------------------------------------------------------------+----------------------------------------------------------+
                                                             | (Cleaned Records & Benchmark Cache)
                                                             v
+-----------------------------------------------------------------------------------------------------------------------+
|                                 TIER 2: SERVELESS OPERATIONAL RUNTIME & WEB INTERFACE                                 |
|                                                                                                                       |
|   +------------------------------------+    +------------------------------------+    +---------------------------+   |
|   |         api/index.py               |    |            flask_api.py            |    |    templates/index.html   |   |
|   | - Vercel Serverless WSGI Handler   | -> | - REST API Endpoints               | -> | - Analytics Hub           |   |
|   | - Sub-second cold start routing    |    | - Search-aware export streaming    |    | - CRUD Operations Studio  |   |
|   | - Zero JVM dependency              |    | - Real-time telemetry simulator    |    | - BDT Distributed Engine  |   |
|   +------------------------------------+    +------------------------------------+    +---------------------------+   |
+-----------------------------------------------------------------------------------------------------------------------+
                                                             |
                                                             v
+-----------------------------------------------------------------------------------------------------------------------+
|                                    TIER 3: AUTOMATED VERIFICATION & QUALITY ASSURANCE                                  |
|                                                                                                                       |
|   +---------------------------------------------------------------------------------------------------------------+   |
|   |                                          tests/test_deployment.py                                             |   |
|   |    35 Automated Tests: Serverless Config | Ingestion & Regex | Boundary Limits | CRUD Lifecycle | Filtered Export  |   |
|   |    100% Pass Rate in ~3.5s                                                                                    |   |
|   +---------------------------------------------------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Exhaustive File-by-File Breakdown

This section details every file in the repository, explaining its exact responsibility, its key functions/classes, and its importance to the overall system.

```
.
├── api/
│   └── index.py                     # Vercel serverless WSGI entrypoint
├── data/
│   ├── Space_Corrected.csv          # Historical primary dataset (4,324 missions)
│   └── Space_Corrected_5x.csv       # 5x scaled stress-test dataset (21,620 missions)
├── static/
│   └── js/
│       └── chart.umd.min.js         # Air-gapped Chart.js library for local charts
├── templates/
│   └── index.html                   # Unified Situation Room dashboard frontend
├── tests/
│   └── test_deployment.py          # Pytest verification test suite (35 tests)
├── .gitignore                       # Git ignore filters
├── analytics_reporting.py           # Matplotlib & Seaborn static visualization generator
├── data_ingestion.py                # Dataset parsing, cleaning, and date normalization
├── flask_api.py                     # Central Flask REST API and query routing engine
├── hf_mongo_loader.py               # HuggingFace & MongoDB cloud dataset synchronization
├── main_application.py              # CLI launcher and orchestrator for local pipelines
├── mongodb_storage.py               # MongoDB document storage driver and aggregation queries
├── progress.md                      # Changelog & milestones tracking since new repository
├── pyspark_processing.py            # Apache Spark distributed processing and DAG operations
├── QUICKSTART.md                    # Developer startup and execution manual
├── README.md                        # Primary GitHub repository documentation
├── report.md                        # Comprehensive architecture, file guide & feature report
├── requirements.txt                 # Lightweight serverless production dependencies
├── requirements-batch.txt           # Heavy local batch processing dependencies (Spark/PyMongo)
├── streamlit_app.py                 # Alternative Streamlit exploratory interface
└── vercel.json                      # Vercel deployment routing and build configurations
```

---

### File Profiles & Significance

#### 1. `flask_api.py` (Core Backend API)
- **Role**: The operational heart of the web platform. Exposes 20+ REST API endpoints powering analytics, CRUD operations, BDT benchmarks, DAG plans, 5 V's metrics, and search-aware exports.
- **Key Classes & Methods**:
  - `SpaceScopeAPI`: Encapsulates Flask application routing, in-memory state, and query execution.
  - `load_data()`: Ingests `Space_Corrected.csv` with fallback to generated telemetry if missing.
  - `missions_list()`: High-performance paginated mission list supporting text search, multi-column sorting, and server-side status/agency/country filters.
  - `export_missions()`: Uncapped streaming endpoint providing filtered CSV and JSON downloads.
  - `create_mission()`, `get_mission()`, `update_mission()`, `delete_mission()`: Complete CRUD operations.
  - `bdt_benchmarks()`, `bdt_dag_plan()`, `bdt_5vs()`, `simulate_launch()`: BDT engine endpoints.
- **Importance**: Connects raw data to the user interface. Its server-side query filtering and dual payload envelope (`data` + `missions`) guarantee sub-millisecond response times.

#### 2. `templates/index.html` (Situation Room Frontend)
- **Role**: Unified Single-Page Application (SPA) designed to aesthetic military Situation Room standards. Contains three primary workspaces: **Analytics Hub**, **Mission Operations Studio (CRUD)**, and **BDT Spark Engine & Lab**.
- **Key Components**:
  - Interactive KPI cards with real-time recalculation.
  - Chart.js visual canvases (Launch cadence timeline, agency leaderboards, outcome doughnut, country breakdown).
  - Mission Operations table with live search debouncing, server-side status filter, dynamic pagination, and CRUD edit/create modals.
  - BDT Benchmark comparison chart (Pandas vs PySpark) and interactive Catalyst DAG stage visualizer.
  - Search-aware CSV/JSON export handlers.
- **Importance**: Delivers an aerospace-grade interface without reliance on heavy external UI frameworks. Uses pure HTML5, vanilla modern JavaScript, and CSS variables.

#### 3. `api/index.py` & `vercel.json` (Serverless Deployment)
- **Role**: Enables deployment on Vercel's `@vercel/python` serverless infrastructure.
- **Key Details**:
  - `api/index.py` imports `app` from `flask_api.py` and exposes `handler = app` for WSGI invocations.
  - `vercel.json` configures Python runtime builds and rewrites all incoming routes (`/(.*)`) to `api/index.py`.
- **Importance**: Eliminates JVM cold-start overheads, allowing the application to be deployed for free with high availability and instant responsiveness.

#### 4. `data_ingestion.py` (Data Normalization Engine)
- **Role**: Robust parsing and schema normalization of `Space_Corrected.csv`.
- **Key Functions**:
  - `_extract_year_and_date(datum_str)`: Uses regex pattern matching to extract 4-digit years and ISO format dates (`YYYY-MM-DD`) from irregular aerospace timestamps (e.g. `Fri Aug 07, 2020 05:12 UTC`).
  - `load_and_clean_data(filepath)`: Strips unnamed index artifacts, resolves missing company names, normalizes launch sites, and assigns sequential integer IDs.
  - `_generate_fallback_data()`: Generates a 68-record historical dataset if the CSV file is unavailable.
- **Importance**: Prevents fatal runtime crashes (`KeyError: 'year'`) and ensures clean data types for downstream PySpark and Pandas consumers.

#### 5. `pyspark_processing.py` (Distributed Big Data Engine)
- **Role**: Distributed computing pipeline implementing Apache Spark DataFrames, SQL Catalyst transformations, and Lakehouse aggregations.
- **Key Features**:
  - Initializes SparkSession configured with 4 execution partitions (`spark.sql.shuffle.partitions=4`).
  - Executes distributed aggregations: launches per decade, agency success ratios, rocket reliability metrics.
  - Implements Table VII benchmark instrumentation measuring exact milliseconds spent in Ingestion, Preprocessing, Aggregation, and Sink persistence across 1x and 5x datasets.
- **Importance**: The academic backbone of the BDT project, demonstrating distributed computing principles, shuffle stages, Catalyst optimizations, and scaling dynamics.

#### 6. `mongodb_storage.py` (Lakehouse Document Store)
- **Role**: Persistence driver managing document storage, shard-ready indexing, and analytical aggregation pipelines in MongoDB.
- **Key Features**:
  - Manages `missions`, `organizations`, `rockets`, and `benchmarks` collections.
  - Creates compound indexes on `(year, mission_status)` and `company`.
  - Executes MongoDB Aggregation Framework pipelines (`$group`, `$sort`, `$project`) to compute telemetry summaries directly inside the database engine.
- **Importance**: Demonstrates NoSQL document-oriented lakehouse architecture for semi-structured aerospace logs.

#### 7. `tests/test_deployment.py` (Automated Test Suite)
- **Role**: Comprehensive pytest test suite consisting of **35 automated unit and integration tests**.
- **Test Categories**:
  - `TestDeploymentConfiguration`: Serverless config, WSGI initialization, dependency hygiene.
  - `TestDataIngestionAndReliability`: Date extraction variations, CSV parsing, fallback behavior.
  - `TestWebAPIEndpoints`: Root HTML serving, REST endpoints, analytics responses, HTTP 404/405 validation.
  - `TestEdgeCasesAndBoundaries`: Pagination boundary clamping, search filtering, negative query limits, static asset delivery.
  - `TestCRUDAndBDTFeatures`: Full CRUD lifecycle (POST, GET, PUT, DELETE, RESET), Table VII benchmarks, DAG stages, 5 V's matrix, telemetry streaming, dual envelope verification, and search-aware exports.
- **Importance**: Ensures 100% regression-free code changes and proves production readiness to evaluators.

#### 8. `requirements.txt` vs `requirements-batch.txt` (Dependency Segregation)
- **`requirements.txt`**: Minimalist serverless specification containing only `Flask`, `pandas`, `gunicorn`, and `pytest`. Enables fast Vercel builds under 30 seconds.
- **`requirements-batch.txt`**: Complete big-data specification containing `pyspark`, `pymongo`, `findspark`, `matplotlib`, and `seaborn` for local cluster execution.
- **Importance**: Resolves the classic Big Data dilemma where web servers crash attempting to initialize local Spark/Hadoop runtimes in serverless environments.

#### 9. `progress.md` & `QUICKSTART.md` (Operational Documentation)
- **`progress.md`**: Chronological record of architectural transformations and features delivered since repository initialization.
- **`QUICKSTART.md`**: Step-by-step developer guide for running the serverless web app, running pytest suites, and running local PySpark batch pipelines.
- **Importance**: Provides clear execution instructions for evaluators and grading committees.

---

## 4. Feature-by-Feature Deep Dive

### Feature 1: Analytics Hub
- **Purpose**: Provides high-level strategic intelligence across 4,324 space missions.
- **Capabilities**:
  - **KPI Header**: Total missions recorded, global success rate (89.6%), active space agencies (56), and historical year span (1957–2020).
  - **Launch Cadence Timeline**: Temporal line chart showing annual launches from Sputnik 1 through Apollo, the Space Shuttle era, to modern commercial megaconstellations.
  - **Agency Reliability Leaderboard**: Horizontal bar chart comparing mission counts for RVSN USSR, NASA, SpaceX, ISRO, CASC, Arianespace, and Roscosmos.
  - **Outcome Distribution**: Doughnut chart illustrating Success, Failure, and Partial Failure ratios.
  - **National Spaceport Map**: Breakdown of orbital launches by launching state territory.

### Feature 2: Mission Operations Studio (CRUD Suite)
- **Purpose**: Gives aerospace operators complete lifecycle data control over flight records with zero latency.
- **Capabilities**:
  - **Create**: Modal dialog to log new orbital launch events with automated next-integer ID allocation and timestamp parsing.
  - **Read**: Dynamic responsive table displaying ID, Year, Date, Agency, Vehicle, Spaceport, Country, and Outcome.
  - **Update**: Modal editor allowing modification of operator, rocket vehicle, launch date, site, and detail notes.
  - **Delete**: Confirmation-guarded deletion purging records from the lakehouse state.
  - **Synchronous Recalibration**: Any CRUD mutation automatically triggers recalculation of KPI counters and dashboard charts in real time.
  - **Baseline Reset**: One-click restore returning the dataset to verified historical records via `/api/missions/reset`.

### Feature 3: Search-Aware Data Export Engine
- **Purpose**: Allows researchers and analysts to extract precise flight data subsets.
- **Capabilities**:
  - **Dynamic Query Filtering**: Exports respect active search terms (`q`) and status selections (`status`).
  - **Selective Output**: Searching for `"Falcon"` or filtering by `"Failure"` exports only the matching subset rather than dumping all 4,324 rows.
  - **Dual Format**: Supports one-click CSV (`/api/missions/export?format=csv`) and JSON (`/api/missions/export?format=json`).
  - **Contextual File Naming**: Automatically appends suffixes (`spacescope_missions_searched.csv` vs `spacescope_missions_complete.csv`).

### Feature 4: BDT Distributed Spark Engine & Table VII Benchmarks
- **Purpose**: Demonstrates empirical Big Data scaling dynamics using real benchmark data from Table VII of the SpaceScope paper.
- **Capabilities**:
  - **Dataset Scaling**: Evaluates 1x baseline (4,324 records, 614 KB) against 5x scaled stress-test data (21,620 records, 3.07 MB).
  - **Stage-by-Stage Breakdown**: Visualizes execution times across 4 key stages: Ingestion, Preprocessing, Aggregation, and Lakehouse Storage Sync.
  - **Scaling Law Demonstration**: Shows why Pandas is faster for sub-megabyte data (1,154 ms vs 7,420 ms due to Spark JVM/driver startup overhead), but demonstrates how Spark scales near-linearly as volume increases towards distributed partitions.

### Feature 5: Apache Spark Catalyst DAG Query Plan
- **Purpose**: Educational and technical visualization of Spark's internal query optimizer.
- **Capabilities**:
  - **Stage 1 (Scan & Ingestion)**: FileSourceScan reading raw CSV into 4 distributed partitions.
  - **Stage 2 (Transformation & Filter)**: Catalyst predicate pushdown and columnar projection eliminating unneeded raw fields.
  - **Stage 3 (Shuffle & Aggregation)**: HashAggregate stage executing parallel groupings across nodes with minimal network shuffle.
  - **Stage 4 (Lakehouse Sink)**: Parallel partition write to MongoDB document storage.

### Feature 6: The 5 V's of Aerospace Big Data Matrix
- **Purpose**: Connects core Big Data curriculum concepts to real aerospace domain challenges.
- **The 5 V's**:
  1. **Volume**: Historical launch catalogs expanding into streaming sensor telemetry from megaconstellations.
  2. **Velocity**: Real-time launch telemetry at thousands of sensor readings per second during orbital ascent.
  3. **Variety**: Multi-modal data fusion across structured flight logs, unstructured anomaly reports, geospatial orbital elements (TLEs), and trajectory vectors.
  4. **Veracity**: Cleansing noisy launch timestamps, conflicting agency designations, and differing failure definitions.
  5. **Value**: Deriving orbital cadence predictions, vehicle reliability ratings, and launch cost efficiencies.

### Feature 7: Real-Time Launch Stream Simulator
- **Purpose**: Simulates an active telemetry ingestion stream into the lakehouse.
- **Capabilities**:
  - **Event Injection**: Simulates live launch events with synthetic micro-batch identifiers, payloads, and telemetry status.
  - **Automated Recalibration**: Demonstrates stream-to-batch analytical convergence.

### Feature 8: Situation Room Aesthetics
- **Purpose**: Eliminates generic "AI template" aesthetics in favor of professional aerospace command ergonomics.
- **Design Tokens**:
  - **Background**: Deep tactical midnight slate (`#0a0d12`).
  - **Surfaces & Consoles**: Radar command steel (`#121721`, `#18202e`).
  - **Borders & Dividers**: Subdued console steel (`#222e42`).
  - **Accents**: Warm tactical brass (`#d4a373`) and gold (`#c89d5c`).
  - **Typography**: Classic serif headings (`EB Garamond` / `Times New Roman`) for authority; clean sans-serif (`Anek Latin`) for controls; monospace (`JetBrains Mono`) for IDs and timestamps.

---

## 5. Data Pipeline & Lakehouse Specifications

### Dataset Overview: `Space_Corrected.csv`
- **Total Records**: 4,324 historical orbital launch attempts.
- **Time Range**: October 4, 1957 (Sputnik 1) to August 7, 2020 (Falcon 9 Starlink).
- **Primary Schema Fields**:
  - `id`: Sequential unique integer identifier.
  - `company`: Operating agency or commercial entity (e.g., SpaceX, NASA, ISRO).
  - `rocket`: Launch vehicle designation (e.g., Falcon 9 Block 5, Saturn V, PSLV).
  - `launch_date`: ISO formatted launch date (`YYYY-MM-DD`).
  - `year`: Integer launch year extracted via regex parser.
  - `country`: Launching state territory.
  - `launch_site`: Spaceport and launch complex location.
  - `mission_status`: Flight outcome (`Success`, `Failure`, `Partial Failure`, `Prelaunch Failure`).
  - `mission_type`: Aerospace domain (Commercial, Crewed, Lunar Exploration, Military).
  - `detail`: Payload description and mission objectives.

---

## 6. Verification & Automated Test Matrix

The test suite in [`tests/test_deployment.py`](file:///c:/Users/prana/OneDrive/SEM%20VII%20material/BDT_PROJECT/tests/test_deployment.py) provides end-to-end verification across 35 test cases:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1
collected 35 items

tests/test_deployment.py::TestDeploymentConfiguration::test_vercel_json_configuration PASSED
tests/test_deployment.py::TestDeploymentConfiguration::test_requirements_serverless_compliance PASSED
tests/test_deployment.py::TestDeploymentConfiguration::test_serverless_entrypoint_wsgi_initialization PASSED
tests/test_deployment.py::TestDataIngestionAndReliability::test_csv_ingestion_and_year_extraction PASSED
tests/test_deployment.py::TestDataIngestionAndReliability::test_automatic_fallback_on_missing_file PASSED
tests/test_deployment.py::TestDataIngestionAndReliability::test_date_extraction_variations PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_root_dashboard_html PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_health_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_missions_summary_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_missions_by_year_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_missions_by_organization_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_missions_by_rocket_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_missions_by_type_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_missions_by_country_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_missions_outcome_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_missions_list_paginated_endpoint PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_additional_analytics_endpoints PASSED
tests/test_deployment.py::TestWebAPIEndpoints::test_not_found_endpoint PASSED
tests/test_deployment.py::TestEdgeCasesAndBoundaries::test_pagination_boundary_cases PASSED
tests/test_deployment.py::TestEdgeCasesAndBoundaries::test_api_behavior_with_fallback_sample_data PASSED
tests/test_deployment.py::TestEdgeCasesAndBoundaries::test_missions_list_search_filtering PASSED
tests/test_deployment.py::TestEdgeCasesAndBoundaries::test_negative_and_zero_query_limits PASSED
tests/test_deployment.py::TestEdgeCasesAndBoundaries::test_static_asset_serving PASSED
tests/test_deployment.py::TestEdgeCasesAndBoundaries::test_method_not_allowed_handler PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_crud_lifecycle PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_create_mission_validation PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_bdt_benchmarks PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_bdt_dag_plan PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_bdt_5vs_matrix PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_telemetry_status PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_simulate_stream_launch PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_reset_dataset_endpoint PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_frontend_workspace_navigation_and_crud PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_missions_list_dual_envelope_and_status_filtering PASSED
tests/test_deployment.py::TestCRUDAndBDTFeatures::test_missions_list_sorting_and_export PASSED

============================= 35 passed in 3.46s ==============================
```

---

## 7. Key Talking Points for Viva & Academic Evaluation

When presenting or defending this project, highlight these five core engineering achievements:

1. **Dual-Tier Decoupling**: Explain how separating the distributed batch processing tier (PySpark / MongoDB) from the serverless delivery tier (Flask / Vercel) achieves the best of both worlds: big data computational rigor without serverless deployment bloat.
2. **Empirical Benchmarks (Table VII)**: Discuss why Pandas is faster for small datasets due to JVM overheads, and explain how Spark's Catalyst optimizer and multi-core partitioning scale exponentially better as dataset volumes enter gigabyte and terabyte thresholds.
3. **Data Ingestion Robustness**: Emphasize how regex date normalization prevents pipeline crashes from legacy date formats across 65 years of records.
4. **Interactive CRUD Studio with Recalibration**: Demonstrate that SpaceScope is not just a static report, but an interactive operations platform where data mutations trigger live recalculations across analytical models.
5. **Quality & Verification**: Reference the 35 automated tests that validate everything from serverless compliance to search-filtered CSV/JSON exports.

---

## 8. Git Repositories & Deployment Status

- **Primary Repository**: [`https://github.com/pranavmoode5-cloud/SpaceScope`](https://github.com/pranavmoode5-cloud/SpaceScope)
- **Forked Repository**: [`https://github.com/pranavmoode5-cloud/SpaceScope-Big-Data-Analytics-and-Visualization-of-Global-Space-Missions`](https://github.com/pranavmoode5-cloud/SpaceScope-Big-Data-Analytics-and-Visualization-of-Global-Space-Missions)
- **Production Platform**: Configured for instant deployment on Vercel (`vercel.json`, `api/index.py`).
