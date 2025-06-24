from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import Transaction  # adjust import path if needed
from django.shortcuts import render
from .models import Transaction
from django.db.models import Q


@login_required
def transaction_report(request):
    transactions = None  # Show empty by default
    error_message = None  # To pass to the template

    if request.GET.get('filter'):
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        payment_mode = request.GET.get('payment_mode')
        status = request.GET.get('status')
        sender_name = request.GET.get('sender_name')
        receiver_name = request.GET.get('receiver_name')

        # Check mandatory date fields
        if from_date and to_date:
            filters = Q()
            try:
                filters &= Q(txn_date__date__range=[from_date, to_date])
                if payment_mode:
                    filters &= Q(payment_mode=payment_mode)
                if status:
                    filters &= Q(status__iexact=status)
                if sender_name:
                    filters &= (Q(sender_first_name__icontains=sender_name) | Q(sender_last_name__icontains=sender_name))
                if receiver_name:
                    filters &= (Q(receiver_first_name__icontains=receiver_name) | Q(receiver_last_name__icontains=receiver_name))

                transactions = Transaction.objects.filter(filters).order_by('-txn_date')

            except Exception as e:
                error_message = "An error occurred while filtering: " + str(e)
                transactions = []
        else:
            error_message = "Please select both From Date and To Date to generate the report."
            transactions = []

    return render(request, 'transaction_report.html', {
        'transactions': transactions,
        'error_message': error_message
    })