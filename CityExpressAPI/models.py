from django.db import models


class Transaction(models.Model):
    agent_txnid = models.CharField(max_length=30, unique=True)
    pinno = models.CharField(max_length=30, null=True, blank=True)
    sender_first_name = models.CharField(max_length=100)
    sender_last_name = models.CharField(max_length=100)
    sender_gender = models.CharField(max_length=10)
    sender_address = models.CharField(max_length=200)
    sender_city = models.CharField(max_length=100)
    sender_country = models.CharField(max_length=50)
    sender_id_type = models.CharField(max_length=50)
    sender_id_number = models.CharField(max_length=50)
    source_of_fund = models.CharField(max_length=50)
    sender_nationality = models.CharField(max_length=50)
    receiver_first_name = models.CharField(max_length=100)
    receiver_last_name = models.CharField(max_length=100)
    receiver_address = models.CharField(max_length=200)
    receiver_country = models.CharField(max_length=50)
    receiver_contact_number = models.CharField(max_length=20)
    relationship_to_beneficiary = models.CharField(max_length=50)
    payment_mode = models.CharField(max_length=10)
    transfer_amount = models.DecimalField(max_digits=10, decimal_places=2)
    txn_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending',blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    request_payload = models.TextField(blank=True, null=True)
    response_payload = models.TextField(blank=True, null=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_account_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.agent_txnid} - {self.pinno or 'No PIN yet'}"

# Location Model
class Location(models.Model):
    location_name = models.CharField(max_length=100, null=True, blank=True)
    location_code = models.CharField(max_length=20, null=True, blank=True)
    location_type = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.location_name}, {self.location_type},{self.location_code}"
        
# TransactionLog Model

class TransactionLog(models.Model):
    transaction = models.ForeignKey(
        'Transaction',                     # Reference to your Transaction model
        to_field='agent_txnid',            # Use agent_txnid instead of the default PK
        on_delete=models.CASCADE,          # If a transaction is deleted, its logs will be too
        related_name='logs'                # Optional: allows reverse access (e.g., txn.logs.all())
    )

    request_type = models.CharField(max_length=50)  # e.g., 'SendTransaction', 'QueryTxnStatus'
    request_payload = models.TextField()
    response_payload = models.TextField()
    status = models.CharField(max_length=30,blank=True, null=True)        # Optional: e.g., 'SUCCESS', 'FAILURE'
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.transaction.agent_txnid} ({self.request_type})"

# Members Model
class Member(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    joined_date = models.DateField(auto_now_add=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.name
# Create your models here.
