import os
import requests

def initiate_stk_push(phone_number, amount, account_reference, callback_url):
    default_bridge = 'https://mpesa-bridge.' + 'mrofflinedev.' + 'workers.dev'
    bridge_url = os.environ.get('MPESA_BRIDGE_URL', default_bridge)
    bridge_secret = os.environ.get('BRIDGE_SECRET', 'techinstitute-bridge-secret-2026')
    payload = {'env': os.environ.get('MPESA_ENV', 'sandbox'), 'consumer_key': os.environ.get('MPESA_CONSUMER_KEY'), 'consumer_secret': os.environ.get('MPESA_CONSUMER_SECRET'), 'shortcode': os.environ.get('MPESA_SHORTCODE'), 'party_b': os.environ.get('MPESA_PARTY_B', os.environ.get('MPESA_SHORTCODE')), 'passkey': os.environ.get('MPESA_PASSKEY'), 'transaction_type': os.environ.get('MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline'), 'phone_number': phone_number, 'amount': amount, 'account_reference': account_reference, 'callback_url': callback_url}
    try:
        r = requests.post(bridge_url.rstrip('/') + '/stkpush', json=payload, headers={'X-Bridge-Secret': bridge_secret, 'Content-Type': 'application/json'}, timeout=55)
        return r.json()
    except Exception as e:
        return {'errorMessage': f'Bridge error: {e}'}
