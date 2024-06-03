import requests
import logging
from django.http import JsonResponse
from .models import CategoryMapping, UserAnswer

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

def fetch_categories_from_erp(session_cookie, erp_server_ip, erp_server_port):
    erp_categories_path = "/services/sync/itemcategories"
    erp_categories_url = f"http://{erp_server_ip}:{erp_server_port}{erp_categories_path}"
    headers = {
        "Cookie": f"ss-id={session_cookie}"
    }
    response = requests.get(erp_categories_url, headers=headers)

    print("Fetching categories from ERP...")  # Debugging line
    if response.status_code == 200:
        categories = response.json()
        print(f"Fetched {len(categories)} categories from ERP.")  # Debugging line
        return categories
    else:
        print(f"Failed to fetch categories from ERP. Status Code: {response.status_code}")  # Debugging line
        return []

def transform_category_for_opencart(category, categories_mapping, set_parent_id=True):
    parent_id = categories_mapping.get(category.get("ParentNodeID"), 0) if set_parent_id else 0

    transformed_category = {
        "category_description": [
            {
                "name": category["Description"],
                "description": "Description for " + category["Description"],
                "language_id": 2,
                "meta_description": "Meta description for " + category["Description"],
                "meta_keyword": category["Description"],
                "meta_title": category["Description"]
            }
        ],
        "sort_order": 0,
        "category_store": ["0"],
        "parent_id": parent_id,
        "status": "1",
        "column": 1,
        "top": "0",
        "category_layout": ["3"],
        "keyword": category["Code"]
    }
    return transformed_category

def update_category_with_parent_id(category, categories_mapping, opencart_api_url, opencart_api_key):
    parent_id = categories_mapping.get(category["ParentNodeID"])
    if parent_id is not None:
        category_id = categories_mapping.get(category["ID"])
        if category_id is not None:
            update_url = f"{opencart_api_url}&id={category_id}"
            updated_category_data = {"parent_id": parent_id}
            response = requests.put(update_url, headers={"X-Oc-Restadmin-Id": opencart_api_key}, json=updated_category_data)

            if response.status_code == 200:
                logger.info(f"Updated category {category['Description']} in OpenCart with parent ID {parent_id}.")
            else:
                logger.error(f"Error updating category in OpenCart: {response.text}")


def read_categories_mapping():
    mappings = CategoryMapping.objects.all()
    return {mapping.erp_id: mapping.opencart_id for mapping in mappings}

def get_user_answers_from_db():
    return UserAnswer.objects.latest('id')

def sync_categories(erp_categories, opencart_api_url, opencart_api_key, is_top_level=True):
    categories_mapping = read_categories_mapping()

    # Step 1: Initially create all categories without setting parent_id
    for category in erp_categories:
        erp_id = category["ID"]
        if CategoryMapping.objects.filter(erp_id=erp_id).exists():
            logger.info(f"Category with ERP ID {erp_id} already exists in OpenCart. Skipping.")
            continue

        transformed_category = transform_category_for_opencart(category, categories_mapping, set_parent_id=False)
        response = requests.post(opencart_api_url, headers={"X-Oc-Restadmin-Id": opencart_api_key}, json=transformed_category)

        if response.status_code == 200:
            response_data = response.json()
            opencart_category_id = response_data.get('data', {}).get('id')
            mapping = CategoryMapping.objects.create(erp_id=erp_id, opencart_id=opencart_category_id)
            logger.info(f"Category {transformed_category['category_description'][0]['name']} initially created in OpenCart with ID {opencart_category_id}.")
        else:
            logger.error(f"Error creating category in OpenCart: {response.text}")

    # Refresh the categories_mapping after initial creation
    categories_mapping = read_categories_mapping()

    # Step 2: Update categories with their correct parent_id
    for category in erp_categories:
        if category.get("ParentNodeID") is not None:
            update_category_with_parent_id(category, categories_mapping, opencart_api_url, opencart_api_key)



def run_import():
    print("Starting import process...")  # Debugging line

    user_answers = get_user_answers_from_db()
    print("Fetched user answers from the database.")  # Debugging line

    store_domain = user_answers.store_domain
    store_path = user_answers.store_path
    erp_server_ip = user_answers.erp_server_ip
    erp_server_port = user_answers.erp_server_port
    erp_username = user_answers.erp_username
    erp_password = user_answers.erp_password
    opencart_api_key = user_answers.opencart_api_key

    session_cookie = authenticate_with_erp(erp_username, erp_password, erp_server_ip, erp_server_port)
    opencart_api_url = f"https://{store_domain}{store_path}/index.php?route=rest/category_admin/category"

    if session_cookie:
        erp_categories = fetch_categories_from_erp(session_cookie, erp_server_ip, erp_server_port)
        print(f"Fetched {len(erp_categories)} categories from ERP.")  # Debugging line

        # Call the sync_categories function
        print("Calling sync_categories function...")  # Debugging line
        sync_categories(erp_categories, opencart_api_url, opencart_api_key)

        logger.info("Categories synchronization completed.")
    else:
        logger.error("Authentication with ERP failed.")

    return JsonResponse({"message": "Categories synchronization completed"})
