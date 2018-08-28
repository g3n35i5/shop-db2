#!/usr/bin/env python3

import argparse
import sys
import os
import unittest


if __name__ == '__main__':

    list_files = os.listdir('tests')
    list_tests = []

    for file in list_files:
        try:
            file.index('test')
        except ValueError:
            continue
        else:
            list_tests.append(file)

    print('Please select the tests you want to run. [Default=all]')
    print('all: All tests')
    for i, test in enumerate(list_tests):
        print('{:3d}: {}'.format(i, test))
    answ = input('Testnumbers: ')

    if answ in ['', 'all', 'a']:
        tests = unittest.TestLoader().discover('tests')
        unittest.TextTestRunner(verbosity=2).run(tests)
    else:  # pragma: no cover
        list_testnumbers = answ.split(' ')
        test = []

        for i, testnumber in enumerate(list_testnumbers):
            try:
                testnumber = int(testnumber)

            except ValueError:
                sys.exit('Invalid input')

            if testnumber not in range(0, len(list_tests)):
                sys.exit('Invalid input')

            test.append((unittest.TestLoader()
                         .discover('tests', pattern=list_tests[testnumber])))

        testcombo = unittest.TestSuite(test)
        unittest.TextTestRunner(verbosity=2).run(testcombo)
