import os
import base64
from datetime import datetime
from curl_cffi import requests

def get_access_token():
    consumer_key = os.environ.get('MPESA_CONSUMER_KEY', 'HUIW5aZ2Xq8hypmjLy7jwfuvwAEnDUda96xUk0jEv9hWoCRG').strip()
    consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET', 'xgKoKLGq5C2CDZJ32WwL9E7RHDpfXA8VzfNdeXD43eThHOGl4JAv4CDGZpAfjmWD').strip()

    if not consumer_key or not consumer_secret:
        return None, "Missing MPESA_CONSUMER_KEY or MPESA_CONSUMER_SECRET in .env"

    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    try:
        response = requests.get(
            api_url,
            auth=(consumer_key, consumer_secret),
            impersonate="chrome",
            timeout=15
        )
        if response.status_code != 200:
            return None, f"Auth failed ({response.status_code}): Check your Consumer Key & Secret in .env"
        return response.json().get('access_token'), None
    except Exception as e:
        return None, f"Auth error: {str(e)}"

def initiate_stk_push(phone_number, amount, account_reference, callback_url):
    access_token, auth_error = get_access_token()
    if auth_error:
        return {"errorMessage": auth_error}

    shortcode = os.environ.get('MPESA_SHORTCODE', '174379').strip()
    passkey = os.environ.get('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919').strip()

    if not passkey or not callback_url:
        return {"errorMessage": "Missing MPESA_PASSKEY or MPESA_CALLBACK_URL in .env"}

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = f"{shortcode}{passkey}{timestamp}"
    password = base64.b64encode(data_to_encode.encode()).decode('utf-8')

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)),
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url.strip(),
        "AccountReference": "TECH_INSTITUTE",
        "TransactionDesc": f"Fee for {account_reference}"
    }

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            impersonate="chrome",
            timeout=15
        )
        return response.json()
    except Exception as e:
        return {"errorMessage": f"STK Push error: {str(e)}"}
