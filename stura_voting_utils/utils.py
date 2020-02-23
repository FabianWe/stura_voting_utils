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


def output_currency(val, currency=None, delim=','):
    """Format a value in cents in a currency.

    The value is always formatted s.t. it contains exactly two decimal places.

    Args:
        val (int): The value to format.
        currency: The currency as a string, for example '€' or None if no currency should be used.
        delim: The delimiter to separate the number before the decimal point (default is ',', the German default)

    Returns:
        str: The formatted number with the delimiter. The value is considered to be in cents, for example 1000 for
        10.00€.

    Examples:
        >>> output_currency(9)
        '0,09'

        >>> output_currency(42, currency='$', delim='.')
        '0.42 $'

        >>> output_currency(100, '€')
        '1,00 €'

        >>> output_currency(4284)
        '42,84'
    """
    if currency is None:
        currency = ''
    else:
        currency = ' ' + currency
    if val < 0:
        return '-' + output_currency(-val, currency, delim)
    elif val < 10:
        return '0%s0%d%s' % (delim, val, currency)
    elif val < 100:
        return '0%s%d%s' % (delim, val, currency)
    else:
        euro = val // 100
        cent = val % 100
        if cent < 10:
            return '%d%s0%d%s' % (euro, delim, cent, currency)
        else:
            return '%d%s%d%s' % (euro, delim, cent, currency)


class WeightedVoter(object):
    """Class for a voter with a name and weight.

    Attributes:
        name (str): Name of the voter.
        weight (int): Weight of the voter in votings.
    """

    def __init__(self, name, weight):
        self.name = name
        self.weight = weight

    def output(self):
        """Return the voter in the Markdown-like format.

        Returns:
            str: The voter in the format '* <NAME>: <WEIGHT>'
        """
        return '* %s: %d' % (self.name, self.weight)


class VotingCollection(object):
    """A class for representing a collection of groups (the groups contain the actual votes).

    Attributes:
        name (str): The name of the collection, for example 'Votings on day XXX'.
        date (datetime.datetime): The date when the voting takes place, can be None.
        groups (list of VotingGroup): All groups of the collection.
    """

    def __init__(self, name, date, groups):
        self.name = name
        self.date = date
        self.groups = groups

    def output(self):
        """Return the collection in the Markdown-like format.

        Note that the date is ignored even if it is not None, the format does not support dates and times.

        Returns:
            str: The representation of the collection in the Markdown-like format.
        """
        groups_str = '\n\n'.join(group.output() for group in self.groups)
        return '# %s\n\n%s' % (self.name, groups_str)


class VotingGroup(object):
    """A group consists of different median and schulze votings.

    Attributes:
        name (str): The name of the group, e.g. 'Financial Votings'.
        median_votings (list of MedianVotingSkeleton): All median votings in the group.
        schulze_votings (list of SchulzeVotingSkeleton) Alle Schulze votings in the group.
    """

    def __init__(self, name, median_votings, schulze_votings):
        self.name = name
        self.median_votings = median_votings
        self.schulze_votings = schulze_votings

    def get_votings(self):
        """Get all votings (median and Schulze) sorted according to their id.

        Returns:
            list of MedianVotingSkeleton and SchulzeVotingSkeleton: All votings sorted according to their id.
        """
        return sorted(self.median_votings + self.schulze_votings,
                      key=lambda v: v.id if v.id is not None else 0)

    def __len__(self):
        """Return the number of votings in the group.

        Returns: Number of votings in the group (median and Schulze).

        """
        return len(self.median_votings) + len(self.schulze_votings)

    def output(self):
        """Return the group in the Markdown-like format.

        Returns:
            str: The representation of the group in the Markdown-like format.
        """
        all_votings = self.get_votings()
        return '## %s\n\n%s' % (self.name,
                                '\n\n'.join(voting.output() for voting in all_votings))


class MedianVotingSkeleton(object):
    """A median voting skeleton (contains no votes, just defines the basic structure).

    A median skeleton defines the basic components of the voting. It contains the name of the voting, the value
    voted for (in cents, so 100.00€ should be stored as 10000) and the currency used (can be None). It also has an
    id field that is used for sorting in the voting groups (when median and Schulze votings are combined).

    Attributes:
        name (str): Name of the voting.
        value (int): The max value of the voting.
        currency (str): The currency used in the voting.
        id (int): An internal id that is used for sorting skeletons.

    """

    def __init__(self, name, value, currency, id=None):
        self.name = name
        self.value = value
        self.currency = currency
        self.id = id

    def output(self):
        """Return the voting in the Markdown-like format.

        Returns:
            str: The representation of the voting in the Markdown-like format.
        """
        return '### %s\n- %s' % (self.name, output_currency(self.value, self.currency))


class SchulzeVotingSkeleton(object):
    """A Schulze voting skeleton (contains no votes, just defines the basic structure).

    The skeleton defines the name of the voting and all valid options. It also has an id field that is used for sorting
    in the voting groups (when median and Schulze votings are combined).

    Attributes:
        name (str): Name of the voting.
        options (list of str): All possible options of the voting.
        id (int): An internal id that is used for sorting skeletons.
    """

    def __init__(self, name, options, id=None):
        self.name = name
        self.options = options
        self.id = id

    def output(self):
        """Return the voting in the Markdown-like format.

        Returns:
            str: The representation of the voting in the Markdown-like format.
        """
        return '### %s\n%s' % (self.name, '\n'.join('* %s' % option for option in self.options))
