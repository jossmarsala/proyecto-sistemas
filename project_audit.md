# Project Audit: SISTEMA DE GESTIÓN DE VENTAS

## Executive Summary
**Cargar_ventas** is a terminal-based Python application designed to manage business sales. It features a straightforward interactive CLI that allows users to create new sales, add products to them, and save the operations into a local database. The project also provides robust reporting capabilities, allowing data extraction and styling into Excel spreadsheets using Pandas and Openpyxl.

## Current Tech Stack & Architecture
- **Language**: Python (Sync, CLI-based execution)
- **Database**: SQLite3 (`database/ventas.db`)
- **Reporting / Data Analysis**: `pandas`, `openpyxl`, `numpy`
- **Architecture**: The project is structured using a simplified Model-View-Controller (MVC) pattern, although the "View" is just the terminal.
  - **Models (Classes)**: `/classes/` directory contains Domain-Driven classes like `Venta`, `Detalle`, `Cliente`, `Producto`, `Direccion`, and `Encargado_obra`.
  - **Controllers**: `/controller/` handles the business logic. It translates Python objects into SQLite relational tables (e.g. `controlador_db.py`, `controlador_venta.py`).
  - **Exporter**: `/exporter/exportar_excel.py` generates `.xlsx` files with professional formatting, including filters and grand totals.
  - **Entry Point**: `main.py` provides the main loop and terminal user interface.

## Core Features
1. **Interactive CLI Menu**: Displays active sales and gives options to start, append to, or discard a sale.
2. **Sales Tracking (Ventas & Detalles)**: Handles relational logic, generating a unified `Venta` and its composite `Detalle` items (Products, prices, amounts).
3. **Persisted Storage**: Safely stores completed transactions into a local SQLite DB, mapping standard Python classes.
4. **Excel Exports**: Can generate a "Reporte_ventas.xlsx" pulling from the DB via a SQL `JOIN` query and formatting headers/currency automatically.

---

## Upscaling to a Full Management Dashboard

The user intent is to evolve this CLI tool into a **Full Management Dashboard with Stats and Predictions**. Here is how we can bridge the gap from the current state:

### 1. The Ideal Stack
To provide a beautiful, modern dashboard as requested, you should migrate to a modern web stack:
- **Frontend**: **Next.js** (React) or **Vite** with Vanilla CSS or Tailwind. This will allow us to create a dynamic, glassmorphic UI with micro-animations that wows the user.
- **Backend / API**: We can either use Next.js API routes or convert the current Python logic into a **FastAPI** backend. FastAPI is recommended because it allows us to reuse your current Python classes and database (`sqlite3` -> `SQLAlchemy`), plus it's great for AI/Predictive Data Science integration later down the line.
- **Database**: Keep **SQLite** for now (easy to port), but abstract the connection using an ORM like SQLAlchemy or Prisma (if using pure TS) to easily migrate to PostgreSQL in the future.

### 2. Feature Roadmap
Based on the current features, here is the suggested upgrade path:

#### Phase 1: API & Database Migration
- Expose your current `sqlite3` methods (Create Venta, List Ventas, Get Detalles) as RESTful API endpoints.
- Evolve the DB Schema to capture timestamps and user contexts properly for analytical grouping.

#### Phase 2: Core Dashboard UI
- Build a beautiful web interface replacing `main.py`.
- **Sales View**: A table/grid replicating the Excel export visually.
- **Point of Sale (POS) View**: A dedicated dynamic page to add products to a cart and "Finalizar y Guardar", replacing the CLI prompts.

#### Phase 3: Analytics & Predictions
- **Stats**: Introduce interactive charts (using libraries like Recharts or Chart.js) showing Sales Over Time, Top Selling Products, and Revenue.
- **Predictions (AI/ML)**: Since the backend is in Python (or utilizing Python microservices), we can easily pipe the historical `ventas.db` data into a linear regression model or a time-series forecasting algorithm (e.g. Prophet or basic Scikit-Learn) to predict next month's sales or inventory depletion rates.