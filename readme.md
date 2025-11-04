<div align="center">
  <img src="https://raw.githubusercontent.com/SachinChandra2022/niftron-frontend/main/public/logo.png" alt="NIFTRON Logo" width="120" />
  <h1 align="center">NIFTRON Backend & Data Pipeline</h1>
  <p align="center">
    The complete data engineering and backend infrastructure for the NIFTRON project, featuring a FastAPI server and an Apache Airflow data orchestration pipeline.
  </p>
</div>

<div align="center">
  <!-- Badges -->
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Apache%20Airflow-2.9+-blueviolet?style=for-the-badge&logo=apache-airflow" alt="Apache Airflow">
  <img src="https://img.shields.io/badge/Docker-24+-blue?style=for-the-badge&logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT">
</div>

<br/>

<p align="center">
  <a href="#-system-architecture">System Architecture</a> •
  <a href="#-key-features">Key Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-local-development">Local Development</a> •
  <a href="#-api-endpoints">API Endpoints</a> •
  <a href="#-license">License</a>
</p>

---

## 🏛️ System Architecture

This backend is designed with a clear separation of concerns between its two primary functions: **serving real-time requests** and **performing scheduled, heavy computations.**

1.  **Apache Airflow (The Data Processor):** Runs on a schedule in a local Docker environment. It executes a multi-step data pipeline (ingest, process, analyze) and writes the final recommendations and performance metrics to a central cloud database.
2.  **FastAPI (The API Server):** A lightweight, high-performance web server deployed on the cloud (Render). Its sole job is to read the pre-computed results from the database and serve them instantly to the frontend.

This decoupled architecture ensures the user-facing application remains fast and responsive, regardless of how long the data analysis takes.

```mermaid
graph TD;
    subgraph "Local Docker Environment"
        Airflow(💨 Apache Airflow);
    end

    subgraph "Cloud Services"
        DB[(☁️ NeonDB PostgreSQL)];
        API(🚀 FastAPI on Render);
        Frontend(🖥️ Vue.js on Vercel);
    end
    
    Airflow -- "1. Runs daily ETL pipeline" --> Airflow;
    Airflow -- "2. Writes fresh analysis results" --> DB;
    Frontend -- "3. User requests data" --> API;
    API -- "4. Reads pre-computed results" --> DB;
    API -- "5. Serves data instantly" --> Frontend;
```
## ✨ Key Features

*   **Automated ETL Pipeline:** A robust, multi-task DAG in **Apache Airflow** handles daily data ingestion, feature engineering, and model execution.
*   **High-Performance API:** A production-ready API built with **FastAPI** serves data with automatic documentation via Swagger UI.
*   **Dual-Model Analysis:** The core logic runs two distinct analysis strategies: a machine-learning ensemble (LEM) and a rule-based heuristic (SHE).
*   **Fully Containerized:** The entire local development stack, including Airflow, its scheduler, and a Redis message broker, is managed via **Docker Compose** for one-command setup.
*   **Cloud Native:** Designed for modern cloud deployment, with the API running as a Docker image on **Render** and connecting to a serverless **NeonDB** instance.
*   **CI/CD Ready:** The repository is configured for continuous integration and deployment, automatically updating the live service on every push to the `main` branch.

## 🛠️ Tech Stack

| Category          | Technology / Library                                       |
|-------------------|------------------------------------------------------------|
| **Web Framework** | `FastAPI`, `Uvicorn`                                       |
| **Data Processing** | `Pandas`, `scikit-learn`                                   |
| **Orchestration** | `Apache Airflow`                                           |
| **Database**      | `PostgreSQL` (via `psycopg2-binary`), `NeonDB` (Cloud)     |
| **DevOps**        | `Docker`, `Docker Compose`                                 |
| **Deployment**    | `Render`                                                   |

## ⚙️ Local Development Setup

To run the complete backend system (API + Airflow) on your local machine, follow these steps.

### Prerequisites
*   [Git](https://git-scm.com/)
*   [Docker](https://www.docker.com/products/docker-desktop/) & Docker Compose

### Setup Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/SachinChandra2022/niftron-backend.git
    cd niftron-backend
    ```

2.  **Create an environment file:**
    Create a file named `.env` in the project root and add your NeonDB connection string.
    ```env
    # .env
    DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
    ```

3.  **Build and run the containers:**
    This command builds the necessary Docker images and starts all services defined in `docker-compose.yml`.
    ```bash
    docker-compose up --build
    ```
    *   To run in the background, use `docker-compose up --build -d`.
    *   To stop all services, use `docker-compose down`.

4.  **Access the services:**
    *   **FastAPI Backend API:** [http://localhost:8001/docs](http://localhost:8001/docs)
    *   **Apache Airflow UI:** [http://localhost:8080](http://localhost:8080) (Login: `admin` / `admin`)

## 🌐 API Endpoints

The main endpoints served by the FastAPI application are:

| Method | Endpoint                      | Description                                                  |
|--------|-------------------------------|--------------------------------------------------------------|
| `GET`  | `/api/v1/recommendations`     | Fetches the latest Top 5 recommendations for both LEM & SHE models. |
| `GET`  | `/api/v1/performance-charts`  | Generates data for the Equity Curve and Drawdown charts.      |
| `POST` | `/api/v1/chat`                | Handles messages for the AI chatbot.                           |
| `POST` | `/api/v1/run-analysis`        | Manually triggers the Airflow analysis pipeline (for debugging). |

## 📄 License

This project is licensed under the MIT License.

<details>
<summary><strong>Click to view the full license text</strong></summary>
MIT License
Copyright (c) 2025 Sachin Chandra
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
</details>

---

<div align="center">
  <em>Developed with passion and precision.</em>
</div>

