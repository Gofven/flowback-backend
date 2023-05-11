from datetime import datetime

from flowback.common.services import model_update, get_object
from flowback.ledger.models import Account, Transaction
from flowback.user.models import User
from django.core.exceptions import ValidationError


def account_create(*, account_number: str, account_name: str, user_id: int) -> Account:
    user = get_object(User, id=user_id)
    account = Account(account_number=account_number,
                      account_name=account_name, user=user)

    account.full_clean()
    account.save()

    return account


def account_update(user_id: int, account_id: int, data) -> Account:
    account = get_object(Account, id=account_id)

    if account.user_id != user_id:
        raise ValidationError("Account doesn't belong to User")

    data['updated_at'] = datetime.now()
    non_side_effect_fields = ['account_number', 'account_name', 'updated_at']
    account, has_updated = model_update(instance=account,
                                        fields=non_side_effect_fields,
                                        data=data)
    return account


def account_delete(user_id: int, account_id: int):
    account = get_object(Account, id=account_id)

    if account.user_id != user_id:
        raise ValidationError("Account doesn't belong to User")

    account.delete()


def transaction_create(*, user_id: int, debit_amount: float = 0, credit_amount: float = 0, description: str, verification_number: str, account_id: int, date: str = datetime.now()) -> Transaction:
    account = get_object(Account, id=account_id)

    if account.user_id != user_id:
        raise ValidationError("Account doesn't belong to User")

    transaction = Transaction(
        account=account,
        debit_amount=debit_amount,
        credit_amount=credit_amount,
        description=description,
        verification_number=verification_number,
        date=date
    )

    transaction.full_clean()
    transaction.save()

    return transaction


def transaction_update(user_id: int, account_id: int, transaction_id: int, data) -> Account:
    account = get_object(Account, id=account_id)
    transaction = get_object(Transaction, id=transaction_id)

    if account.id != transaction.account_id:
        raise ValidationError("Transaction doesn't belong to Account")

    if account.user_id != user_id:
        raise ValidationError("Account doesn't belong to User")

    if 'debit_amount' in data:
        data['credit_amount'] = 0
    else:
        data['debit_amount'] = 0

    data['updated_at'] = datetime.now()
    non_side_effect_fields = [
        'debit_amount', 'credit_amount', 'description', 'verification_number', 'date', 'updated_at']
    transaction, has_updated = model_update(instance=transaction,
                                            fields=non_side_effect_fields,
                                            data=data)
    return transaction

def transaction_delete(user_id: int, account_id: int, transaction_id: int):
    account = get_object(Account, id=account_id)
    transaction = get_object(Transaction, id=transaction_id)

    if account.user_id != user_id:
        raise ValidationError("Account doesn't belong to User")

    transaction.delete()