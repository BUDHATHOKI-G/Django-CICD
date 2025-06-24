from django.contrib import admin
from .models import Member
from .models import Location
from .models import Transaction
from .models import TransactionLog
from import_export.admin import ImportExportModelAdmin
# Register your models here.

admin.site.register(Member)
# admin.site.register(Location)
admin.site.register(Transaction)

# admin site register TransactinLog
admin.site.register(TransactionLog)


# For excel import export at admin portal

@admin.register(Location)
class LocationAdmin(ImportExportModelAdmin):
    pass