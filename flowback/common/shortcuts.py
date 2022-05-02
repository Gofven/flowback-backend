def get_object_or_none(klass, **kwargs):
    try:
        return klass.objects.get(**kwargs)
    except klass.DoesNotExist:
        return None
