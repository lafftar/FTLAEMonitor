import asyncio
from os import makedirs, listdir

# import win32file

from utils.root import get_project_root


class Global:
    def __init__(self):
        # make required files
        base_user_path = f'{get_project_root()}/user_data'
        makedirs(base_user_path, exist_ok=True)
        required_files = ['isps.txt', 'links.txt', 'webhooks.txt', 'config.txt']
        current_files = listdir(base_user_path)
        for item in required_files:
            if item not in current_files:
                if item == 'config.txt':
                    with open(f'{get_project_root()}/user_data/{item}', 'w') as file:
                        file.write('TASKS_PER_SKUS -> 5\n'
                                   'REMINDER_TIMEOUT -> 120\n'
                                   'KEY -> WINX4-V1A0-XOLD-26A7-SGW3')
                        continue
                with open(f'{get_project_root()}/user_data/{item}', 'w') as file:
                    file.write('')

        # set global vars
        with open(f'{get_project_root()}/user_data/webhooks.txt') as file:
            self.webhooks = [line.strip() for line in file.readlines() if len(line.strip()) > 0]

        with open(f'{get_project_root()}/user_data/links.txt') as file:
            self.links = [line.strip() for line in file.readlines() if len(line.strip()) > 0]

        with open(f'{get_project_root()}/user_data/isps.txt') as file:
            self.isps = [line.strip().split(':') for line in file.readlines() if len(line.strip()) > 0]
            self.isps = [
                f'http://{line[0]}:{line[1]}'
                if len(line) == 2
                else
                f'http://{line[2]}:{line[3]}@{line[0]}:{line[1]}'
                for line in self.isps
            ]

        # grab config
        with open(f'{get_project_root()}/user_data/config.txt') as file:
            settings = {
                line.strip().split(' -> ')[0]: line.strip().split(' -> ')[1]
                for line in file.readlines()
                if len(line.strip()) > 0
            }
            self.tasks_per_skus = int(settings['TASKS_PER_SKUS'])
            self.key = settings['KEY']
            self.reminder_timeout = int(settings['REMINDER_TIMEOUT'])

        # increase limits
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        # win32file._setmaxstdio(8192)


GLOBAL = Global()
