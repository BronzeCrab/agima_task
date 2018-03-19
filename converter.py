import logging
import os
from datetime import datetime
import argparse
import sys
import signal
import json
from shutil import copyfile
from collections import OrderedDict
import re
import platform
try:
    from daemonize import Daemonize
except ImportError:
    pass
from yattag import Doc

PID = "/tmp/converter.pid"
# logger's settings
log_file = "C:\\Users\\a.ustinnikov\\test\\agima_task\\converter.log"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.FileHandler(log_file, "a")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

INPUT_FILE_NAME = 'source.json'
FOLDER_TO_LOOK_IN = 'C:\\Users\\a.ustinnikov\\test\\agima_task\\converter'


def gen_html_from_source_data(source_data, tag, text):
    log(logger, source_data)
    if type(source_data) is list:
        with tag('ul'):
            for elem in source_data:
                with tag('li'):
                    gen_html_from_obj(elem, tag, text)

    elif type(source_data) is OrderedDict:
        gen_html_from_obj(source_data, tag, text)


def prepare_tag(tag_name):
    cleaned_tag_name, tag_id, tag_classes = tag_name, None, None
    id_regex = '#[-\w]+'
    m = re.search(id_regex, tag_name)
    if m:
        tag_id = m.group(0).replace('#', '')
        cleaned_tag_name = re.sub(id_regex, '', tag_name)
    classes_regex = '\.[-\w]+'
    m = re.findall(classes_regex, tag_name)
    if m:
        tag_classes = ''.join(m)
        tag_classes = re.sub(' ', '', re.sub('\.', ' ', tag_classes), count=1)
        cleaned_tag_name = re.sub(classes_regex, '', cleaned_tag_name)

    return cleaned_tag_name, tag_id, tag_classes


def switch_cases(
        func, func_params, tag, cleaned_tag_name, tag_id, tag_classes):
    if tag_id is None and tag_classes is None:
        with tag(cleaned_tag_name):
            func(*func_params)
    elif tag_id is not None and tag_classes is None:
        with tag(cleaned_tag_name, id=tag_id):
            func(*func_params)
    elif tag_id is None and tag_classes is not None:
        with tag(cleaned_tag_name, klass=tag_classes):
            func(*func_params)
    else:
        with tag(cleaned_tag_name, id=tag_id, klass=tag_classes):
            func(*func_params)


def gen_html_from_obj(obj, tag, text):
    if type(obj) is OrderedDict:
        for key in obj:
            cleaned_tag_name, tag_id, tag_classes = prepare_tag(key)
            if type(obj[key]) is list or type(obj[key]) is OrderedDict:
                switch_cases(
                    gen_html_from_source_data,
                    (obj[key], tag, text),
                    tag, cleaned_tag_name, tag_id, tag_classes)
            # obj[key] is simple text
            else:
                if cleaned_tag_name == 'body':
                    switch_cases(
                        text,
                        (obj[key],),
                        tag, 'p', tag_id, tag_classes)
                else:
                    switch_cases(
                        text,
                        (obj[key],),
                        tag, cleaned_tag_name, tag_id, tag_classes)
    elif type(obj) is str:
        cleaned_tag_name, tag_id, tag_classes = prepare_tag(obj)
        switch_cases(
            text,
            ('',),
            tag, cleaned_tag_name, tag_id, tag_classes)


def main():
    log(logger, 'start')
    if not os.path.exists(FOLDER_TO_LOOK_IN):
        os.makedirs(FOLDER_TO_LOOK_IN)
        log(logger, 'output directory created')
    while True:
        try:
            input_file_path = os.path.join(
                    FOLDER_TO_LOOK_IN, INPUT_FILE_NAME)
            if (os.path.isfile(input_file_path) and
                    os.stat(input_file_path).st_size > 0):
                with open(input_file_path) as source:
                    source_data = json.load(
                        source, object_pairs_hook=OrderedDict)
                doc, tag, text = Doc().tagtext()
                gen_html_from_source_data(source_data, tag, text)
                convert_time = get_date()
                with open(
                        os.path.join(
                            FOLDER_TO_LOOK_IN,
                            convert_time + '_output'), 'w') as f:
                    f.write(doc.getvalue())
                copyfile(
                    input_file_path,
                    os.path.join(FOLDER_TO_LOOK_IN, convert_time + '_input'))
                os.remove(input_file_path)
                log(logger, 'Input file successfully converted')
        except Exception as e:
            log(logger, "Error, exiting: {0}".format(e))
            sys.exit()


def get_date():
    return datetime.now().strftime('%Y.%m.%d_%H.%M.%S')


def log(logger, message):
    logger.debug("{0} {1}".format(get_date(), message))


def kill(pid_f, logger):
    if os.path.isfile(pid_f):
        with open(pid_f) as pid_file:
            pid = pid_file.read()
            try:
                os.kill(int(pid), signal.SIGKILL)
            except (OSError, ValueError) as e:
                log(logger, 'Process is not killed due to: {0}'.format(e))
            else:
                log(logger, 'Stopped')
                os.remove(pid_f)
    else:
        log(logger, 'There is no pid_file, nothing to kill')


if platform.system() == 'Windows':
    main()
else:
    parser = argparse.ArgumentParser()
    mutually_exclusive_group = parser.add_mutually_exclusive_group(
            required=True)

    mutually_exclusive_group.add_argument(
        "-start", action="store_true")
    mutually_exclusive_group.add_argument(
        "-stop", action="store_true")
    mutually_exclusive_group.add_argument(
        "-status", action="store_true")
    args = vars(parser.parse_args())

    if args.get('stop'):
        kill(PID, logger)
        sys.exit()

    elif args.get('status'):
        try:
            with open(PID) as pid_file:
                pid = pid_file.read()
            os.kill(int(pid), 0)
        except Exception as e:
            log(logger, "Converter is stopped")
        else:
            log(logger, "Converter is running")
        sys.exit()

    # kill in order not to start several processes
    kill(PID, logger)

    daemon = Daemonize(app="test_app", pid=PID, action=main, keep_fds=keep_fds)
    daemon.start()
