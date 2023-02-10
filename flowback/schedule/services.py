from django.utils import timezone

from flowback.common.services import model_update, get_object
from flowback.schedule.models import Schedule, ScheduleEvent, ScheduleSubscription


def create_schedule(*, name: str, origin_name: str, origin_id: str) -> Schedule:
    return Schedule.objects.create(name=name, origin_name=origin_name, origin_id=origin_id)


def update_schedule(*, schedule_id: str, **data) -> Schedule:
    schedule = get_object(Schedule, id=schedule_id)
    non_side_effect_fields = ['name']
    schedule, has_updated = model_update(instance=schedule,
                                         fields=non_side_effect_fields,
                                         data=data)
    return schedule


def delete_schedule(*, schedule_id: int):
    schedule = get_object(Schedule, id=schedule_id)
    schedule.delete()


def create_event(*,
                 schedule_id: int,
                 title: str,
                 description: str,
                 start_date: timezone.datetime,
                 end_date: timezone.datetime,
                 origin_name: str,
                 origin_id: str) -> ScheduleEvent:
    event = ScheduleEvent(schedule_id=schedule_id,
                          title=title,
                          description=description,
                          start_date=start_date,
                          end_date=end_date,
                          origin_name=origin_name,
                          origin_id=origin_id)
    event.full_clean()
    return event.save()


def update_event(*, event_id: int, **data) -> ScheduleEvent:
    event = get_object(ScheduleEvent, id=event_id)
    non_side_effect_fields = ['title', 'description', 'start_date', 'end_date']
    event, has_updated = model_update(instance=event,
                                      fields=non_side_effect_fields,
                                      data=data)

    return event


def delete_event(*, event_id: int):
    event = get_object(ScheduleEvent, id=event_id)
    event.delete()


def subscribe_schedule(*, schedule_id: int, target_id: int) -> ScheduleSubscription:
    subscription = ScheduleSubscription(schedule_id=schedule_id, target_id=target_id)
    subscription.clean()
    return subscription.save()


def unsubscribe_schedule(*, subscription_id: int):
    subscription = get_object(ScheduleSubscription, id=subscription_id)
    subscription.delete()

