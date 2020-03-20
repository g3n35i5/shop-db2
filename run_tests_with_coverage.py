#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import os
import shutil
import unittest
from argparse import ArgumentParser
from http.server import HTTPServer, CGIHTTPRequestHandler
import webbrowser
import threading
import time
import sys
import configuration as config

try:
    import coverage
except ImportError:
    raise ImportError("Please install the coverage module (https://pypi.python.org/pypi/coverage/)")


class SilentHTTPHandler(CGIHTTPRequestHandler):
    """
    Custom HTTP handler which suppresses the console output.
    """
    def log_message(self, format, *args):
        return


def start_server(path, port=8000) -> None:
    """
    Start a simple webserver serving path on port

    :param path: Root path for the webserver
    :param port: Port for the webserver
    :return:     None
    """
    os.chdir(path)
    httpd = HTTPServer(("", port), SilentHTTPHandler)
    httpd.serve_forever()


def main(args) -> None:
    # Load .coveragerc.ini configuration file
    config_file = os.path.join(config.PATH, ".coveragerc.ini")
    os.environ["COVERAGE_PROCESS_START"] = config_file
    cov = coverage.coverage(config_file=config_file)

    # Start coverage
    cov.start()
    html_cov_path = os.path.join(config.PATH, "htmlcov")
    webserver_port = 8000
    try:
        tests = unittest.TestLoader().discover(os.path.join(config.PATH, "tests"))
        unittest.TextTestRunner(verbosity=2).run(tests)
    finally:
        cov.stop()
        cov.save()
        cov.combine()
    if os.path.exists(html_cov_path):
        shutil.rmtree(html_cov_path)
    cov.html_report(directory=html_cov_path)
    cov.xml_report()

    if args.show_results is False:
        return

    # Start webserver
    daemon = threading.Thread(name="Coverage Server", target=start_server, args=(html_cov_path, webserver_port))
    daemon.setDaemon(True)
    daemon.start()

    # Open page in browser
    webbrowser.open("http://localhost:{}".format(webserver_port))

    # Keep the script alive as long it
    print("Webserver is running on port {}. Press CTRL+C to exit".format(webserver_port))
    while True:
        try:
            time.sleep(.1)
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    parser = ArgumentParser(description='Running unittests for shop-db2 with coverage')
    parser.add_argument('--show-results', help='Open results in web browser', action='store_true')
    args = parser.parse_args()
    main(args)
