from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from zeep import Client
# from zeep.transports import Transport
# from requests import Session
# from requests.auth import HTTPBasicAuth
from django.http import JsonResponse
from zeep.helpers import serialize_object
from .models import Transaction
import hashlib
import random
import json
from .models import Location
    

# Function for AJAX search request
def search_locations(request):
    # Check if the request is AJAX (sent via JavaScript)
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, '404.html', status=404)  # Show custom 404 page

    query = request.GET.get('query', '')
    type_param = request.GET.get('type', '').upper()  # Expecting 'B' or 'W'

    type_map = {
        'B': 'BANK',
        'W': 'WALLET'
    }

    location_type = type_map.get(type_param)

    if not query or not location_type:
        return JsonResponse({"error": "404 Not Found"}, status=404)

    locations = Location.objects.filter(
        location_type=location_type,
        location_name__icontains=query
    )[:20]

    results = [{"location_name": loc.location_name, "location_code": loc.location_code} for loc in locations]

    return JsonResponse(results, safe=False)

# Function for generating diffrent Agent_Txn id

def generate_agent_txnid():
    return 'CT' + ''.join(str(random.randint(0, 9)) for _ in range(7))


# Initialize SOAP client (lazy-loaded)
_client = None
def get_soap_client():
    global _client
    if _client is None:
        wsdl_url = 'https://newuat.ct-xpress.net/SendWSv5/txnservice.asmx?WSDL'
        _client = Client(wsdl=wsdl_url)
    return _client

# SHA-256 signature generator
def generate_signature(data, api_password):
    raw_string = (
        data['AGENT_CODE'] +
        data['USER_ID'] +
        data['AGENT_SESSION_ID'] +
        data['AGENT_TXNID'] +
        data['LOCATION_ID'] +
        data['SENDER_FIRST_NAME'] +
        data['SENDER_LAST_NAME'] +
        data['SENDER_GENDER'] +
        data['SENDER_ADDRESS'] +
        data['SENDER_CITY'] +
        data['SENDER_COUNTRY'] +
        data['SENDER_ID_TYPE'] +
        data['SENDER_ID_NUMBER'] +
        data['SOURCE_OF_FUND'] +
        data['RECEIVER_FIRST_NAME'] +
        data['RECEIVER_LAST_NAME'] +
        data['RECEIVER_ADDRESS'] +
        data['RECEIVER_COUNTRY'] +
        data['RECEIVER_CONTACT_NUMBER'] +
        data['RELATIONSHIP_TO_BENEFICIARY'] +
        data['PAYMENT_MODE'] +
        data['BANK_NAME'] +
        data['BANK_ACCOUNT_NUMBER'] +
        data['CALC_BY'] +
        data['TRANSFER_AMOUNT'] +
        data['PURPOSE_OF_REMITTANCE'] +
        data['AUTHORIZED_REQUIRED'] +
        api_password
    )
    return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

