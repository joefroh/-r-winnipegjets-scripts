""" Service execution file for GWG Leader Updater Service """

import argparse
import logging
import sys

from drive_manager import DriveManager
from gwg_leader_updater import GWGLeaderUpdater
from secret_manager import SecretManager
from time import sleep


def parse_args():
    """Handle arguments"""

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test', '-t' ,action='store_true', help='Run in test mode with team -1')
    group.add_argument('--prod', '-p', action='store_true', help='Run in production mode with full subscribed team list')
    parser.add_argument('--debug', '-d', action='store_true', help='debug messages turned on', default=False)
    parser.add_argument('--single', '-s', action='store_true', help='runs only once', default=False)

    gwg_args = parser.parse_args()

    return gwg_args

def init_logger(level):
    logging.basicConfig(level=level, filename="gwg_leader.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
    log = logging.getLogger("gwg_poster")
    log.info("Started gwg_poster")

def main():
    gwg_args = parse_args()

    level = logging.DEBUG if gwg_args.debug else logging.INFO
    init_logger(level)

    secrets = SecretManager()
    
    team = None

    if gwg_args.test:
        team = "-1"
    elif gwg_args.prod:
        team = "52"
    else:
        logging.getLogger("gwg_poster").critical("Something horrible happened because you should always have a single one of the above options on. Quitting.")
        sys.exit()

    gdrive = DriveManager(secrets, team=team, update=False)
    gwg_updater = GWGLeaderUpdater(gdrive, secrets, gwg_args)

    while True:
        gdrive.update_drive_files()

        pending_games = gdrive.new_response_data_available()

        if pending_games != []:
            gwg_updater.manage_gwg_leaderboard(pending_games)

        if gdrive.new_leaderboard_data():
            gwg_updater.update_master_list()
            gwg_updater.notify_reddit(team)

        # quit if we are testing instead of running forever
        if gwg_args.test:
            logging.getLogger("gwg_poster").info("Exiting a test run")
            return

        if gwg_args.single:
            logging.getLogger("gwg_poster").info("Exiting early due to --single command on cli")
            sys.exit()

        sleep_time = 60*60
        logging.getLogger("gwg_poster").info("No new data available for updating with. Sleeping for %s" % sleep_time)
        sleep(sleep_time)

if __name__ == '__main__':
    main()
