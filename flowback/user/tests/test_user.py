import json

from rest_framework import status
from rest_framework.test import APITransactionTestCase, APIRequestFactory, force_authenticate

from flowback.chat.models import MessageChannel, MessageChannelParticipant
from flowback.chat.tests.factories import MessageChannelFactory
from flowback.common.tests import generate_request
from flowback.user.tests.factories import UserFactory
from flowback.user.views.user import UserDeleteAPI, UserGetChatChannelAPI


class UserTest(APITransactionTestCase):
    reset_sequences = True

    def setUp(self):
        (self.user_one,
         self.user_two,
         self.user_three) = (UserFactory() for x in range(3))

    def test_user_delete(self):
        user = self.user_one

        factory = APIRequestFactory()
        view = UserDeleteAPI.as_view()
        request = factory.post('')
        force_authenticate(request, user=user)
        view(request)

        user.refresh_from_db()
        self.assertTrue(user.username.startswith('deleted_user'))
        self.assertTrue(user.email.startswith('deleted_user'))

        self.assertTrue(not all([user.is_active,
                                 user.email_notifications,
                                 user.profile_image,
                                 user.banner_image,
                                 user.bio,
                                 user.website,
                                 user.kanban,
                                 user.schedule]))

    def test_user_get_chat_channel(self):
        participants = UserFactory.create_batch(25)

        response = generate_request(api=UserGetChatChannelAPI,
                                    data=dict(target_user_ids=[u.id for u in participants]),
                                    user=self.user_one)

        # Run second time to make sure we get the same channel_id
        response_two = generate_request(api=UserGetChatChannelAPI,
                                        data=dict(target_user_ids=[u.id for u in participants]),
                                        user=self.user_one)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response_two.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(response.data['id'], response_two.data['id'])
        self.assertTrue(MessageChannel.objects.filter(id=response.data['id']).exists())

        # Count all participants + the user itself
        self.assertEqual(MessageChannelParticipant.objects.filter(channel_id=response.data['id']).count(), 26)

    def test_generate(self):
        import os
        import inspect
        import ast
        from typing import List
        from tabulate import tabulate

        # Function to extract all the functions from a given module's file path
        def get_functions_from_module(file_path: str) -> List[dict]:
            functions = []
            with open(file_path, 'r') as file:
                file_content = file.read()
                tree = ast.parse(file_content)

            # Iterate through all nodes in the file
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_name = node.name
                    signature = inspect.signature(eval(function_name))

                    args = []
                    for param in signature.parameters.values():
                        param_type = param.annotation if param.annotation is not param.empty else 'Any'
                        args.append((param.name, param_type))

                    return_type = signature.return_annotation if signature.return_annotation is not signature.empty else 'Any'

                    # Function summary details
                    function_summary = {
                        'function': f"{function_name}({', '.join([f'{arg[0]}: {arg[1]}' for arg in args])})",
                        'arguments': [f"({arg[1]}) {arg[0]}: argument description" for arg in args],
                        'return': f"({return_type}) return description",
                        'description': "Brief function description",
                    }

                    functions.append(function_summary)

            return functions

        # Function to summarize functions in a specific directory
        def summarize_functions_in_directory(directory: str):
            all_functions = []

            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py'):
                        module_path = os.path.join(root, file)
                        all_functions.extend(get_functions_from_module(module_path))

            return all_functions

        # Function to display the summary table
        def display_summary(functions: List[dict]):
            table = []
            for func in functions:
                table.append([func['function'], func['arguments'][0], func['return'], func['description']])
                # Add rows for additional arguments
                for arg in func['arguments'][1:]:
                    table.append(['', arg, '', ''])

            print(tabulate(table, headers=["Function", "Arguments", "Return", "Description"]))

        # Example usage
        directory_path = 'C:\\Users\\Waffle\\Documents\\Flowback\\backend\\flowback'
        functions = summarize_functions_in_directory(directory_path)
        display_summary(functions)