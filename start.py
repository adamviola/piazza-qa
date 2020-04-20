import time
import os.path
from utilities.piazza import PiazzaInterface
import utilities.notifications as n
import utilities.documents as d
from piazza_api import Piazza
from configparser import ConfigParser, ParsingError

# Configuration settings structure
configuration_settings = {
    'Account Settings': ['username', 'password', 'course_link'],
    'Runtime Settings': ['check_interval'],
    'Notification Settings': ['email', 'email_password', 'recipient_email', 'notification_interval']
}




# Check if configuration file exists
if (not os.path.exists('config.ini')):
    print('Configuration file \'config.ini\' is missing.')
    exit()

# Check for configuration file parsing errors
try:
    config = ConfigParser()
    config.read('config.ini')
except ParsingError as e:
    print(str(e))
    exit()

# Verify that configuration file contains all settings to prevent rare errors
for section in configuration_settings:
    if not config.has_section(section):
        print('Configuration file \'config.ini\' is missing section \'%s\'.' % section)
        exit()

    for option in configuration_settings[section]:
        if not config.has_option(section, option):
            print('Configuration file \'config.ini\' is missing option \'%s\' from section \'%s\'.' % (option, section))
            exit()




# Check for new documents
# d.check_documents()




# Configuration data
username = config['Account Settings']['username']
password = config['Account Settings']['password']

check_interval = float(config['Runtime Settings']['check_interval'])
notification_interval = float(config['Notification Settings']['notification_interval'])

email = config['Notification Settings']['email']
email_password = config['Notification Settings']['email_password']

recipient_email = config['Notification Settings']['recipient_email']

last_notification_time = 0
suggestion_queue = [1]

while True:

    # Fetch new threads

    # If new threads exist, send them to qa system

    # If Answers exist, append to suggestion_queue

    if len(suggestion_queue) > 0 and time.time() - last_notification_time > notification_interval:
        print('send notification')

    time.sleep(check_interval * 60)
