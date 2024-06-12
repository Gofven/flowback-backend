import random

import factory

from flowback.common.tests import fake
from flowback.kanban.models import KanbanEntry

class KanbanEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = KanbanEntry

    description = factory.lazy_attribute(lambda _: fake.sentence())
    tag = factory.LazyAttribute(lambda _: random.randint(1, 5))
