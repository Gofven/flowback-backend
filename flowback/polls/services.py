import json
import math
import hashlib
from itertools import groupby

from django.core.files.base import ContentFile
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404
from rest_framework import serializers
import datetime

from flowback.polls.helper import PollAdapter
from flowback.polls.models import Poll, PollProposal, PollUserDelegate
from flowback.users.models import GroupMembers
from flowback.users.selectors import get_group_member


def create_poll_receipt(
        *,
        poll: int
):
    poll = get_object_or_404(Poll, id=poll)
    adapter = PollAdapter(poll)

    class VoteSerializer(serializers.ModelSerializer):
        score = serializers.FloatField(source='priority')

        class Meta:
            model = adapter.index
            fields = ('hash', 'score', 'is_positive')

    class ProposalSerializer(serializers.ModelSerializer):
        votes = serializers.SerializerMethodField()

        class Meta:
            model = PollProposal
            fields = (
                'id', 'proposal', 'final_score_positive',
                'final_score_negative', 'created_at', 'votes'
            )

        def get_votes(self, obj):
            data = adapter.index.objects.filter(proposal=obj).all()
            result = []

            for vote in data:

                # Count vote multiplier (slow, but manageable)
                group = obj.poll.group
                multiplier = 1 if get_group_member(user=vote.user_id, group=group.id).allow_vote else 0
                if group.delegators.filter(pk=vote.user_id).exists():
                    for user_delegate in PollUserDelegate.objects.filter(delegator=vote.user, group=group).all():
                        if get_group_member(user=user_delegate.user.pk, group=group.pk).allow_vote:
                            multiplier += 1

                if multiplier:
                    result += [dict(
                        hash=vote.hash if x < 1 else None,
                        priority=vote.priority / multiplier,
                        is_positive=vote.is_positive,
                        created_at=vote.created_at
                    ) for x in range(multiplier)]

            return VoteSerializer(result, many=True).data

    class PollSerializer(serializers.ModelSerializer):
        proposals = serializers.SerializerMethodField()

        class Meta:
            model = Poll
            fields = (
                'id', 'title', 'description', 'total_participants',
                'success', 'top_proposal', 'created_at', 'proposals'
            )

        def get_proposals(self, obj):
            data = PollProposal.objects.filter(poll=obj).all()
            return ProposalSerializer(data, many=True).data

    return PollSerializer(poll).data


def check_poll(poll: Poll):
    adapter = PollAdapter(poll)

    # Counting Proposal Votes
    if poll.end_time <= datetime.datetime.now() and not poll.votes_counted:
        counter_proposals = adapter.proposal.objects.filter(poll=poll).all()
        total_participants = len(GroupMembers.objects.filter(group=poll.group, allow_vote=True))
        indexes = adapter.index.objects.filter(proposal__poll=poll)

        # Positive, Negative
        counter = {key.id: [0, 0] for key in counter_proposals}

        user_indexes = [list(g) for k, g in groupby(sorted(indexes, key=lambda x: x.user_id), lambda x: x.user_id)]
        for user_index in user_indexes:
            group = poll.group
            user = user_index[0].user
            multiplier = 1 if get_group_member(user=user.pk, group=group.pk).allow_vote else 0

            # Check if user is delegate
            if group.delegators.filter(pk=user.pk).exists():
                votes = adapter.index.objects.filter(user=user).all()

                for user_delegate in PollUserDelegate.objects.filter(delegator=user, group=group).all():
                    if get_group_member(user=user_delegate.user.pk, group=group.pk).allow_vote:
                        for vote in votes:
                            vote.hash = None
                            vote.user = user_delegate.user
                            vote.save()

            # Count votes
            if poll.voting_type == poll.VotingType.CONDORCET:
                positive = sorted([x for x in user_index if x.is_positive], key=lambda x: x.priority)
                # negative = sorted([x for x in user_index if not x.is_positive], key=lambda x: x.priority)

                for sub, index in enumerate(positive):
                    counter[index.proposal_id][0] += (len(counter_proposals) - sub) * multiplier

                # for sub, index in enumerate(negative):
                #    counter[index.proposal_id] += (sub - len(counter_proposals)) * multiplier

            elif poll.voting_type == poll.VotingType.TRAFFIC:
                positive = [x for x in user_index if x.is_positive]
                negative = [x for x in user_index if not x.is_positive]

                for index in positive:
                    counter[index.proposal_id][0] += multiplier

                for index in negative:
                    counter[index.proposal_id][1] += multiplier

            elif poll.voting_type == poll.VotingType.CARDINAL:
                total_score = sum([x.priority for x in user_index])

                if total_score > 0:
                    for vote in user_index:
                        vote.priority = multiplier * (vote.priority / total_score)
                        vote.save()
                        counter[vote.proposal_id][0] += vote.priority

        # Insert counter to proposals
        for key, counter_proposal in enumerate(counter_proposals):
            counter_proposals[key].final_score_positive = counter[counter_proposal.id][0]
            counter_proposals[key].final_score_negative = counter[counter_proposal.id][1]

        # Apply
        adapter.proposal.objects.bulk_update(
            counter_proposals,
            ['final_score_positive', 'final_score_negative']
        )

        top = counter_proposals.annotate(
            final_score=Sum(F('final_score_positive') - F('final_score_negative'))
        ).order_by('-final_score').first()
        print(top.final_score_positive, top.final_score_negative)
        success = bool(top
                       and top.final_score_positive != 0.0
                       and top.final_score_positive != 0.0
                       and top.type != adapter.proposal.Type.DROP)

        result_file = json.dumps(create_poll_receipt(poll=poll.id), indent=4)
        result_hash = hashlib.sha512(result_file.encode('utf-8')).hexdigest()

        poll.result_file.save('result.json', ContentFile(result_file))

        Poll.objects.filter(id=poll.id).update(
            votes_counted=True,
            success=success,
            top_proposal=top.id if top else None,
            total_participants=total_participants,
            result_hash=result_hash
        )
        return True

    return False
