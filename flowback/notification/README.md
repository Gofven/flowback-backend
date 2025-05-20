# Flowback Notification Module
This thread only contains some heads-up information about how to set up Notifications for any given Model

## Creating a Channel
To create a Channel, it is recommended to do it within a model referencing the NotificationChannel instance using post_create:
```python
from flowback.common.models import BaseModel
from flowback.notification.models import NotificationChannel
from flowback.group.models import Group
from django.db import models
from django.db.models.signals import post_save
from django.contrib.contenttypes.fields import GenericRelation


class ExampleModel(BaseModel):
    example_group = models.ForeignKey(Group, on_delete=models.CASCADE)
    notification_channel = GenericRelation(NotificationChannel)
    
    # Notification tag functions start with 'notify_', must call on notification_channel.notify()
    def notify_group(self, group_id: int):
        # TODO include notify return
        return 'notify'

    @property
    def notification_data(self):
        # Data contains default data included in every notification
        return dict(example_id=self.id,
                    group_id=self.example_group.id)

    @classmethod
    def post_save(cls, instance, created, *args, **kwargs):
        if created:
            NotificationChannel.objects.create(name=instance.name,
                                               content_object=instance)


post_save.connect(ExampleModel.post_save, sender=ExampleModel)
```
Note that deleting the `ExampleModel` instance will also delete the NotificationChannel

## Shifting notifications
To shift notifications, all you need to do is run `shift_notifications` on a NotificationChannel instance