@login_required
def send_transaction(request):
    if request.method == 'POST':
        transaction = None
        try:
            client = get_soap_client()

            # Clean input data
            form = {key: value.strip() for key, value in request.POST.items()}
            api_password = '1234567A'
            agent_txnid = generate_agent_txnid()

            payment_mode = form.get('PAYMENT_MODE', '')
            location_id = None

            if payment_mode in ['B', 'W']:
                bank_name = form.get('BANK_NAME', '')
                if bank_name:
                    try:
                        location = Location.objects.get(location_name__iexact=bank_name)
                        location_id = location.location_code
                    except Location.DoesNotExist:
                        return HttpResponse("Invalid Bank/Wallet Name. Location ID not found.", status=400)
                else:
                    return HttpResponse("Bank/Wallet Name is required.", status=400)
            elif payment_mode == 'C':
                location_id = "89100100"
            else:
                return HttpResponse("Invalid payment mode.", status=400)

            if not location_id:
                return HttpResponse("Missing LOCATION_ID. Cannot proceed.", status=400)

            # Prepare payload
            payload = {
                'AGENT_CODE': 'TR001',
                'USER_ID': 'sendv5',
                'AGENT_SESSION_ID': '89534531000100',
                'AGENT_TXNID': agent_txnid,
                'LOCATION_ID': location_id,
                'SENDER_FIRST_NAME': form.get('SENDER_FIRST_NAME'),
                'SENDER_LAST_NAME': form.get('SENDER_LAST_NAME'),
                'SENDER_GENDER': form.get('SENDER_GENDER'),
                'SENDER_ADDRESS': form.get('SENDER_ADDRESS'),
                'SENDER_CITY': form.get('SENDER_CITY'),
                'SENDER_COUNTRY': form.get('SENDER_COUNTRY'),
                'SENDER_ID_TYPE': form.get('SENDER_ID_TYPE'),
                'SENDER_ID_NUMBER': form.get('SENDER_ID_NUMBER'),
                'SOURCE_OF_FUND': form.get('SOURCE_OF_FUND'),
                'RECEIVER_FIRST_NAME': form.get('RECEIVER_FIRST_NAME'),
                'RECEIVER_LAST_NAME': form.get('RECEIVER_LAST_NAME'),
                'RECEIVER_ADDRESS': form.get('RECEIVER_ADDRESS'),
                'RECEIVER_COUNTRY': form.get('RECEIVER_COUNTRY'),
                'RECEIVER_CONTACT_NUMBER': form.get('RECEIVER_CONTACT_NUMBER'),
                'RELATIONSHIP_TO_BENEFICIARY': form.get('RELATIONSHIP_TO_BENEFICIARY'),
                'PAYMENT_MODE': payment_mode,
                'BANK_NAME': form.get('BANK_NAME'),
                'BANK_ACCOUNT_NUMBER': form.get('BANK_ACCOUNT_NUMBER'),
                'CALC_BY': 'P',
                'TRANSFER_AMOUNT': form.get('TRANSFER_AMOUNT'),
                'PURPOSE_OF_REMITTANCE': 'FAMILY SUPPORT',
                'AUTHORIZED_REQUIRED': form.get('AUTHORIZED_REQUIRED'),
            }

            payload['SIGNATURE'] = generate_signature(payload, api_password)

            # Save request in DB
            transaction = Transaction.objects.create(
                agent_txnid=agent_txnid,
                status='PENDING',
                sender_first_name=payload['SENDER_FIRST_NAME'],
                sender_last_name=payload['SENDER_LAST_NAME'],
                sender_gender=payload['SENDER_GENDER'],
                sender_address=payload['SENDER_ADDRESS'],
                sender_city=payload['SENDER_CITY'],
                sender_country=payload['SENDER_COUNTRY'],
                sender_id_type=payload['SENDER_ID_TYPE'],
                sender_id_number=payload['SENDER_ID_NUMBER'],
                source_of_fund=payload['SOURCE_OF_FUND'],
                sender_nationality=form.get('SENDER_NATIONALITY'),
                receiver_first_name=payload['RECEIVER_FIRST_NAME'],
                receiver_last_name=payload['RECEIVER_LAST_NAME'],
                receiver_address=payload['RECEIVER_ADDRESS'],
                receiver_country=payload['RECEIVER_COUNTRY'],
                receiver_contact_number=payload['RECEIVER_CONTACT_NUMBER'],
                relationship_to_beneficiary=payload['RELATIONSHIP_TO_BENEFICIARY'],
                payment_mode=payment_mode,
                bank_name=payload['BANK_NAME'],
                bank_account_number=payload['BANK_ACCOUNT_NUMBER'],
                transfer_amount=payload['TRANSFER_AMOUNT'],
                request_payload=json.dumps(payload),
                response_payload=json.dumps(payload),  
            )

            # API Call
            response = client.service.SendTransaction(**payload)
            data = serialize_object(response)

            # Update transaction
            transaction.pinno = data.get('PINNO')
            transaction.status = 'SUCCESS' if data.get('CODE') == '0' else 'FAILED'
            transaction.response_payload = json.dumps(data)
            transaction.save()

            return render(request, 'transaction_success.html', {'data': data})

        except Exception as e:
            if transaction is not None:
                transaction.status = 'FAILED'
                transaction.response_payload = json.dumps({'error': str(e)})
                transaction.save()
            return HttpResponse(f"SOAP Error: {str(e)}", status=500)

    return render(request, 'send_transaction_form.html')

 
  
# Login page code

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Both fields are required.')
            return redirect('login')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')  # Change this as needed
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')



@login_required
def main(request):
  template = loader.get_template('home.html')
  return HttpResponse(template.render({}, request))

def logout_view(request):
    logout(request)
    return redirect('login')