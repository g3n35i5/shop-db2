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


    print('Please select the tests you want to run [Default=0] \n'
            '0: All tests')
    for i in range(0, len(list_tests)):
        print('{}: {}'.format(i+1, list_tests[i]))
    answ = input("Testnumbers: ")


    if answ == "" or answ == "0":
        tests = unittest.TestLoader().discover('tests')
        unittest.TextTestRunner(verbosity=2).run(tests)
    else:
        testnumbers = answ.split(" ")

        for i in range(0, len(testnumbers)):
            try:
                testnumbers[i] = int(testnumbers[i])-1
            except ValueError:
                print("Invalid input")
                sys.exit()
        if  -1 in testnumbers:
            print("Invalid input")
            sys.exit()

        test = []
        for i in testnumbers:
            if i > (len(list_tests)-1):
                print("Invalid input")
                sys.exit()
            test.append(unittest.TestLoader().discover("tests", pattern=list_tests[i]))
        testcombo = unittest.TestSuite(test)
        unittest.TextTestRunner(verbosity=2).run(testcombo)
