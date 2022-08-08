from django.urls import path, include

from flowback.todo.views import TodoCreateApi, TodoGetApi, TodoDeleteApi

todo_patterns = [
    path('', TodoGetApi.as_view(), name='todo-get'),
    path('create/', TodoCreateApi.as_view(), name='todo-create'),
    path('delete/', TodoDeleteApi.as_view(), name='todo-delete')
]

urlpatterns = [
    path('todo/', include((todo_patterns, 'todo')))
]