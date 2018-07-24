# -*- coding: utf-8 -*-

import sys
import argparse

from parser import *

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
            s_res = evaluate_schulze(votes[i-1], len(skel.options))
            eq_list = [' = '.join(str(i) for i in l) for l in s_res.candidate_wins]
            out = ' > '.join(eq_list)
            print(out)
        elif isinstance(skel, MedianVotingSkeleton):
            print('Median voting with value %d' % skel.value)
            stat = MedianStatistics(votes[i-1])
            agreed_value = stat.median()
            if agreed_value is None:
                print('No value agreed upon')
            else:
                print('Agreed on value', agreed_value)
        else:
            assert False
        print()
    print('Note that the capabilities of this tool are very limited, it is rather a demonstration of the voting packages')