import hashlib
import json
import logging
from django.conf import settings
from django.shortcuts import render
from zeep import Client
from zeep.transports import Transport
from zeep.exceptions import Fault
from CityExpressAPI.models import Transaction, TransactionLog
from django.contrib.auth.decorators import login_required





logger = logging.getLogger(__name__)


def generate_signature(agent_session_id, agent_txnid=""):
    """
    Generate SHA256 signature as per API documentation.
    """
    agent_code = settings.CITY_EXPRESS_CONFIG['AGENT_CODE']
    user_id = settings.CITY_EXPRESS_CONFIG['USER_ID']
    password = settings.CITY_EXPRESS_CONFIG['PASSWORD']

    raw_data = agent_code + user_id + agent_session_id + agent_txnid + password
    return hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

@login_required
def query_txn_status(request):
    """
    View to query transaction status from City Express API and show recent transactions.
    """
    agent_txnid = request.GET.get('agent_txnid', '').strip()
    context = {
        'agent_txnid': agent_txnid,
        'response': None,
        'error': None,
        'recent_transactions': Transaction.objects.filter(
            payment_mode__in=['B', 'W'],
            status__in=['processing','success','un-paid','hold','compliance']
        ).order_by('-txn_date')[:20]
    }

    if agent_txnid:
        agent_session_id = "DLFJSF"  # Static or dynamic session ID as needed
        signature = generate_signature(agent_session_id, agent_txnid) 

        request_data = {
            'AGENT_CODE': settings.CITY_EXPRESS_CONFIG['AGENT_CODE'],
            'USER_ID': settings.CITY_EXPRESS_CONFIG['USER_ID'],
            'PINNO': '',
            'AGENT_SESSION_ID': agent_session_id,
            'AGENT_TXNID': agent_txnid,
            'SIGNATURE': signature,
        }

        try:
            wsdl_url = settings.CITY_EXPRESS_CONFIG['WSDL_URL']
            client = Client(wsdl=wsdl_url, transport=Transport(timeout=10))
            response = client.service.QueryTXNStatus(**request_data)

            context['response'] = response

            # Extract status from response
            status = getattr(response, 'STATUS', 'UNKNOWN')

            # Find corresponding Transaction
            try:
                txn = Transaction.objects.get(agent_txnid=agent_txnid)
                txn.status = status
                txn.save()

                # Create TransactionLog
                TransactionLog.objects.create(
                    request_type="QueryTXNStatus",
                    request_payload=json.dumps(request_data),
                    response_payload=str(response),
                    status=status,
                    transaction_id=agent_txnid
                )

            except Transaction.DoesNotExist:
                context['error'] = f"Transaction with Agent TXN ID {agent_txnid} not found."
                logger.warning(context['error'])
        except Fault as fault:
            logger.error(f"SOAP Fault: {fault}")
            context['error'] = f"SOAP Fault: {fault}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            context['error'] = str(e)

    return render(request, 'CheckStatus.html', context)
