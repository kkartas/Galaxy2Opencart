import requests
import json
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

def retrieve_order_data_from_opencart(opencart_api_url, opencart_api_key, status_id=1):
    orders_url = f"{opencart_api_url}/listorderswithdetails&filter_order_status_id={status_id}"
    headers = {"X-Oc-Restadmin-Id": opencart_api_key}
    response = requests.get(orders_url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        logger.error("Failed to retrieve orders from OpenCart")
        return []

def post_order_data_to_erp(session_cookie, erp_endpoint, order_data):
    headers = {
        "Cookie": f"ss-id={session_cookie}",
        "Content-Type": "application/json"
    }
    json_order_data = json.dumps(order_data, ensure_ascii=False)
    response = requests.post(erp_endpoint, headers=headers, json=json.loads(json_order_data))
    response_json = response.json()
    json_order_data = json.loads(json_order_data)
    doc_id = json_order_data["body"]["data"]["docid"]
    if response.status_code == 200:
        logger.info(f"Order {doc_id} posted to ERP successfully.")
    else:
        error_message = response_json["ResponseStatus"]["Message"]
        logger.error(f"Error posting order {doc_id} to ERP: {error_message}")

def get_id_from_erp(session_cookie, erp_server_ip, erp_server_port, sku):
    erp_item_url = f"http://{erp_server_ip}:{erp_server_port}/api/glx/entities/item/fetch"
    headers = {
        "Cookie": f"ss-id={session_cookie}",
        "Content-Type": "application/json"
    }
    data = {
        "SelectProperties": ["ID", "LightCrmCode"],
        "Filters": [
            {
                "Name": "LightCrmCode",
                "Type": "Default",
                "Operator": "Equal",
                "Value": sku
            }
        ]
    }
    response = requests.post(erp_item_url, headers=headers, json=data)
    item_data = response.json()
    if item_data:
        product_id = item_data[0].get("ID")
        return product_id
    else:
        return None

def construct_erp_order_data(opencart_order, session_cookie, erp_server_ip, erp_server_port):
    print("Constructing ERP order data for OpenCart order ID:", opencart_order["order_id"])  # Debugging
    print("Products in order:", opencart_order["products"])  # Debugging
    erp_order_data = {
        "body": {
            "header": {
                "version": "2.3.2",
                "processtype": "B2C",
                "source": "Webshop"
            },
            "data": {
                "company": {
                    "identifier": {
                        "id": "7fbc52c2-5aa7-4140-b390-a1cd33f1a853",  # Replace with your company ID
                        "codelist": "RCP"
                    }
                },
                "revisionnumber": 1,
                "doccurrency": {
                    "descr": "\u0395\u03c5\u03c1\u03ce"
                },
                "docid": opencart_order["order_id"],
                "docdate": opencart_order["date_added"],
                "billtoaddress": {
                    "country": {
                        "descr": opencart_order["payment_country"]
                    },
                    "prefecture": {
                        "descr": opencart_order["payment_zone"]
                    },
                    "city": {
                        "descr": opencart_order["payment_city"]
                    },
                    "zipcode": opencart_order["payment_postcode"],
                    "streetname": opencart_order["payment_address_1"],
                    "streetnum": opencart_order["payment_address_2"]
                },
                "deliveryinfo": {
                    "delivdate": opencart_order["date_added"],
                    "address": {
                        "country": {
                            "descr": opencart_order["shipping_country"]
                        },
                        "prefecture": {
                            "descr": opencart_order["shipping_zone"]
                        },
                        "city": {
                            "descr": opencart_order["shipping_city"]
                        },
                        "zipcode": opencart_order["shipping_postcode"],
                        "streetname": opencart_order["shipping_address_1"],
                        "streetnum": opencart_order["shipping_address_2"]
                    },
                    "telephone": opencart_order["telephone"],
                    "email": opencart_order["email"]
                },
                "trader": {
                    "identifier": {
                        "id": "95CDAD23-08DF-4F8A-A954-64837FCCE9CB",  # Replace with trader identifier
                        "codelist": "RCP"
                    },
                    "name": f"{opencart_order['firstname']} {opencart_order['lastname']}",
                    "address": {
                        "country": {
                            "descr": opencart_order["payment_country"]
                        },
                        "prefecture": {
                            "descr": opencart_order["payment_zone"]
                        },
                        "city": {
                            "descr": opencart_order["payment_city"]
                        },
                        "zipcode": opencart_order["payment_postcode"],
                        "streetname": opencart_order["payment_address_1"],
                        "streetnum": opencart_order["payment_address_2"]
                    },
                    "telephone": opencart_order["telephone"],
                    "email": opencart_order["email"]
                },
                "lines": []  # Initialize an empty list for line items
            }
        }
    }

    # Construct line items and add them directly to the 'lines' list in erp_order_data
    for product in opencart_order["products"]:       
        print("Processing product:", product["sku"])  # Debugging
        product_id = get_id_from_erp(session_cookie, erp_server_ip, erp_server_port, product["sku"])
        print("Product ID from ERP:", product_id)  # Debugging
        if product_id:
            erp_line_item = {
                "item": {
                    "mgitemtypeid": 0,
                    "identifier": {
                        "id": product_id,
                        "idspecifier": "ID"
                    }
                },
                "qty": product["quantity"],
                "totalamount": product["total"],
                "chargestotal": 0
            }
            erp_order_data["body"]["data"]["lines"].append(erp_line_item)
            print(f"Added line item for product SKU {product['sku']}")  # Debugging

        else:
            logger.error(f"Product with SKU {product['sku']} not found in ERP.")

    print("Final ERP order data with lines:", json.dumps(erp_order_data, indent=4))  # Debugging
    return erp_order_data


def get_user_answers_from_db():
    answers = UserAnswer.objects.latest('id')
    return answers

def run_import():
    user_answers = get_user_answers_from_db()

    store_domain = user_answers.store_domain
    store_path = user_answers.store_path
    erp_server_ip = user_answers.erp_server_ip
    erp_server_port = user_answers.erp_server_port
    erp_username = user_answers.erp_username
    erp_password = user_answers.erp_password
    opencart_api_key = user_answers.opencart_api_key

    opencart_api_url = f"http://{store_domain}{store_path}/index.php?route=rest/order_admin"
    session_cookie = authenticate_with_erp(erp_username, erp_password, erp_server_ip, erp_server_port)

    if session_cookie:
        opencart_orders = retrieve_order_data_from_opencart(opencart_api_url, opencart_api_key)
        for order in opencart_orders:
            erp_order_data = construct_erp_order_data(order, session_cookie, erp_server_ip, erp_server_port)
            print("Final ERP order data:", json.dumps(erp_order_data, indent=4))  # Debugging
            post_order_data_to_erp(session_cookie, f"http://{erp_server_ip}:{erp_server_port}/services/sync/actions/postentry", erp_order_data)
    else:
        logger.error("Authentication with ERP failed.")
