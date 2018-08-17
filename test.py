#!/usr/bin/env python3

import argparse
import sys
import unittest

###Usage:   -to run all test "./test.py"
###         -to run specific files "./test.py --file [files with path]"
###Example: "./test.py --file tests/base.py tests/base_api.py"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Application to run unittest, default runs all")
    parser.add_argument('--file', nargs='+', help="Single files to test")
    args = parser.parse_args()
    if args.file:
        print(args.file)
        list_files = args.file
        test = []
        for i in range(0, len(list_files)):
            list_files[i] = list_files[i].strip("tests/")
            test += unittest.TestLoader().discover("tests", pattern=list_files[i])
        testcombo = unittest.TestSuite(test)
        unittest.TextTestRunner(verbosity=2).run(testcombo)

    else:
        tests = unittest.TestLoader().discover('tests')
        unittest.TextTestRunner(verbosity=2).run(tests)
