from flowback.todo.models import Todo
from django.shortcuts import get_object_or_404


def todo_create(*, user=int, category=int, content=int):
    Todo.objects.create(user=user, category=category, content=content)


def todo_delete(*, todo=int):
    obj = get_object_or_404(todo)
    obj.delete()
