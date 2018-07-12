# -*- coding: utf-8 -*-

import re

from utils import *


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
        yield SimpleVoter(name, weight)


_head_rx = re.compile(r'\s*#\s*(?P<title>.+)$')
_group_rx = re.compile(r'\s*##\s*(?P<group>.+?)$')
_voting_rx = re.compile(r'\s*###\s*(?P<voting>.+?)$')
_schulze_option_rx = re.compile(r'\s*[*]\s+(?P<option>.+?)$')
_median_option_rx = re.compile(r'\s*[-]\s+(?P<euro>\d+)(?:[.,](?P<cent>\d{1,2}))?\s*(?P<concurrency>[€$£])?$')


def _parse_concurrency_value(match):
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
        line = line.sptrip()
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
            state, last_voting_name = _handle_schulze_option_state(res, last_voting_name, line, line_num)
        else:
            raise ParseException('Internal error: Invalid state while parsing voting collection')


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
        parse_res = _parse_concurrency_value(m)
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
        state = last_voting_name, _schulze_option_state
    else:
        # now it must be a group or a new voting
        try:
            return _handle_group_or_voting_state(res, last_voting_name, line, line_num)
        except ParseException as e:
            raise ParseException('Invalid syntax in line %d: Must be a Schulze option, group or new voting' % line_num)
    return last_voting_name, state
