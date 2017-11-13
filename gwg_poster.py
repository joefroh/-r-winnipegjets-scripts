import json
import argparse
import traceback
import logging
from datetime import date
from urllib.request import urlopen
from datetime import datetime
from time import sleep

from drive_manager import DriveManager
from praw_login import r, DEFAULT_USERS, USER_NAME

gwg_args = None
gdrive = None
game_history = None
participating_teams = [52]
cached_inbox = None
log = None

def _update_todays_game(team):
    """Updates todays date with and game day info."""

    global game_history

    today = date.today()
    today = str(today.year) + "-" + str(today.month) + "-" + str(today.day)

    if gwg_args.test:
        team = 52
        today = "2017-11-16"

    attempts = 0
    while attempts < 2:
        try:
            attempts +=1
            data = urlopen("https://statsapi.web.nhl.com/api/v1/schedule?site=en_nhlCA&expand=schedule.teams,schedule.linescore,schedule.broadcasts.all&startDate=" + today + "&endDate=" + today + "&teamId=" + str(team))
            game_history = json.load(data)['dates']
            return
        except Exception as e:
            log.error("exception occurred in is_game_day trying again shortly")
            log.error(str(e))
            sleep(15)

    game_history = None

def is_game_day(team):
    """Checks if the Winnipeg jets are playing today. If so, returns true."""

    _update_todays_game(team)

    return game_history != [] and game_history != None

def _get_team_name(home=True):
    """gets the team name of the requested home/away pairing"""
    team_type = "home"
    if not home:
        team_type = "away"

    return game_history[0]['games'][0]['teams'][team_type]['team']['teamName']

def _get_game_number(team):
    """Returns what the next game number it is for team team."""

    if team == -1:
        team = 52

    win = loss = otl = 0
    if str(game_history[0]['games'][0]['teams']['home']['team']['id']) == str(team):
        win = game_history[0]['games'][0]['teams']['home']['leagueRecord']['wins']
        loss = game_history[0]['games'][0]['teams']['home']['leagueRecord']['losses']
        otl = game_history[0]['games'][0]['teams']['home']['leagueRecord']['ot']
    else:
        win = game_history[0]['games'][0]['teams']['away']['leagueRecord']['wins']
        loss = game_history[0]['games'][0]['teams']['away']['leagueRecord']['losses']
        otl = game_history[0]['games'][0]['teams']['away']['leagueRecord']['ot']

    # +1 because 'next' game.
    if gwg_args.game83:
        return "83"
    return str(win + loss + otl + 1)

def _get_date():
    """Returns todays date as a nice string"""

    today = date.today()
    return str(today.day) + "-" + str(today.month) + "-" + str(today.year)

def generate_post_title(team=52):
    """Creates the title of the post

    team is the team that this bot runs for

    Result is something like
    Jets @ Canucks 10/12/17 GWG Challenge #4
    """

    home = _get_team_name()
    away = _get_team_name(home=False)
    game_number = _get_game_number(team)
    game_date = _get_date()

    return away + " @ " + home + " " + game_date + " GWG Challenge #" + str(game_number)

def generate_post_contents(gwg_link):
    """create the threads body. include the form link for participation."""
    leader_link = gdrive.get_drive_filetype('leaderboard')['alternateLink']
    
    return  ("""[Link to current GWG challenge](%s)  \n\n
Please comment here immediately ('done' or a general comment about the challenge) following their GWG form submission to add a layer of security on your entry. If you don't comment and someone else types your user name into the form for an entry your GWG entry will be void! Avoid this by commenting so we can cross reference the form submission time with the Reddit comment time. \n\n
Every Correct answer you get gives you a point in the standings and at the end of the season the point leader will get a custom flair (Thanks KillEmAll!)!  \n\n
If at the end of the season two people are tied the win will go to whoever had the least GWG entries in total! If they both had the same amount of games played we will tie break on   \n\n
[Current Standings](%s)  \n\n
As always, if you find any issues please PM me directly and we will sort out any/all issues.  \n\n
NOTE: LATE ENTIRES WILL NOT BE ACCEPTED ANYTIME AFTER SCHEDULED GAME START UNLESS THERE IS AN OFFICAL GAME DELAY OF SOME SORT""" 
% (gwg_link, leader_link))

def get_gwg_contact(team):
    """take a team and returns a list of people that should be contacted if there is an issues with 
    the gwg form not being ready on time.
    """

    contacts = {
        -1: DEFAULT_USERS,
        52: DEFAULT_USERS,
    }

    return contacts.get(team, DEFAULT_USERS)

def get_reddit_from_team_id(team):
    """returns a subreddit from a passed teamid"""

    teams = {
            "-1": "jets_bot", 
            "52": "winnipegjets"}

    return teams.get(str(team), None)

