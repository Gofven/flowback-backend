from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from flowback.ledger.selectors import account_list, transaction_list

from flowback.ledger.services import account_create, account_update, account_delete, transaction_create, transaction_update, transaction_delete
from flowback.common.pagination import LimitOffsetPagination, get_paginated_response
from .serializers import AccountListInputSerializer, AccountListOutputSerializer, AccountSerializer, TransactionListOutputSerializer, TransactionSerializer


class AccountListAPI(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    def get(self, request):
        serializer = AccountListInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        accounts = account_list(user_id=request.user.id,
                                filters=serializer.validated_data)

        return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=AccountListOutputSerializer,
                                      queryset=accounts,
                                      request=request,
                                      view=self)


class AccountCreateAPI(APIView):
    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = account_create(user_id=request.user.id,
                                 **serializer.validated_data)

        return Response(status=status.HTTP_200_OK, data=account.id)


class AccountUpdateApi(APIView):
    def post(self, request, account_id: int):
        serializer = AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account_update(user_id=request.user.id, account_id=account_id,
                       data=serializer.validated_data)
        return Response(status=status.HTTP_200_OK)


class AccountDeleteAPI(APIView):
    def post(self, request, account_id: int):
        account_delete(user_id=request.user.id, account_id=account_id)

        return Response(status=status.HTTP_200_OK)


class TransactionListAPI(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    def get(self, request, account_id: int):
        serializer = AccountListInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        transactions = transaction_list(account_id=account_id,
                                        filters=serializer.validated_data)

        return get_paginated_response(pagination_class=self.Pagination,
                                      serializer_class=TransactionListOutputSerializer,
                                      queryset=transactions,
                                      request=request,
                                      view=self)


class TransactionCreateAPI(APIView):
    def post(self, request, account_id: int):
        serializer = TransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = transaction_create(account_id=account_id, user_id=request.user.id,
                                     **serializer.validated_data)

        return Response(status=status.HTTP_200_OK, data=account.id)


class TransactionUpdateApi(APIView):
    def post(self, request, account_id: int, transaction_id: int):
        serializer = TransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction_update(account_id=account_id, user_id=request.user.id,
                           transaction_id=transaction_id,
                           data=serializer.validated_data)
        return Response(status=status.HTTP_200_OK)


class TransactionDeleteAPI(APIView):
    def post(self, request, account_id: int, transaction_id: int):
        transaction_delete(user_id=request.user.id,
                           transaction_id=transaction_id, account_id=account_id)

        return Response(status=status.HTTP_200_OK)
