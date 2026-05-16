from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from django.db.models import Case, F, OuterRef, Subquery, Sum, When
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from backend.settings import FLOWBACK_SCORE_VOTE_CEILING, FLOWBACK_SCORE_VOTE_FLOOR

if TYPE_CHECKING:
    from flowback.poll.models import Poll, PollProposal


_REGISTRY: dict[int, type["PollType"]] = {}


def register(poll_type_id: int):
    def decorator(cls):
        cls.poll_type_id = poll_type_id
        _REGISTRY[poll_type_id] = cls
        return cls

    return decorator


def resolve(poll: "Poll") -> "PollType":
    cls = _REGISTRY.get(poll.poll_type)
    if cls is None:
        raise ValidationError("Unknown poll type")
    return cls(poll)


class PollType(ABC):
    """Strategy: per-poll-type behavior. One subclass per Poll.PollType value, registered via @register."""

    poll_type_id: int

    def __init__(self, poll: "Poll"):
        self.poll = poll

    # --- Labels / phases ---

    @abstractmethod
    def labels(self) -> tuple: ...

    def finished(self) -> bool:
        now = timezone.now()
        return self.poll.end_date is not None and self.poll.end_date <= now

    # --- Create-time validation + post-create / fast-forward tasks ---

    def validate_create(self, *, dynamic: bool, end_date, work_group_id) -> None:
        if work_group_id is not None:
            raise ValidationError("Work groups are only assignable to date polls")

    def schedule_post_create_tasks(self) -> None:
        raise NotImplementedError

    def schedule_fast_forward_tasks(self) -> None:
        raise NotImplementedError

    # --- Proposal create ---

    def create_proposal_type_data(self, proposal: "PollProposal", data: dict) -> None:
        pass

    @abstractmethod
    def proposal_input_serializer_class(self) -> type[serializers.Serializer]: ...

    # --- Proposal list filter ---

    @abstractmethod
    def proposal_filter_class(self) -> type: ...

    # --- Proposal serializer extra fields ---

    def proposal_start_date(self, proposal: "PollProposal"):
        return None

    def proposal_end_date(self, proposal: "PollProposal"):
        return None

    def proposal_preliminary_score(self, proposal: "PollProposal"):
        return None

    # --- Vote ---

    @abstractmethod
    def vote_input_serializer_class(self) -> type[serializers.Serializer]: ...

    @abstractmethod
    def vote_output_serializer_class(self) -> type[serializers.Serializer]: ...

    @abstractmethod
    def delegate_vote_input_serializer_class(self) -> type[serializers.Serializer]: ...

    @abstractmethod
    def update_vote(self, *, group_user, data: dict) -> None: ...

    @abstractmethod
    def update_delegate_vote(self, *, delegate_pool, data: dict) -> None: ...

    # --- Vote count (tasks.py) ---

    @abstractmethod
    def update_vote_scores(self, *, delegate_mandate_subquery) -> None: ...

    def on_poll_finalized(self, *, winning_proposal) -> None:
        pass


# ----------------- Concrete strategies -----------------


