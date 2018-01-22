import os
from chirptext.cli import setup_logging

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')

setup_logging(os.path.join(TEST_DIR, 'logging.json'), os.path.join(TEST_DIR, 'logs'))
