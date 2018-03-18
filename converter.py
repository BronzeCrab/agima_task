import logging
import os
from datetime import datetime
import argparse
import sys
import signal
import json
from shutil import copyfile
from collections import OrderedDict

from daemonize import Daemonize
from yattag import Doc

PID = "/tmp/converter.pid"
# logger's settings
log_file = "/tmp/converter.log"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.FileHandler(log_file, "a")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

INPUT_FILE_NAME = 'source.json'
FOLDER_TO_LOOK_IN = '/home/austinnikov/projects/agima_task/converter'


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
                for elem in source_data:
                    for key in elem:
                        if key == 'body':
                            with tag('p'):
                                text(elem[key])
                        else:
                            with tag(key):
                                text(elem[key])
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
        except Exception as e:
            log(logger, e)


def get_date():
    return datetime.now().strftime('%Y.%m.%d-%H:%M:%s')


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
