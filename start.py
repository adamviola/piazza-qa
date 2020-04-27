import time
import os.path
import subprocess
from utilities.piazza import PiazzaInterface
from utilities.notifications import Notifications
from utilities.parser import Parser
from utilities.qa import QASystem
from piazza_api import Piazza
from configparser import ConfigParser, ParsingError

# Configuration settings structure
configuration_settings = {
    'Account Settings': ['username', 'password', 'course_id'],
    'Runtime Settings': ['check_interval', 'consider_followups', 'automatically_reply'],
    'Notification Settings': ['send_notifications', 'email', 'email_password', 'recipients']
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

# Configuration data
username = config['Account Settings']['username']
password = config['Account Settings']['password']
course_id = config['Account Settings']['course_id']

check_interval = float(config['Runtime Settings']['check_interval'])
consider_followups = config['Runtime Settings'].getboolean('consider_followups')
automatically_reply = config['Runtime Settings'].getboolean('automatically_reply')

send_notifications = config['Runtime Settings'].getboolean('send_notiifcations')
email = config['Notification Settings']['email']
email_password = config['Notification Settings']['email_password']
recipients = config['Notification Settings']['recipients'].split()

# Initialize utility objects
# p = PiazzaInterface(username, password, course_id)
# n = Notifications(email, email_password, recipients, automatically_reply)


# Preprocess documents
parser = Parser()
parser.process_documents()

drqa_retriever_path = './model/DrQA/scripts/retriever/'
data_path = './data/'

# # Builds database from documents
# subprocess.run(['python', drqa_retriever_path + 'build_db.py', data_path + 'docs.json', data_path + 'docs.db'])
# print('db complete')

# # Builds tf-idf features
# subprocess.run(['python', drqa_retriever_path + 'build_tfidf.py', data_path + 'docs.db', data_path])
# print('tf-idf complete')


# qa = QASystem()

# answers = qa.get_answers(['where are the SI sessions?'])

# print('\n\nHERE WE GO')
# if len(answers[0]) == 0:
#     print('no answers')
# else:
#     for answer in answers[0]:
#         print(answer.keys())
#         print(answer)
#         print('')



# while True:

#     # Fetch new threads
#     questions = p.fetch_new_questions()

#     # If new threads exist, send them to QA system
#     if len(questions) > 0:
#         answers = []

#         # If answers exist, reply and/or notify
#         if len(answers) > 0:
#             if automatically_reply:
#                 p.reply_to_questions(questions, answers)

#             if send_notifications:
#                 pass
#                 #n.send
        

#     time.sleep(check_interval * 60)

