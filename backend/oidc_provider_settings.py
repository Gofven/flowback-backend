from flowback.user.models import User


def userinfo(claims, user: User):
    # Populate claims dict.
    claims['name'] = user.username
    claims['preferred_username'] = user.username

    claims['picture'] = user.profile_image
    claims['website'] = user.website

    claims['email'] = user.email
    claims['mail'] = user.email

    return claims
