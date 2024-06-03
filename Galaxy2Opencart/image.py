import requests
import base64
import logging
import mimetypes
import tempfile
import os
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

def fetch_image_info_from_erp(session_cookie, erp_server_ip, erp_server_port):
    erp_images_path = "/services/sync/itemimages"
    erp_images_url = f"http://{erp_server_ip}:{erp_server_port}{erp_images_path}"
    headers = {
        "Cookie": f"ss-id={session_cookie}"
    }
    response = requests.get(erp_images_url, headers=headers)
    image_info = response.json()
    return image_info

def retrieve_image_from_erp(session_cookie, erp_server_ip, erp_server_port, image_id):
    erp_image_url = f"http://{erp_server_ip}:{erp_server_port}/api/glx/entities/itemimage/{image_id}"
    headers = {
        "Cookie": f"ss-id={session_cookie}"
    }
    response = requests.get(erp_image_url, headers=headers)
    image_data = response.json()["Image"]
    return image_data

def get_sku_from_erp(session_cookie, erp_server_ip, erp_server_port, item_id):
    erp_item_url = f"http://{erp_server_ip}:{erp_server_port}/api/glx/entities/item/fetch"
    headers = {
        "Cookie": f"ss-id={session_cookie}",
        "Content-Type": "application/json"
    }
    data = {
        "SelectProperties": ["ID", "LightCrmCode"],
        "Filters": [
            {
                "Name": "ID",
                "Type": "Default",
                "Operator": "Equal",
                "Value": item_id
            }
        ]
    }
    response = requests.post(erp_item_url, headers=headers, json=data)
    item_data = response.json()
    
    if item_data:
        sku = item_data[0].get("LightCrmCode")
        return sku
    else:
        return None

def upload_image_to_opencart(opencart_api_url, product_id, image_data, opencart_api_key):
    """Uploads an image to OpenCart for the specified product."""
    # Convert the base64 image data to bytes
    image_bytes = base64.b64decode(image_data)

    # Create a temporary file with the image data
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_image_file:
        temp_image_file.write(image_bytes)
        temp_image_path = temp_image_file.name

    # Determine the MIME type of the image
    mime_type, _ = mimetypes.guess_type(temp_image_path)
    if mime_type is None:
        mime_type = 'image/jpeg'  # Default MIME type

    # Prepare the file for upload
    with open(temp_image_path, 'rb') as image_file:
        files = {'file': (os.path.basename(temp_image_path), image_file, mime_type)}
        headers = {"X-Oc-Restadmin-Id": opencart_api_key}
        url = f"{opencart_api_url}/productimages&id={product_id}"
        print(url)
        # Send POST request to API endpoint
        response = requests.post(url, files=files, headers=headers)
    # Remove the temporary file
    os.remove(temp_image_path)

    # Process response and handle errors
    if response.status_code == 200:
        logger.info(f"Image uploaded successfully for product ID {product_id}")
    else:
        logger.error(f"Failed to upload image for product ID {product_id}: {response.text}")


def get_opencart_product_id_by_sku(opencart_api_url, sku, opencart_api_key):
    request_url = f"{opencart_api_url}/getproductidbyparameter&p=sku&value={sku}"
    response = requests.get(request_url, headers={"X-Oc-Restadmin-Id": opencart_api_key})

    if response.status_code == 200:
        response_data = response.json()
        if response_data.get('success') == 1 and 'data' in response_data and 'id' in response_data['data']:
            return response_data['data']['id']
        else:
            return None
    else:
        logger.error(f"Unsuccessful response from API: Status Code {response.status_code}")
        return None

def get_user_answers_from_db():
    answers = UserAnswer.objects.latest('id')
    return answers

def run_import():
    user_answers = get_user_answers_from_db()
    opencart_api_url = f"https://{user_answers.store_domain}{user_answers.store_path}/index.php?route=rest/product_admin"
    opencart_api_key = user_answers.opencart_api_key
    session_cookie = authenticate_with_erp(user_answers.erp_username, user_answers.erp_password, user_answers.erp_server_ip, user_answers.erp_server_port)

    if session_cookie:
        erp_images = fetch_image_info_from_erp(session_cookie, user_answers.erp_server_ip, user_answers.erp_server_port)

        if erp_images:
            for image_info in erp_images:
                item_id = image_info["ItemID"]
                sku = get_sku_from_erp(session_cookie, user_answers.erp_server_ip, user_answers.erp_server_port, item_id)

                if sku:
                    opencart_product_id = get_opencart_product_id_by_sku(opencart_api_url, sku, opencart_api_key)
                    if opencart_product_id:
                        image_data = retrieve_image_from_erp(session_cookie, user_answers.erp_server_ip, user_answers.erp_server_port, image_info["ID"])
                        upload_image_to_opencart(opencart_api_url, opencart_product_id, image_data, opencart_api_key)
                    else:
                        logger.error(f"SKU '{sku}' not found in OpenCart.")
                else:
                    logger.error(f"Could not find SKU for item ID '{item_id}' in ERP.")
        else:
            logger.error("No images retrieved from ERP.")
    else:
        logger.error("Authentication with ERP failed.")
