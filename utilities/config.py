import os.path
import logging
from configparser import ConfigParser, ParsingError

# Configuration settings structure
configuration_settings = {
    'Account Settings': ['username', 'password', 'course_id'],
    'Runtime Settings': ['check_interval', 'automatically_reply', 'answerability_threshold'],
    'Notification Settings': ['send_notifications', 'email', 'email_password', 'recipients']
}

def load_config():
    """Loads configuration data from config.ini

    Runs several checks over the config.ini to ensure correctness
    and loads the data into memory.

    Returns:
        ConfigParser of config.ini
    """
    # Check if configuration file exists
    if (not os.path.exists('config.ini')):
        logging.error('Configuration file \'config.ini\' is missing.')
        exit()

    # Check for configuration file parsing errors
    try:
        config = ConfigParser()
        config.read('config.ini')
    except ParsingError as e:
        logging.error(str(e))
        exit()

    # Verify that configuration file contains all settings to prevent rare errors
    for section in configuration_settings:
        if not config.has_section(section):
            logging.error('Configuration file \'config.ini\' is missing section \'%s\'.' % section)
            exit()

        for option in configuration_settings[section]:
            if not config.has_option(section, option):
                logging.error('Configuration file \'config.ini\' is missing option \'%s\' from section \'%s\'.' % (option, section))
                exit()

    logging.info('Configuration file looks good.')

    return config