from assistant.assistant import AssistantService
from assistant.assistant_thread import AssistantThread

import argparse
import logging

cli_args = argparse.ArgumentParser(
    description='Pyyne CV Assistant using OpenAI GPT-3.')

# Enable debug mode
cli_args.add_argument('-d', '--debug', action='store_true',
                      help='Enable debug mode.')

# Display values for the run
cli_args.add_argument('--dry', action='store_true', default=False,
                      help='Does a dry run. Does not initialize the assistant.')

cli_args.add_argument('--cv', dest='cv_filename', type=str,
                      default=None, help='CV file to use.')
cli_args.add_argument(
    '-m', '--message',
    dest='message',
    type=str,
    default=None,
    help='Message to send. If -t or --thread is set, the message will be sent '
         'to the selected thread. Otherwise, it will be sent to the last active '
         'thread.'
)
cli_args.add_argument(
    '-t', '--thread',
    dest='thread_id',
    type=str,
    default=None,
    help='Select thread to use, and set as active.')

args = cli_args.parse_args()


def main(args: argparse.Namespace,
         logger: logging.Logger = logging.getLogger(__name__)) -> None:
    cvassistant = AssistantService()
    logger.info(
        f'Assistant "{cvassistant.name}" ({cvassistant.id}) is ready')

    if args.dry:
        pass
    else:
        if args.message:
            thread: AssistantThread = cvassistant.get_thread(args.thread_id)
            message = thread.send_message(args.message)
            thread.save_response(message.run_id, message.id)
        elif args.cv_filename:
            thread: AssistantThread = cvassistant.create_thread(
                [args.cv_filename])


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    logger.debug(f'Arguments: {args}')

    main(args, logger)
