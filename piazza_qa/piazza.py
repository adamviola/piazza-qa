from piazza_api import Piazza
import time


def main():

    # Load config.ini 


    p = Piazza()
    p.user_login('', '')

    profile = p.get_user_profile()
    print(profile)

    course = p.network('k7gqop42az52ck')

    print(course.get_feed())


def loop():





    time.sleep()
    pass

def fetch_recent_questions():
    