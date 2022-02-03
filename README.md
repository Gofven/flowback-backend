# Flowback

## A liquid democracy engine

The Flowback backend is baded on the python django package.

### Install

After cloning this repo, create a virtual environment:

```
cd flowback-backend
python -m venv env
source env/bin/activate
```

Then install the requirements:

```
pip install -r requirements.txt
```

### 

### Setup

Add your DJANGO_SECRET to environmental variables

#### Apply migrations 

```
python manage.py migrate
```

#### Create a superuser

```
python manage.py createsuperuser
```

*Note: remember these details to sign into the admin portal*

### Running

When starting up the backend be sure you have activated the virtual environment:

```
source env/bin/activate
```

Run the server:

```
python manage.py runserver
```

### Admin

Go to your local endpoint:

```
http://127.0.0.1:8000/admin
```

and log in. This is where you can keep an eye on things. 

### API

**TODO need to get docs on how to interact with these endpoints**

These are the API urls:

```python
default_router.register("user", UserViewSet, basename="user")
default_router.register("me", CurrentUserViewSet, basename="me")
default_router.register("user_group", UserGroupViewSet, basename="user_group")
default_router.register("group_poll", GroupPollViewSet, basename="group_poll")
default_router.register("location", LocationViewSet, basename="location")
default_router.register("friend", FriendsViewSet, basename="friend")
default_router.register('group_chat', GroupChatViewSet, basename='group_chat')
```

