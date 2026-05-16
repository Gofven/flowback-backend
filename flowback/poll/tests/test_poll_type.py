from django.test import TestCase
from django.utils import timezone

from flowback.poll.classes.poll_type import of
from flowback.poll.models import Poll


class PollTypeInstantiationTest(TestCase):
    """Regression: PollType subclasses must implement every @abstractmethod.

    Repro of: TypeError: Can't instantiate abstract class V2ScorePollType
    without an implementation for abstract methods 'create_proposal_type_data',
    'on_poll_finalized', 'proposal_end_date', 'proposal_preliminary_score',
    'proposal_start_date' — raised in pre_save during Poll save and again at
    /group/poll/<id>/proposal/create when serializer is resolved.
    """

    def _poll(self, poll_type: str) -> Poll:
        now = timezone.now()
        return Poll(
            poll_type=poll_type,
            dynamic=False,
            start_date=now,
            area_vote_end_date=now + timezone.timedelta(hours=1),
            proposal_end_date=now + timezone.timedelta(hours=2),
            prediction_statement_end_date=now + timezone.timedelta(hours=3),
            prediction_bet_end_date=now + timezone.timedelta(hours=4),
            delegate_vote_end_date=now + timezone.timedelta(hours=5),
            vote_end_date=now + timezone.timedelta(hours=6),
            end_date=now + timezone.timedelta(hours=7),
        )

    def test_score_poll_type_instantiates(self):
        of(self._poll(Poll.PollType.SCORE))

    def test_v2_score_poll_type_instantiates(self):
        of(self._poll(Poll.PollType.V2_SCORE))

    def test_schedule_poll_type_instantiates(self):
        poll = self._poll(Poll.PollType.SCHEDULE)
        poll.dynamic = True
        of(poll)
