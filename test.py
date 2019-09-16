#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from argparse import ArgumentParser
import sys
import os
import unittest


def do_all_tests():
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':

    parser = ArgumentParser(description='Running unittests for shop.db.')
    parser.add_argument('--mode', help='Select the operating mode.',
                        default='interactive',
                        choices=['interactive', 'auto'])

    args = parser.parse_args()

    if args.mode == 'interactive':  # pragma: no cover
        list_files = os.listdir('tests')
        list_tests = []

        for file in list_files:
            try:
                file.index('test')
            except ValueError:
                continue
            else:
                list_tests.append(file)
        list_tests = sorted(list_tests)

        print('Please select the tests you want to run. [Default=all]')
        print('all: All tests')
        for i, test in enumerate(list_tests):
            print('{:3d}: {}'.format(i, test))
        answ = input('Testnumbers: ')

        if answ in ['', 'all', 'a']:
            do_all_tests()
        else:
            list_testnumbers = answ.split(' ')
            test = []

            for i, testnumber in enumerate(list_testnumbers):
                try:
                    testnumber = int(testnumber)

                except ValueError:
                    sys.exit('Invalid input')

                if testnumber not in range(0, len(list_tests)):
                    sys.exit('Invalid input')

                test.append(unittest.TestLoader()
                            .discover('tests', pattern=list_tests[testnumber]))

            testcombo = unittest.TestSuite(test)
            unittest.TextTestRunner(verbosity=2).run(testcombo)
    elif args.mode == 'auto':
        do_all_tests()

    else:  # pragma: no cover
        sys.exit(f'Invalid operating mode: {args.mode}')
