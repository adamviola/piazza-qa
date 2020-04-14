import os.path
from configparser import ConfigParser, ParsingError
from piazza_qa.piazza import main

configuration_settings = {
    'Account Settings': ['username', 'password', 'course_link'],
    'Runtime Settings': ['check_interval'],
    'Notification Settings': ['email', 'email_password', 'recipient_email', 'max_notification_rate']
}

# Check if configuration file exists
if (not os.path.exists('config.ini')):
    print('Configuration file \'config.ini\' is missing.')
    exit()

# Check for parsing errors
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

# main()