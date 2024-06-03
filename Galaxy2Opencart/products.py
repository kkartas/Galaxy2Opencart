import requests
import logging
from django.http import JsonResponse
from .models import CategoryMapping, UserAnswer

# Setting up logging
logger = logging.getLogger(__name__)


def authenticate_with_erp(erp_username, erp_password, erp_server_ip, erp_server_port):
    erp_auth_path = "/auth"
    erp_auth_url = f"http://{erp_server_ip}:{erp_server_port}{erp_auth_path}"
    erp_auth_data = {
        "username": erp_username,
        "password": erp_password
    }

    try:
        response = requests.get(erp_auth_url, params=erp_auth_data)
        response.raise_for_status()
        session_cookie = response.cookies.get("ss-id")
        return session_cookie
    except Exception as e:
        logger.error(f"Error during ERP authentication: {e}")
        return None

def fetch_items_from_erp(session_cookie, erp_server_ip, erp_server_port, last_revision_number):
    erp_items_path = "/services/sync/items"
    erp_items_url = f"http://{erp_server_ip}:{erp_server_port}{erp_items_path}"
    params = {
        "RevisionNumber": last_revision_number
    }
    headers = {
        "Cookie": f"ss-id={session_cookie}"
    }

    try:
        response = requests.get(erp_items_url, headers=headers, params=params)
        response.raise_for_status()
        items = response.json()
        return items
    except Exception as e:
        logger.error(f"Error fetching items from ERP: {e}")
        return []

def read_categories_mapping():
    mappings = CategoryMapping.objects.all()
    categories_mapping = {mapping.erp_id: mapping.opencart_id for mapping in mappings}
    return categories_mapping


def transform_item_for_opencart(item, categories_mapping):
    erp_categories = item.get("ItemCategories", [])
    erp_child_category = erp_categories[-1] if erp_categories else None
    opencart_category_id = categories_mapping.get(erp_child_category["CategoryLeafID"], 25) if erp_child_category else 25

    transformed_item = {
        "model": item["Code"],
        "price": str(item["ItemPrice"]),
        "sku": item["Code"],
        "product_store": [0],
        "product_description": [{
            "language_id": 2,
            "name": item["Description"],
            "description": item.get("ExtDescription"),
            "meta_title": item["Description"],
            "meta_description": item.get("ExtDescription"),
        #    "meta_keyword": "keyword",  # Simplified as per your working example
        #    "tag": "tag"
        }],
        "product_category": [opencart_category_id] if opencart_category_id is not None else []
    }
    print (transformed_item)
    return transformed_item


def get_user_answers_from_db():
    answers = UserAnswer.objects.latest('id')  # Assumes a single row or latest entry contains the most recent config

    return answers

def instance_to_dict(instance):
    return {field.name: getattr(instance, field.name) for field in instance._meta.fields}


def run_import():
    user_answer_instance = get_user_answers_from_db()
    user_answers = instance_to_dict(user_answer_instance)

    opencart_api_url = f"https://{user_answers['store_domain']}{user_answers['store_path']}/index.php?route=rest/product_admin/products"
    opencart_api_key = user_answers['opencart_api_key']

    session_cookie = authenticate_with_erp(user_answers['erp_username'], user_answers['erp_password'], user_answers['erp_server_ip'], user_answers['erp_server_port'])
    categories_mapping = read_categories_mapping()

    if session_cookie:
        erp_items = fetch_items_from_erp(session_cookie, user_answers['erp_server_ip'], user_answers['erp_server_port'], user_answers['last_revision_number'])

        if erp_items:
            for item in erp_items:
                transformed_item = transform_item_for_opencart(item, categories_mapping)

                # Check if product already exists in OpenCart
                check_url = f"https://{user_answers['store_domain']}{user_answers['store_path']}/index.php?route=rest/product_admin/getproductbysku&sku={transformed_item['sku']}"
                existing_product_response = requests.get(check_url, headers={"X-Oc-Restadmin-Id": opencart_api_key})
                if existing_product_response.status_code == 200:
                    response_data = existing_product_response.json()
                    if response_data.get('success') == 1 and response_data.get('data'):
                        product_id = response_data['data'].get('id')
                        if product_id:
                            # Update the existing product in OpenCart
                            update_url = f"{opencart_api_url}&id={product_id}"
                            update_response = requests.put(update_url, headers={"X-Oc-Restadmin-Id": opencart_api_key}, json=transformed_item)
                            if update_response.status_code == 200:
                                logger.info(f"Item {transformed_item['product_description'][0]['name']} updated successfully in OpenCart.")
                            else:
                                logger.error(f"Error updating item {transformed_item['product_description'][0]['name']} in OpenCart: {update_response.text}")
                            continue

                # If the product does not exist, post it to OpenCart
                created_item_response = requests.post(opencart_api_url, headers={"X-Oc-Restadmin-Id": opencart_api_key}, json=transformed_item)
                if created_item_response.status_code == 200:
                    logger.info(f"Item {transformed_item['product_description'][0]['name']} successfully posted to OpenCart.")
                else:
                    logger.error(f"Error posting item {transformed_item['product_description'][0]['name']} to OpenCart: {created_item_response.text}")

                user_answers['last_revision_number'] = item["RevisionNumber"]
                user_answer_instance.last_revision_number = user_answers['last_revision_number']
                user_answer_instance.save()
        else:
            logger.info("All items have been synced!")

    else:
        logger.error("Authentication with ERP failed.")

    return JsonResponse({"messages": "Product synchronization completed"})