@register(4)
class CardinalPollType(PollType):
    def labels(self) -> tuple:
        poll = self.poll
        if poll.dynamic:
            return (
                (poll.start_date, "start_date", "dynamic"),
                (poll.end_date, "end_date", "result"),
            )

        if poll.version == 2:
            return (
                (poll.start_date, "start_date", "proposal"),
                (poll.proposal_end_date, "proposal_end_date", "prediction_bet"),
                (
                    poll.prediction_bet_end_date,
                    "prediction_bet_end_date",
                    "delegate_vote",
                ),
                (poll.delegate_vote_end_date, "delegate_vote_end_date", "vote"),
                (poll.end_date, "end_date", "result"),
            )

        return (
            (poll.start_date, "start_date", "area_vote"),
            (poll.area_vote_end_date, "area_vote_end_date", "proposal"),
            (poll.proposal_end_date, "proposal_end_date", "prediction_statement"),
            (
                poll.prediction_statement_end_date,
                "prediction_statement_end_date",
                "prediction_bet",
            ),
            (poll.prediction_bet_end_date, "prediction_bet_end_date", "delegate_vote"),
            (poll.delegate_vote_end_date, "delegate_vote_end_date", "vote"),
            (poll.vote_end_date, "vote_end_date", "result"),
            (poll.end_date, "end_date", "prediction_vote"),
        )

    def finished(self) -> bool:
        poll = self.poll
        now = timezone.now()
        if poll.version == 2:
            return poll.end_date is not None and poll.end_date <= now
        return (poll.vote_end_date is not None and poll.vote_end_date <= now) or (
            poll.end_date is not None and poll.end_date <= now
        )

    def schedule_post_create_tasks(self) -> None:
        from flowback.poll.tasks import (
            poll_area_vote_count,
            poll_kpi_count,
            poll_prediction_bet_count,
            poll_proposal_vote_count,
        )

        poll = self.poll
        if poll.version == 2:
            poll_kpi_count.apply_async(
                kwargs=dict(poll_id=poll.id), eta=poll.prediction_bet_end_date
            )
        else:
            poll_area_vote_count.apply_async(
                kwargs=dict(poll_id=poll.id), eta=poll.area_vote_end_date
            )
            poll_prediction_bet_count.apply_async(
                kwargs=dict(poll_id=poll.id), eta=poll.prediction_bet_end_date
            )

        if not poll.dynamic:
            eta = poll.end_date if poll.version == 2 else poll.vote_end_date
            poll_proposal_vote_count.apply_async(kwargs=dict(poll_id=poll.id), eta=eta)

    def schedule_fast_forward_tasks(self) -> None:
        from flowback.poll.tasks import (
            poll_area_vote_count,
            poll_kpi_count,
            poll_prediction_bet_count,
        )

        poll = self.poll
        now = timezone.now()
        if poll.version == 2:
            if poll.prediction_bet_end_date and poll.prediction_bet_end_date > now:
                poll_kpi_count.apply_async(
                    kwargs=dict(poll_id=poll.id), eta=poll.prediction_bet_end_date
                )
            else:
                poll_kpi_count(poll_id=poll.id)
        else:
            if poll.area_vote_end_date and poll.area_vote_end_date > now:
                poll_area_vote_count.apply_async(
                    kwargs=dict(poll_id=poll.id), eta=poll.area_vote_end_date
                )
            else:
                poll_area_vote_count(poll_id=poll.id)

            if poll.prediction_bet_end_date and poll.prediction_bet_end_date > now:
                poll_prediction_bet_count.apply_async(
                    kwargs=dict(poll_id=poll.id), eta=poll.prediction_bet_end_date
                )
            else:
                poll_prediction_bet_count(poll_id=poll.id)

    def proposal_input_serializer_class(self) -> type[serializers.Serializer]:
        from flowback.poll.models import PollProposal
        from flowback.files.serializers import FileCollectionCreateSerializerMixin

        class InputSerializerCardinal(
            FileCollectionCreateSerializerMixin, serializers.ModelSerializer
        ):
            class Meta:
                model = PollProposal
                fields = ("title", "description", "blockchain_id")

        return InputSerializerCardinal

    def proposal_filter_class(self) -> type:
        from flowback.poll.selectors.proposal import BasePollProposalFilter

        return BasePollProposalFilter

    def vote_input_serializer_class(self) -> type[serializers.Serializer]:
        class InputSerializerCardinal(serializers.Serializer):
            proposals = serializers.ListField(child=serializers.IntegerField())
            scores = serializers.ListField(child=serializers.IntegerField())

        return InputSerializerCardinal

    def vote_output_serializer_class(self) -> type[serializers.Serializer]:
        from flowback.group.serializers import GroupUserSerializer
        from flowback.poll.models import PollVotingTypeCardinal

        class OutputSerializerTypeCardinal(serializers.ModelSerializer):
            author = GroupUserSerializer(
                source="author.created_by", hide_relevant_users=True
            )

            class Meta:
                model = PollVotingTypeCardinal
                fields = ("author", "author_delegate", "proposal", "score", "raw_score")

        return OutputSerializerTypeCardinal

    def delegate_vote_input_serializer_class(self) -> type[serializers.Serializer]:
        return self.vote_input_serializer_class()

    @staticmethod
    def _validate_scores(scores: list[int]) -> None:
        if FLOWBACK_SCORE_VOTE_CEILING is not None and any(
            s > FLOWBACK_SCORE_VOTE_CEILING for s in scores
        ):
            raise ValidationError(
                f"Voting scores exceeds ceiling bounds (currently set at {FLOWBACK_SCORE_VOTE_CEILING})"
            )
        if FLOWBACK_SCORE_VOTE_FLOOR is not None and any(
            s < FLOWBACK_SCORE_VOTE_FLOOR for s in scores
        ):
            raise ValidationError(
                f"Voting scores exceeds floor bounds (currently set at {FLOWBACK_SCORE_VOTE_FLOOR})"
            )

    def update_vote(self, *, group_user, data: dict) -> None:
        from flowback.poll.models import PollVoting, PollVotingTypeCardinal

        poll = self.poll
        self._validate_scores(data["scores"])

        if not data["proposals"]:
            PollVoting.objects.filter(created_by=group_user, poll=poll).delete()
            return

        if len(data["scores"]) != len(data["proposals"]):
            raise ValidationError("The amount of votes don't match the amount of polls")

        proposals = poll.pollproposal_set.filter(id__in=data["proposals"]).all()
        if len(proposals) != len(data["proposals"]):
            raise ValidationError("Not all proposals are available to vote for")

        user_vote, _ = PollVoting.objects.get_or_create(
            created_by=group_user, poll=poll
        )
        rows = [
            PollVotingTypeCardinal(
                author=user_vote,
                proposal_id=data["proposals"][i],
                raw_score=data["scores"][i],
            )
            for i in range(len(data["proposals"]))
        ]
        PollVotingTypeCardinal.objects.filter(author=user_vote).delete()
        PollVotingTypeCardinal.objects.bulk_create(rows)

    def update_delegate_vote(self, *, delegate_pool, data: dict) -> None:
        from flowback.poll.models import PollDelegateVoting, PollVotingTypeCardinal

        poll = self.poll

        if not data["proposals"]:
            PollDelegateVoting.objects.filter(
                created_by=delegate_pool, poll=poll
            ).delete()
            return

        if len(data["scores"]) != len(data["proposals"]):
            raise ValidationError("The amount of votes don't match the amount of polls")

        proposals = poll.pollproposal_set.filter(id__in=data["proposals"]).all()
        if len(proposals) != len(data["proposals"]):
            raise ValidationError("Not all proposals are available to vote for")

        self._validate_scores(data["scores"])

        pool_vote, _ = PollDelegateVoting.objects.get_or_create(
            created_by=delegate_pool, poll=poll
        )
        rows = [
            PollVotingTypeCardinal(
                author_delegate=pool_vote,
                proposal_id=data["proposals"][i],
                raw_score=data["scores"][i],
            )
            for i in range(len(data["proposals"]))
        ]
        PollVotingTypeCardinal.objects.filter(author_delegate=pool_vote).delete()
        PollVotingTypeCardinal.objects.bulk_create(rows)

    def update_vote_scores(self, *, delegate_mandate_subquery) -> None:
        from flowback.poll.models import PollProposal, PollVotingTypeCardinal
        from flowback.group.selectors.permission import permission_q

        poll = self.poll
        PollVotingTypeCardinal.objects.filter(
            permission_q("author__created_by", "allow_vote"),
            proposal__active=True,
            author__poll=poll,
        ).update(score=F("raw_score"))

        PollVotingTypeCardinal.objects.filter(
            author_delegate__poll=poll,
            proposal__active=True,
        ).update(score=F("raw_score") * Subquery(delegate_mandate_subquery))

        proposal_scores = (
            PollVotingTypeCardinal.objects.filter(
                proposal=OuterRef("id"),
            )
            .values("proposal")
            .annotate(total_score=Sum("score"))
            .values("total_score")
        )

        PollProposal.objects.filter(poll=poll, active=True).update(
            score=Subquery(proposal_scores)
        )


