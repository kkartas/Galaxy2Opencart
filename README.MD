
# Galaxy2Opencart

## Overview

**Galaxy2Opencart** is a Python-based application designed to integrate the Epsilon Singularlogic Galaxy ERP with OpenCart. This tool enables seamless data transfer and synchronization between Epsilon Singularlogic Galaxy ERP and OpenCart, facilitating efficient e-commerce operations.

## Features
- **Data Synchronization**: Automatically sync data between Epsilon Singularlogic Galaxy ERP and OpenCart.
- **API Integration**: Utilizes Epsilon Singularlogic Galaxy ERP and OpenCart APIs for seamless integration.
- **Error Handling**: Robust error handling to ensure data integrity.

## Prerequisites
- Python 3.8+
- Epsilon Singularlogic Galaxy ERP API credentials
- OpenCart API credentials

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/kkartas/Galaxy2Opencart.git
   cd Galaxy2Opencart
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv env
   source env/bin/activate   # On Windows: env\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **API Credentials**
   - Create a `config.json` file in the root directory with your API credentials:
     ```json
     {
       "galaxy_api_key": "your_galaxy_api_key",
       "opencart_consumer_key": "your_opencart_consumer_key",
       "opencart_consumer_secret": "your_opencart_consumer_secret",
       "opencart_url": "your_opencart_store_url"
     }
     ```

2. **Database Setup**
   - The project uses SQLite by default. Ensure `db.sqlite3` exists in the project root. If not, create it by running:
     ```bash
     python manage.py migrate
     ```

## Usage

1. **Run the Application**
   ```bash
   python manage.py runserver
   ```

2. **Access the Application**
   - Open your browser and navigate to `http://127.0.0.1:8000`.

3. **Synchronization**
   - The application will start synchronizing data between Epsilon Singularlogic Galaxy ERP and OpenCart based on the predefined schedule or triggers.

## Directory Structure

- **.github/workflows**: Contains GitHub Actions workflows for CI/CD.
- **Galaxy2Opencart**: Main application directory.
- **app/templates**: HTML templates for the web application.
- **db.sqlite3**: SQLite database file.
- **manage.py**: Entry point for the Django application.
- **requirements.txt**: Python dependencies.

## Acknowledgments

WooCommerce and Epsilon Singularlogic Galaxy ERP are not my property or trademarks. Special thanks to the contributors and the open-source community for their invaluable support.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
