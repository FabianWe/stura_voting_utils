class SimpleVoter(object):
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight


class VotingGroup(object):
    def __init__(self, name, median_votings, schulze_votings):
        self.name = name
        self.median_votings = median_votings
        self.schulze_votings = schulze_votings


class VotingCollection(object):
    def __init__(self, name, date, groups):
        self.name = name
        self.date = date
        self.groups = groups


class MedianVotingSkeleton(object):
    def __init__(self, name, value, concurrency):
        self.name = name
        self.value = value
        self.concurrency = concurrency


class SchulzeVotingSkeleton(object):
    def __init__(self, name, options):
        self.name = name
        self.options = options
