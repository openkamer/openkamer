#!/usr/bin/env python3

import codecs
import os
import random
import shutil
import string
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

LOCAL_SETTINGS_PATH = os.path.join(BASE_DIR, './website/local_settings.py')
LOCAL_SETTINGS_EXAMPLE_PATH = os.path.join(BASE_DIR, './website/local_settings_example.py')


def main():
    if os.path.exists(LOCAL_SETTINGS_PATH):
        print('ERROR: ' + LOCAL_SETTINGS_PATH +
              ' already exists! Please remove this file manually if you intent to overwrite it.')
        return
    if not os.path.exists(LOCAL_SETTINGS_EXAMPLE_PATH):
        print('ERROR: ' + LOCAL_SETTINGS_EXAMPLE_PATH +
              ' could not be found! Please make sure this example settings file is readable at the given location.')
        return
    shutil.copyfile(LOCAL_SETTINGS_EXAMPLE_PATH, LOCAL_SETTINGS_PATH)
    secret_key_random = generate_random_secret_key()
    replace(LOCAL_SETTINGS_PATH, "SECRET_KEY = ''", "SECRET_KEY = '" + secret_key_random + "'")


def replace(source_file_path, pattern, substring):
    fh, target_file_path = tempfile.mkstemp()

    with codecs.open(target_file_path, 'w', 'utf-8') as target_file:
        with codecs.open(source_file_path, 'r', 'utf-8') as source_file:
            for line in source_file:
                target_file.write(line.replace(pattern, substring))
    os.remove(source_file_path)
    shutil.move(target_file_path, source_file_path)


def generate_random_secret_key():
    # source: https://gist.github.com/mattseymour/9205591
    # Get ascii Characters numbers and punctuation (minus quote characters as they could terminate string).
    chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')
    secret_key = ''.join([random.SystemRandom().choice(chars) for i in range(50)])
    return secret_key

if __name__ == "__main__":
    main()