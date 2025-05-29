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
![inventory_app_ss1](https://github.com/user-attachments/assets/781801f2-3968-4930-8527-aff73c715ae6)
![inventory_app_ss5](https://github.com/user-attachments/assets/a9a29fd1-53fb-4e4e-adc3-8750f935af12)
![inventory_app_ss3](https://github.com/user-attachments/assets/a083ff93-e715-4c37-a232-6aeffd692eea)
![inventory_app_ss4](https://github.com/user-attachments/assets/ebc37eb1-d121-4e5b-8e7e-dee0a4344778)



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
