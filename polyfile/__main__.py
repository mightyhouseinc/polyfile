import argparse
import json
import logging
import sys

from . import logger
from . import polyfile


log = logger.getStatusLogger("polyfile")


def main(argv=None):
    parser = argparse.ArgumentParser(description='A utility to recursively map the structure of a file.')
    parser.add_argument('FILE', help='The file to analyze')
    parser.add_argument('--debug', '-d', action='store_true', help='Print debug information')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress all log output (overrides --debug)')

    if argv is None:
        argv = sys.argv
    
    args = parser.parse_args(argv[1:])

    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(logger.STATUS)

    matches = []
    for match in polyfile.match(args.FILE):
        if hasattr(match.match, 'filetype'):
            filetype = match.match.filetype
        else:
            filetype = match.name
        if match.parent is None:
            log.info(f"Found a file of type {filetype} at byte offset {match.offset}")
            matches.append(match)
        elif isinstance(match, polyfile.Submatch):
            log.info(f"Found a subregion of type {filetype} at byte offset {match.offset}")
        else:
            log.info(f"Found an embedded file of type {filetype} at byte offset {match.offset}")
    sys.stderr.flush()
    print(json.dumps([match.to_obj() for match in matches]))


if __name__ == '__main__':
    main()
