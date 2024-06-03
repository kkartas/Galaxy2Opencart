import requests
import logging
from .models import UserAnswer

logger = logging.getLogger(__name__)

def authenticate_with_erp(erp_username, erp_password, erp_server_ip, erp_server_port):
    erp_auth_path = "/auth"
    erp_auth_url = f"http://{erp_server_ip}:{erp_server_port}{erp_auth_path}"
    erp_auth_data = {
        "username": erp_username,
        "password": erp_password
    }
    response = requests.get(erp_auth_url, params=erp_auth_data)
    session_cookie = response.cookies.get("ss-id")
    return session_cookie

def fetch_item_balances_from_erp(session_cookie, erp_server_ip, erp_server_port):
    erp_balances_path = "/services/sync/itembalances"
    erp_balances_url = f"http://{erp_server_ip}:{erp_server_port}{erp_balances_path}"
    headers = {
        "Cookie": f"ss-id={session_cookie}"
    }
    response = requests.get(erp_balances_url, headers=headers)
    item_balances = response.json()
    return item_balances

def transform_balance_for_opencart(balance):
    transformed_balance = {
        "sku": balance["Code"],
        "quantity": balance["Balance"],
    }
    return transformed_balance

def get_user_answers_from_db():
    answers = UserAnswer.objects.latest('id')
    return answers

def update_product_quantity_in_opencart(opencart_api_url, balances, opencart_api_key):
    # The API endpoint for updating quantities
    update_url = f"{opencart_api_url}/quantitybysku"

    # Set the headers for the request
    headers = {"X-Oc-Restadmin-Id": opencart_api_key}

    # Prepare the data for the request. The data should be a list of dictionaries.
    data = [{"sku": balance["sku"], "quantity": str(balance["quantity"])} for balance in balances]

    # Send a PUT request with the formatted data
    response = requests.put(update_url, json=data, headers=headers)

    # Check the response and log accordingly
    if response.status_code == 200:
        logger.info("Product quantities successfully updated in OpenCart.")
    else:
        logger.error(f"Error updating product quantities in OpenCart: {response.text}")

def run_import():
    user_answers = get_user_answers_from_db()

    store_domain = user_answers.store_domain
    store_path = user_answers.store_path
    erp_server_ip = user_answers.erp_server_ip
    erp_server_port = user_answers.erp_server_port
    erp_username = user_answers.erp_username
    erp_password = user_answers.erp_password
    opencart_api_key = user_answers.opencart_api_key

    opencart_api_url = f"https://{store_domain}{store_path}/index.php?route=rest/product_admin/productquantitybysku"
    print(opencart_api_url)
    session_cookie = authenticate_with_erp(erp_username, erp_password, erp_server_ip, erp_server_port)

    if session_cookie:
        erp_balances = fetch_item_balances_from_erp(session_cookie, erp_server_ip, erp_server_port)

        if erp_balances:
            transformed_balances = [transform_balance_for_opencart(balance) for balance in erp_balances]
            update_product_quantity_in_opencart(opencart_api_url, transformed_balances, opencart_api_key)
            print(transformed_balances)
        else:
            logger.error("No item balances retrieved from ERP.")

        logger.info("Balance synchronization completed.")
    else:
        logger.error("Authentication with ERP failed.")
