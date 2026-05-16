from abc import ABC, abstractmethod


class Phase(ABC):
    pass


class PollType(ABC):
    phases: list[Phase]

    @abstractmethod
    def proposal_posting():
        ...


class ForAgainst(PollType):
    pass


# Borrows from For Against alot
class Schedule(PollType):
    pass


# Cardinal is renamed to Score
class Score(PollType):
    pass
