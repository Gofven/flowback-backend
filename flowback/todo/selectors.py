from flowback.todo.models import Todo


def todo_get(*, user=int):
    return Todo.objects.filter(user_id=user).all()