def refresh_inbox_pms():
    global cached_inbox

    if not cached_inbox or datetime.now() - cached_inbox['time'] < datetime.timedelta(hours=1, minutes=30):
        log.info("Refreshing mailbox")
        cached_inbox = {'mail': r.inbox.sent(limit=64), 'time': datetime.now()}

def already_sent_reminder(owner):
    """Checks if we've already reminded someone about them needing to create a GWG form. 
    If so, returns True, if not, returns false. No need to spam the users.
    """

    refresh_inbox_pms()

    for message in cached_inbox['mail']:
        sent_today = check_same_day(message.created_utc)

        if (message.dest.name.lower() == owner.lower() and 
            "Hey you!" in message.body and
            sent_today) and not gwg_args.test:
            log.info("We've already alerted %s. Ignoring the warning" % owner)
            return True

    if gwg_args.test:
        log.info("Sending a PM because of test mode")
    else:
        log.info("We haven't alerted %s yet. Sending a PM." % owner)
    return False

def alert_gwg_owners(team, body=None):
    """Direct messages the owners of the GWG challenge that there isn't a form available
    for todays game and that their players are angry!!!
    """

    owners = get_gwg_contact(team)
    subject = "GWG form not created yet for \\r\\" + get_reddit_from_team_id(team)
    if not body:
        today = date.today()
        body = "Hey you! Log in and make a form for todays GWG challenge, ya bum! It's {} and your team plays today. Get on it!!!".format(today)

    mail_success = True
    for owner in owners:
        if already_sent_reminder(owner):
            continue

        success = False
        attempts = 0
        while not success and attempts < 5:
            try:
                r.redditor(owner).message(subject, body)
                success = True
            except Exception as e:
                log.error("Exception trying to mail redditer %s. Waiting 60 and trying again." % owner)
                log.error(traceback.print_stack())
                attempts += 1
                sleep(60)
        if not success:
            mail_success = False
    return mail_success

def attempt_new_gwg_post(team=-1):
    """Submits, creates and posts the GWG challenge post."""

    gwg_form = gdrive.get_gameday_form(_get_game_number(team))

    # message my owner and cry that we don't have a form to post
    if not gwg_form:
        log.info("No gwg form found for game day for team %s! Alerting owners of GWG challenge and continuing." % team)
        alert_gwg_owners(team)
        return True

    url = gwg_form['embedLink']
    title = generate_post_title()
    contents = generate_post_contents(url)
    reddit_name = get_reddit_from_team_id(team)
    try:
        r.subreddit(reddit_name).submit(title, selftext=contents)
        log.info("Successfully posted new thread to %s!" % reddit_name)
    except Exception as e:
        log.error("failed to post new thread to subreddit with error %s" % e )
        log.error(traceback.print_stack())
        return False
    return True

def check_same_day(requested_date):
    """checks if requested_date is the same as today."""
    today = date.today()

    posted_time = datetime.fromtimestamp(requested_date)
    posted_time = date(posted_time.year, posted_time.month, posted_time.day)

    return posted_time == today

def already_posted_gwg(team):
    """Checks if we've already posted the GWG thread in the team team sub"""

    for submission in r.redditor(USER_NAME).submissions.new():
        posted_today = check_same_day(submission.created_utc)
        
        if (submission.subreddit_name_prefixed.lower() == "r/" + team.lower() and 
            posted_today and
            "GWG" in submission.title):
            log.info("We posted the GWG already for team %s! Ignore this beast!" % team)
            return True
    return False

def init_gdrive(team):
    global gdrive
    gdrive = DriveManager(team=str(team))

def gwg_poster_runner(team=-1):
    """Checks if we need to post a new thread and if so, does it."""

    if is_game_day(team) and not already_posted_gwg(get_reddit_from_team_id(team)):
        init_gdrive(team)

        if not attempt_new_gwg_post(team=team):
            alert_gwg_owners(team, body="Unable to create new gwg post. Sorry, will try later.")
    else:
        log.info("Doing nothing since it isn't game day for team %s." % team)

def main():

    if gwg_args.test:
        gwg_poster_runner(-1)
    else:
        for team in participating_teams:
            gwg_poster_runner(team)

def setup():
    global gwg_args
    global log

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test', '-t' ,action='store_true', help='Run in test mode with team -1')
    group.add_argument('--prod', '-p', action='store_true', help='Run in production mode with full subscribed team list')
    parser.add_argument('--game83', action='store_true', help='forces a GWG challenge to not be present', default=False)

    gwg_args = parser.parse_args()

    level = logging.INFO
    if gwg_args.test:
        level = logging.DEBUG

    logging.basicConfig(level=level, filename="gwg_poster.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
    log = logging.getLogger("gwg_poster")
    log.info("Stared gwg_poster")

if __name__ == '__main__':
    setup()
    main()