from django.utils import timezone


# Generates kwargs for Poll to match the given phase
def generate_poll_phase_kwargs(poll_start_phase: str):
    match poll_start_phase:
        case 'proposal_end_date':
            poll_offset_hours = 1
        case 'vote_start_date':
            poll_offset_hours = 2
        case 'delegate_vote_end_date':
            poll_offset_hours = 3
        case 'vote_end_date':
            poll_offset_hours = 4
        case 'end_date':
            poll_offset_hours = 5
        case _:
            poll_offset_hours = 0

    return dict(start_date=timezone.now() + timezone.timedelta(hours=0 - poll_offset_hours),
                proposal_end_date=timezone.now() + timezone.timedelta(hours=1 - poll_offset_hours),
                vote_start_date=timezone.now() + timezone.timedelta(hours=2 - poll_offset_hours),
                delegate_vote_end_date=timezone.now() + timezone.timedelta(hours=3 - poll_offset_hours),
                vote_end_date=timezone.now() + timezone.timedelta(hours=4 - poll_offset_hours),
                end_date=timezone.now() + timezone.timedelta(hours=5 - poll_offset_hours))
