from rest_framework import serializers
from .models import Account, Transaction

class AccountListInputSerializer(serializers.Serializer):
    order_by = serializers.CharField(required=False)
    id = serializers.IntegerField(required=False)
    
class AccountListOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    account_number = serializers.CharField()
    account_name = serializers.CharField()
    balance = serializers.FloatField()
    

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'account_name', 'balance']

class TransactionListOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    debit_amount = serializers.FloatField()
    credit_amount = serializers.FloatField()
    description = serializers.CharField()
    verification_number = serializers.CharField()
    date = serializers.DateTimeField()

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'debit_amount', 'credit_amount', 'description', 'verification_number', 'date']
    
    def validate(self, data):
        if not data.get('debit_amount') and not data.get('credit_amount'):
            raise serializers.ValidationError("You must provide a debit or credit amount.")
        if data.get('debit_amount') and data.get('credit_amount'):
            raise serializers.ValidationError("Each transaction must have either a debit or a credit amount, but not both")
        if data.get('debit_amount', 0) <= 0 and data.get('credit_amount', 0) <= 0:
            raise serializers.ValidationError("The debit or credit amount must be greater than zero.")
        return data