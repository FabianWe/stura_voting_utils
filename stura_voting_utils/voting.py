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

import sys
import argparse

from .parser import *

from schulze_voting import evaluate_schulze
from median_voting import MedianStatistics

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Command line tool for evaluating Schulze and Median votings',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '--file',
        '-f',
        help='Path to the csv file',
        required=True)

    parser.add_argument(
        '--delimiter',
        help='The csv file delimiter, default is ","',
        required=False,
        default=',')

    args = parser.parse_args()

    with open(args.file, 'r') as f:
        try:
            all_votings, votes = parse_csv(f, args.delimiter)
        except ParseException as e:
            print('Error while parsing csv file:')
            print(e)
            sys.exit(1)

    print('Evaluating votings...')
    print()
    for i, skel in enumerate(all_votings, 1):
        print('Voting %d ' % i, end='')
        if isinstance(skel, SchulzeVotingSkeleton):
            print('Schulze voting with %d options' % len(skel.options))
            print('The ranking groups are as follows:')
            s_res = evaluate_schulze(votes[i - 1], len(skel.options))
            eq_list = [' = '.join(str(i) for i in l) for l in s_res.candidate_wins]
            out = ' > '.join(eq_list)
            print(out)
        elif isinstance(skel, MedianVotingSkeleton):
            print('Median voting with value %d' % skel.value)
            stat = MedianStatistics(votes[i - 1])
            agreed_value = stat.median()
            if agreed_value is None:
                print('No value agreed upon')
            else:
                print('Agreed on value', agreed_value)
        else:
            assert False
        print()
    print(
        'Note that the capabilities of this tool are very limited, it is rather a demonstration of the voting packages')
