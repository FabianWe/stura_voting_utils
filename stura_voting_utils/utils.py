# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018 Fabian Wenzelmann
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def output_concurrency(val, concurrency=None, delim=','):
    if concurrency is None:
        concurrency = ''
    else:
        concurrency = ' ' + concurrency
    if val < 0:
        assert False
    elif val < 10:
        return '0%s0%d%s' % (delim, val, concurrency)
    elif val < 100:
        return '0%s%d%s' % (delim, val, concurrency)
    else:
        euro = val // 100
        cent = val % 100
        return '%d%s%d%s' % (euro, delim, cent, concurrency)


class WeightedVoter(object):
    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

    def output(self):
        return '* %s: %d' % (self.name, self.weight)


class VotingCollection(object):
    def __init__(self, name, date, groups):

        self.name = name
        self.date = date
        self.groups = groups

    def output(self):
        groups_str = '\n\n'.join( group.output() for group in self.groups )
        if self.date is None:
            return '# %s\n\n%s' % (self.name, groups_str)
        else:
            return '# %s\n\n%s' % (self.name,
                                   groups_str)


class VotingGroup(object):
    def __init__(self, name, median_votings, schulze_votings):
        self.name = name
        self.median_votings = median_votings
        self.schulze_votings = schulze_votings

    def output(self):
        return '## %s\n\n%s\n%s' % (self.name,
                                 '\n\n'.join( median.output() for median in self.median_votings ),
                                 '\n\n'.join( schulze.output() for schulze in self.schulze_votings ))



class MedianVotingSkeleton(object):
    def __init__(self, name, value, concurrency, id=None):
        self.name = name
        self.value = value
        self.concurrency = concurrency
        self.id = id

    def output(self):
        return '### %s\n- %s' % (self.name, output_concurrency(self.value, self.concurrency))


class SchulzeVotingSkeleton(object):
    def __init__(self, name, options, id=None):
        self.name = name
        self.options = options
        self.id = id

    def output(self):
        return '### %s\n%s' % (self.name, '\n'.join( '* %s' % option for option in self.options ))