@register(3)
class SchedulePollType(PollType):
    def labels(self) -> tuple:
        poll = self.poll
        return (
            (poll.start_date, "start_date", "schedule"),
            (poll.end_date, "end_date", "result"),
        )

    def finished(self) -> bool:
        poll = self.poll
        now = timezone.now()
        return poll.end_date is not None and poll.end_date <= now

    def validate_create(self, *, dynamic: bool, end_date, work_group_id) -> None:
        if not end_date:
            raise ValidationError("Missing required parameter(s) for schedule poll")
        if not dynamic:
            raise ValidationError("Schedule poll must be dynamic")

    def schedule_post_create_tasks(self) -> None:
        from flowback.poll.tasks import poll_area_vote_count

        poll = self.poll
        poll_area_vote_count.apply_async(
            kwargs=dict(poll_id=poll.id), eta=poll.area_vote_end_date
        )

    def schedule_fast_forward_tasks(self) -> None:
        pass

    def create_proposal_type_data(self, proposal: "PollProposal", data: dict) -> None:
        from flowback.poll.models import PollProposalTypeSchedule

        if not (data.get("start_date") and data.get("end_date")):
            raise ValidationError(
                "Missing start_date and/or end_date, for proposal schedule creation"
            )

        schedule_proposal = PollProposalTypeSchedule(
            proposal=proposal,
            event_start_date=data["start_date"],
            event_end_date=data["end_date"],
        )
        try:
            schedule_proposal.full_clean()
        except ValidationError:
            proposal.delete()
            raise

        schedule_proposal.save()

    def proposal_input_serializer_class(self) -> type[serializers.Serializer]:
        from flowback.poll.models import PollProposal
        from flowback.files.serializers import FileCollectionCreateSerializerMixin

        class InputSerializerSchedule(
            FileCollectionCreateSerializerMixin, serializers.ModelSerializer
        ):
            start_date = serializers.DateTimeField()
            end_date = serializers.DateTimeField()

            def validate(self, data):
                if data.get("start_date") >= data.get("end_date"):
                    raise ValidationError(
                        "Start date can't be the same or later than End date"
                    )
                return data

            class Meta:
                model = PollProposal
                fields = (
                    "title",
                    "description",
                    "blockchain_id",
                    "start_date",
                    "end_date",
                )

        return InputSerializerSchedule

    def proposal_filter_class(self) -> type:
        from flowback.poll.selectors.proposal import BasePollProposalScheduleFilter

        return BasePollProposalScheduleFilter

    def proposal_start_date(self, proposal: "PollProposal"):
        return proposal.pollproposaltypeschedule.event_start_date

    def proposal_end_date(self, proposal: "PollProposal"):
        return proposal.pollproposaltypeschedule.event_end_date

    def proposal_preliminary_score(self, proposal: "PollProposal"):
        return proposal.pollproposaltypeschedule.preliminary_score

    def vote_input_serializer_class(self) -> type[serializers.Serializer]:
        class InputSerializerSchedule(serializers.Serializer):
            proposals = serializers.ListField(child=serializers.IntegerField())

        return InputSerializerSchedule

    def vote_output_serializer_class(self) -> type[serializers.Serializer]:
        from flowback.group.serializers import GroupUserSerializer
        from flowback.poll.models import PollVotingTypeForAgainst

        class OutputSerializerTypeForAgainst(serializers.ModelSerializer):
            author = GroupUserSerializer(
                source="author.created_by", hide_relevant_users=True
            )

            class Meta:
                model = PollVotingTypeForAgainst
                fields = ("author", "author_delegate", "proposal", "vote", "score")

        return OutputSerializerTypeForAgainst

    def delegate_vote_input_serializer_class(self) -> type[serializers.Serializer]:
        return self.vote_input_serializer_class()

    def update_vote(self, *, group_user, data: dict) -> None:
        from flowback.poll.models import (
            PollProposalTypeSchedule,
            PollVoting,
            PollVotingTypeForAgainst,
        )

        poll = self.poll

        if not data["proposals"]:
            PollVoting.objects.filter(created_by=group_user, poll=poll).delete()
            return

        if len(set(data["proposals"])) != len(data["proposals"]):
            raise ValidationError("Duplicate proposals are not allowed")

        proposals = poll.pollproposal_set.filter(id__in=data["proposals"]).all()
        if len(proposals) != len(data["proposals"]):
            raise ValidationError("Not all proposals are available to vote for")

        poll_vote, _ = PollVoting.objects.get_or_create(
            created_by=group_user, poll=poll
        )
        rows = [
            PollVotingTypeForAgainst(author=poll_vote, proposal_id=proposal, vote=True)
            for proposal in data["proposals"]
        ]

        old_proposal_ids = list(
            PollVotingTypeForAgainst.objects.filter(author=poll_vote).values_list(
                "proposal_id", flat=True
            )
        )

        PollVotingTypeForAgainst.objects.filter(author=poll_vote).delete()
        PollVotingTypeForAgainst.objects.bulk_create(rows)

        PollProposalTypeSchedule.objects.filter(
            proposal_id__in=old_proposal_ids
        ).update(preliminary_score=F("preliminary_score") - 1)
        PollProposalTypeSchedule.objects.filter(
            proposal_id__in=data["proposals"]
        ).update(preliminary_score=F("preliminary_score") + 1)

    def update_delegate_vote(self, *, delegate_pool, data: dict) -> None:
        from flowback.poll.models import PollDelegateVoting, PollVotingTypeForAgainst

        poll = self.poll

        if not data["proposals"]:
            PollDelegateVoting.objects.filter(
                created_by=delegate_pool, poll=poll
            ).delete()
            return

        proposals = poll.pollproposal_set.filter(id__in=data["proposals"]).all()
        if len(proposals) != len(data["proposals"]):
            raise ValidationError("Not all proposals are available to vote for")

        poll_vote, _ = PollDelegateVoting.objects.get_or_create(
            created_by=delegate_pool, poll=poll
        )
        rows = [
            PollVotingTypeForAgainst(
                author_delegate=poll_vote, proposal_id=proposal, vote=True
            )
            for proposal in data["proposals"]
        ]
        PollVotingTypeForAgainst.objects.filter(author_delegate=poll_vote).delete()
        PollVotingTypeForAgainst.objects.bulk_create(rows)

    def update_vote_scores(self, *, delegate_mandate_subquery) -> None:
        from flowback.poll.models import PollProposal, PollVotingTypeForAgainst
        from flowback.group.selectors.permission import permission_q

        poll = self.poll
        PollVotingTypeForAgainst.objects.filter(
            permission_q("author__created_by", "allow_vote"),
            proposal__active=True,
            author__poll=poll,
        ).update(score=Case(When(vote=True, then=1), default=-1))

        PollVotingTypeForAgainst.objects.filter(
            author_delegate__poll=poll,
            proposal__active=True,
        ).update(
            score=Case(When(vote=True, then=1), default=-1)
            * Subquery(delegate_mandate_subquery)
        )

        proposal_scores = (
            PollVotingTypeForAgainst.objects.filter(
                proposal=OuterRef("id"),
            )
            .values("proposal")
            .annotate(total_score=Sum("score"))
            .values("total_score")
        )

        PollProposal.objects.filter(poll=poll, active=True).update(
            score=Subquery(proposal_scores)
        )

    def on_poll_finalized(self, *, winning_proposal) -> None:
        poll = self.poll
        if poll.status != 1 or not winning_proposal:
            return
        schedule = (
            poll.created_by.group.schedule
            if poll.work_group is None
            else poll.work_group.schedule
        )
        schedule.create_event(
            title=poll.title,
            description=poll.description,
            meeting_link=poll.schedule_poll_meeting_link,
            start_date=winning_proposal.pollproposaltypeschedule.event_start_date,
            end_date=winning_proposal.pollproposaltypeschedule.event_end_date,
            created_by=poll,
        )
