def userinfo(claims, user):
    # Populate claims dict.
    claims['name'] = user.username
    claims['preferred_username'] = user.username
    claims['picture'] = user.profile_image
    claims['website'] = user.website
    claims['updated_at'] = user.updated_at

    claims['email'] = user.email
    claims['email_verified'] = user.email_verified

    return claims