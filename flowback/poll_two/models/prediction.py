# Cast predictions on polls
from flowback.prediction.models import (PredictionStatement,
                                        PredictionStatementSegment,
                                        PredictionStatementVote,
                                        PredictionBet)


class PollPredictionStatement(PredictionStatement):
    pass


# Select multiple proposals for specific segment
class PollPredictionStatementSegment(PredictionStatementSegment):
    pass


class PollPredictionStatementVote(PredictionStatementVote):
    pass


class PollPredictionBet(PredictionBet):
    pass
