#!/usr/bin/env python3

import unittest

if __name__ == '__main__':
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
