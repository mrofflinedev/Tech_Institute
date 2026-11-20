import os, requests

# Bridge URL - from .env, fallback to your Render URL
BRIDGE_URL = os.environ.get("MPESA_BRIDGE_URL", "https://mpesa-bridge-5od8.onrender.com").rstrip("/")

def initiate_stk_push(phone, amount, account_reference="TechInstitute", callback_url=None):
    try:
        # Clean phone: 07... -> 254...
        phone = str(phone).strip()
        if phone.startswith("07") or phone.startswith("01"):
            phone = "254" + phone[1:]
        elif phone.startswith("+254"):
            phone = phone[1:]

        payload = {
            "phone": phone,
            "PhoneNumber": phone,
            "amount": int(float(amount)),
            "Amount": int(float(amount)),
            "account_reference": account_reference,
            "AccountReference": account_reference,
            "callback_url": callback_url,
        }

        # Try /stkpush first - this is what most bridges use
        r = requests.post(f"{BRIDGE_URL}/stkpush", json=payload, timeout=90)
        print(f"BRIDGE RESPONSE: {r.status_code} {r.text}")

        try:
            data = r.json()
        except:
            return {"ResponseCode": "1", "errorMessage": f"Bridge returned non-JSON: {r.text[:200]}"}

        # Normalize Bridge response to what views.py expects
        if data.get("ResponseCode") == "0" or data.get("CheckoutRequestID"):
            return data
        # If bridge returns Daraja error, pass it through
        return {
            "ResponseCode": data.get("ResponseCode", "1"),
            "CheckoutRequestID": data.get("CheckoutRequestID", ""),
            "errorMessage": data.get("errorMessage") or data.get("ResponseDescription") or data.get("error") or str(data)[:300]
        }
    except Exception as e:
        print(f"BRIDGE ERROR: {e}")
        return {"ResponseCode": "1", "errorMessage": str(e)}