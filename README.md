# Inventory Application

An efficient, browser-based inventory management tool built with Flask and SQLite, designed to help organize hardware components, tools, or any items stored in drawers across multiple cabinets. This is a DIY-focused tool designed for makers, engineers, and garage tinkerers.

## Features

- **Search drawers** by name, quantity, location (row/column), or category
- **Multi-cabinet support** for managing separate physical storage systems
- Add, update, or delete inventory items easily
- Export to **CSV or Google Sheets** for backups and reporting
- Mobile-friendly design with **swipe actions**
- Label drawers with **QR codes** and custom codes
- Ready for deployment on Raspberry Pi, Docker, or cloud services

## Program Structure

```
inventorywebapp/
|---> app/
|      |---> static/
|      |      |---> style.css
|      |---> templates/
|      |      |---> index.html
|      |---> __init__.py
|      |---> api_routes.py
|      |---> app.py
|      |---> export_manager.py
|      |---> import_manager.py
|      |---> inventory_manager.py
|      |---> Logger.py
|      |---> system_stats.py
|      |---> utilities.py
|---> resources/
|      |---> backup.csv
|      |---> database.db
|      |---> inventory.log
|---> clean_run.py
|---> README.md
|---> requirements.txt
|---> reset_database.py
```

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Database**: SQLite
- **Platform Ready**: Raspberry Pi, Docker, Heroku

## Screenshots
add screen shots later

## Setup Instructions

### Prerequisites

- Python 3.8+
- `pip` (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/Johniecache/inventory-application.git
cd inventory-application

# Create a virtual environment
python -m venv venv
source venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
flask run
