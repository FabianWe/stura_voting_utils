# -*- coding: utf-8 -*-

import re
import csv

from utils import *
from schulze_voting import SchulzeVote
from median_voting import MedianVote


class ParseException(Exception):
    pass

_voter_rx = re.compile(r'\s*[*]\s+(?P<name>.+?):\s*(?P<weight>\d+)$')


def parse_voters(reader):
    for line_num, line in enumerate(reader, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = _voter_rx.match(line)
        if not m:
            raise ParseException('Invalid syntax in line %d, must be of form "* voter: weight"' % line_num)
        name, weight = m.group('name'), m.group('weight')
        # should not happen, just to be sure
        try:
            weight = int(weight)
        except ValueError as e:
            raise ParseException('Invalid enry in line %d: %s, line must be of form "voter: weight"' % (line_num, str(e)))
        yield WeightedVoter(name, weight)


_head_rx = re.compile(r'\s*#\s+(?P<title>.+)$')
_group_rx = re.compile(r'\s*##\s+(?P<group>.+?)$')
_voting_rx = re.compile(r'\s*###\s+(?P<voting>.+?)$')
_schulze_option_rx = re.compile(r'\s*[*]\s+(?P<option>.+?)$')
_median_option_rx = re.compile(r'\s*[-]\s+(?P<euro>\d+)(?:[.,](?P<cent>\d{1,2}))?\s*(?P<concurrency>[€$£])?$')


def parse_concurrency_value(match):
    if not match:
        return None
    # maybe the try is not necessary because it should always be parsable as int, but just to be sure
    try:
        value = int(match.group('euro')) * 100
        cent = match.group('cent')
        if cent is not None:
            if len(cent) == 1:
                value += (int(cent) * 10)
            elif len(cent) == 2:
                value += int(cent)
            else:
                assert False
        return value, match.group('concurrency')
    except ValueError as e:
        return None


_head_state = 'start'
_group_state = 'group'
_voting_state = 'voting'
_option_state = 'option'
_group_or_voting_state = 'group-or-voting'
_schulze_option_state = 'schulze-option'


def _match_first(s, *args):
    for i, rx in enumerate(args):
        m = rx.match(s)
        if m:
            return i, m
    return -1, None


def parse_voting_collection(reader):
    res = VotingCollection('', None, [])
    state = _head_state
    last_voting_name = None
    for line_num, line in enumerate(reader, 1):
        line = line.strip()
        if not line:
            continue
        if state == _head_state:
            m = _head_rx.match(line)
            if not m:
                raise ParseException('Invalid head line in line %d, must be "# <TITLE>"' % line_num)
            res.name = m.group('title')
            state = _group_state
        elif state == _group_state:
            state = _handle_group_state(res, line, line_num)
        elif state == _voting_state:
            # parse a voting name
            last_voting_name, state = _handle_voting_state(res, line, line_num)
        elif state == _option_state:
            state = _handle_option_state(res, last_voting_name, line, line_num)
        elif state == _group_or_voting_state:
            last_voting_name, state = _handle_group_or_voting_state(res, last_voting_name, line, line_num)
        elif state == _schulze_option_state:
            last_voting_name, state = _handle_schulze_option_state(res, last_voting_name, line, line_num)
        else:
            raise ParseException('Internal error: Invalid state while parsing voting collection: %s' % str(state))
    return res


def _handle_group_state(res, line, line_num):
    # parse a new group name
    m = _group_rx.match(line)
    if not m:
        raise ParseException('Invalid group in line %d, must be "## <GROUP>"' % line_num)
    # create new group
    group = VotingGroup(m.group('group'), [], [])
    # append group to result
    res.groups.append(group)
    return _voting_state


def _handle_voting_state(res, line, line_num):
    # parse a voting name
    m = _voting_rx.match(line)
    if not m:
        raise ParseException('Invalid voting in line %d, must be "### <VOTING>"' % line_num)
    last_voting_name = m.group('voting')
    state = _option_state
    return last_voting_name, state


def _handle_option_state(res, last_voting_name, line, line_num):
    if not res.groups or last_voting_name == "" or last_voting_name is None:
        # should not happen, just to be sure
        raise ParseException('Internal error: Illegal state while parsing voting options in line %d' % line_num)
    last_group = res.groups[-1]
    # parse either a median or schulze option
    # there must be an option now
    id, m = _match_first(line, _schulze_option_rx, _median_option_rx)
    if id < 0:
        raise ParseException('Invalid voting option in line %d, must be a Median or Schulze option' % line_num)
    elif id == 0:
        # we parsed a schulze option
        # create a new schulze voting (this is the first time we parsed an option)
        option = m.group('option')
        schulze_skel = SchulzeVotingSkeleton(last_voting_name, [option, ])
        last_group.schulze_votings.append(schulze_skel)
        # now parse more schulze options or new group / voting
        state = _schulze_option_state
    elif id == 1:
        # we parsed the value of a median voting, transform to int
        parse_res = parse_concurrency_value(m)
        if not parse_res:
            # should never happen
            raise ParseException('Internal error: Unable to parse value for median voting in line %d' % line_num)
        val, concurrency = parse_res
        median_skel = MedianVotingSkeleton(last_voting_name, val, concurrency)
        last_group.median_votings.append(median_skel)
        # now we must parse a group or a voting
        state = _group_or_voting_state
    else:
        assert False
    return state


def _handle_group_or_voting_state(res, last_voting_name, line, line_num):
    # first try to handle as group
    try:
        return last_voting_name, _handle_group_state(res, line, line_num)
    except ParseException as e:
        pass
    try:
        return _handle_voting_state(res, line, line_num)
    except ParseException as e:
        raise ParseException('Invalid syntax in line %d: Must be either a group or a voting' % line_num)


def _handle_schulze_option_state(res, last_voting_name, line, line_num):
    # now we must parse either a new schulze option or an new group or voting
    m = _schulze_option_rx.match(line)
    if m:
        # code duplication but ok
        if not res.groups:
            # should not happen
            raise ParseException('Internal error: Invalid syntax in line %d: No group given.' % line_num)
        last_group = res.groups[-1]
        skel = last_group.schulze_votings[-1]
        skel.options.append(m.group('option'))
        # state does not change
        state = _schulze_option_state
        return last_voting_name, state
    else:
        # now it must be a group or a new voting
        try:
            return _handle_group_or_voting_state(res, last_voting_name, line, line_num)
        except ParseException as e:
            raise ParseException('Invalid syntax in line %d: Must be a Schulze option, group or new voting' % line_num)


_csv_median_head_rx = re.compile(r'[Mm]edian\s*\((?P<value>\d+)\)\s*$')
_csv_schulze_head_rx = re.compile(r'[Ss]chulze\s*\((?P<num>\d+)\)')


def _parse_csv_head(head_row):
    if len(head_row) < 2:
        raise ParseException('csv head must contain at least two columns')
    group = VotingGroup('Votings', [], [])
    res = VotingCollection('', None, [group,])
    for col_num, col in enumerate(head_row[2:]):
        col = col.strip()
        i, m = _match_first(col, _csv_median_head_rx, _csv_schulze_head_rx)
        if i < 0:
            raise ParseException('Invalid column %d: Expected Schulze or Median definition' % col_num)
        elif i == 0:
            try:
                value = int(m.group('value'))
                voting = MedianVotingSkeleton('Voting %d' % (col_num + 1), value, None, col_num)
                group.median_votings.append(voting)
            except ValueError as e:
                raise ParseException('Invalid entry in column %d: %s, column must be of form "Median(<VALUE>)"' % (col_num, str(e)))
        elif i == 1:
            num = int(m.group('num'))
            voting = SchulzeVotingSkeleton('Voting %d' % (col_num + 1), ['Option %d' % (i + 1) for i in range(num)], col_num)
            group.schulze_votings.append(voting)
        else:
            assert False
    return res


def _parse_csv_body(collection, rows):
    # ugly but ok
    all_votings = sorted(collection.groups[0].median_votings + collection.groups[0].schulze_votings,
                         key=lambda v: v.id)
    num_votings = len(all_votings)
    # stores all votes
    votes = [[] for _ in all_votings]
    for row_num, row in enumerate(rows, 2):
        if num_votings != (len(row) - 2):
            raise ParseException('Invalid syntax in row %d: Not enough votings' % row)
        # parse weight, we ignore the name
        try:
            weight = int(row[1])
        except ValueError as e:
            raise ParseException("Can't parse weight as int: %s" % str(e))
        # everything okay, now we can parse all votings
        for i, (skel, entry) in enumerate(zip(all_votings, row[2:])):
            if not entry:
                continue
            if isinstance(skel, SchulzeVotingSkeleton):
                try:
                    options = [int(as_str) for as_str in entry.split('/')]
                    if len(options) != len(skel.options):
                        raise ParseException('Invalid options in row %d: Must contain exactly as many options as defined in voting' % row_num)
                    v = SchulzeVote(options, weight)
                    votes[i].append(v)
                except ValueError as option_err:
                    raise ParseException("Can't parse options for Schulze voting: %s" % str(option_err))
            elif isinstance(skel, MedianVotingSkeleton):
                try:
                    value = int(entry)
                except ValueError as median_err:
                    raise ParseException('Invalid value for median voting: %s' % str(median_err))
                v = MedianVote(value, weight)
                votes[i].append(v)
            else:
                assert False
    return all_votings, votes


def parse_csv(reader, delimiter=','):
    csv_reader = csv.reader(reader, delimiter=delimiter)
    try:
        head = next(csv_reader)
    except StopIteration:
        raise ParseException('No header found in csv file')
    votings = _parse_csv_head(head)
    return _parse_csv_body(votings, csv_reader)


