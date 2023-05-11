from django.db import models
from django.utils import timezone

from flowback.user.models import User

class Account(models.Model):
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def balance(self):
        debit_total = self.transactions.filter(debit_amount__isnull=False).aggregate(models.Sum('debit_amount'))['debit_amount__sum'] or 0
        credit_total = self.transactions.filter(credit_amount__isnull=False).aggregate(models.Sum('credit_amount'))['credit_amount__sum'] or 0
        return credit_total - debit_total

    def __str__(self):
        return self.account_name

class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    debit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.CharField(max_length=100)
    verification_number = models.CharField(max_length=20)
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description