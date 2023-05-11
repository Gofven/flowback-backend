from django.urls import path

from .views import (AccountListAPI,
                    AccountCreateAPI,
                    AccountUpdateApi,
                    AccountDeleteAPI,
                    TransactionListAPI,
                    TransactionCreateAPI,
                    TransactionUpdateApi,
                    TransactionDeleteAPI)

accounts_patterns = [
    path('accounts', AccountListAPI.as_view(), name='accounts_list'),
    path('accounts/create', AccountCreateAPI.as_view(), name='accounts_create'),
    path('accounts/<int:account_id>/update',
         AccountUpdateApi.as_view(), name='accounts_update'),
    path('accounts/<int:account_id>/delete',
         AccountDeleteAPI.as_view(), name='accounts_delete'),
    path('accounts/<int:account_id>/transactions',
         TransactionListAPI.as_view(), name='transactions_list'),
    path('accounts/<int:account_id>/transactions/create',
         TransactionCreateAPI.as_view(), name='transactions_create'),
    path('accounts/<int:account_id>/transactions/<int:transaction_id>/update',
         TransactionUpdateApi.as_view(), name='transactions_update'),
    path('accounts/<int:account_id>/transactions/<int:transaction_id>/delete',
         TransactionDeleteAPI.as_view(), name='transactions_update'),
]
