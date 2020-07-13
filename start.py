import datetime
import time
import os
import sys
import traceback
import subprocess

import logging
logging.basicConfig(filename='./logs/' + datetime.datetime.now().strftime("%Y-%m-%d_%I-%M-%S_%p") + '.log',
                    format='%(asctime)s [%(levelname)s]: %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

from piazza_api import Piazza
from utilities.piazza import PiazzaInterface
from utilities.qa import QASystem
from utilities.config import load_config
from utilities.parser import process_documents
from utilities.notifications import send_email

# Logs unhandled exceptions instead of printing them
def log_except_hook(type_, value, tb):
    text = "".join(traceback.format_exception(type_, value, tb))
    logging.error("Unhandled exception: %s", text)
    print('Execution halted. Check logs for details.')
sys.excepthook = log_except_hook

# Load configuration data
config = load_config()

username = config['Account Settings']['username']
password = config['Account Settings']['password']
course_id = config['Account Settings']['course_id']

check_interval = float(config['Runtime Settings']['check_interval'])
automatically_reply = config['Runtime Settings'].getboolean('automatically_reply')
answerability_threshold = float(config['Runtime Settings']['answerability_threshold'])

send_notifications = config['Notification Settings'].getboolean('send_notifications')
email = config['Notification Settings']['email']
email_password = config['Notification Settings']['email_password']
recipients = config['Notification Settings']['recipients'].split()

drqa_retriever_path = './model/DrQA/scripts/retriever/'
data_path = './data/'

# Prepare documents for DrQA
logging.info('Checking if documents have changed...')
if process_documents():
    logging.info('Documents have changed and have been converted to text.')

    # Builds database from documents
    os.remove(data_path + 'docs.db')
    subprocess.run(['python', drqa_retriever_path + 'build_db.py', data_path + 'docs.json', data_path + 'docs.db'])
    logging.info('Database has been built from text.')

    # Builds tf-idf features
    subprocess.run(['python', drqa_retriever_path + 'build_tfidf.py', data_path + 'docs.db', data_path])
    logging.info('TF-IDF features have been built.')
else:
    logging.info('Documents have not changed.')


# Initialize QA system and Piazza interface
p = PiazzaInterface(username, password, course_id)
qa = QASystem()
last_login = time.time()
logging.info('QA system and Piazza interface initialization complete.')

while True:
    # Reinitialize the Piazza interface every hour
    if time.time() - last_login > 3600:
        success = False
        while not success:
            try: 
                p = PiazzaInterface(username, password, course_id)
                success = True
                last_login = time.time()
                logging.info('Reinitialized Piazza interface after at least an hour since last login')
            except:
                logging.error('Piazza interface reinitialization failed. Waiting 5 minutes before trying again...')
                time.sleep(300)

    # Fetch for new questions on Piazza
    try:
        questions = p.fetch_new_questions()
    except:
        logging.error('Fetch for questions on Piazza failed.')
        questions = []

    # If new threads exist, send them to QA system
    if len(questions) > 0:

        # Fetching 5 possible answers to each question
        logging.info(str(len(questions)) + ' question(s) found on Piazza.')
        answers = qa.get_answers(questions)

        # Enforce answerability classifier score threshold and build question-answer pair
        qa_pairs = []
        for i, question in enumerate(questions):
            for answer in answers[i]:
                if answer['answerability'] > answerability_threshold:
                    qa_pairs.append({
                        'id': question[0],
                        'question': question[1],
                        'type': question[2],
                        'answer': answer['answer'],
                        'context': answer['context']
                    })
                    break
        logging.info('Answers to ' + str(len(qa_pairs)) + ' question(s) remain with answerability scores above the threshold.')
        for qa_pair in qa_pairs:
            logging.info('Q: ' + question[1])
            logging.info('A: ' + answer['answer'] + '; ' + answer['context'])

        # If any answers are left, reply and/or notify
        if len(qa_pairs) > 0:
            if automatically_reply:
                try:
                    p.reply_to_questions(qa_pairs)
                    logging.info('Automatically replied on Piazza.')
                except:
                    logging.error('Automatic reply on Piazza failed. Triggering Piazza interface reinitialization...')
                    last_login = 0

            if send_notifications:
                try:
                    send_email(email, email_password, recipients, qa_pairs, automatically_reply)
                    logging.info('Sent email notification.')
                except:
                    logging.error('Email notification failed.')
                    
    else:
        logging.info('No new questions found.')

    logging.info('Waiting ' + str(check_interval) + ' minute(s)...')
    time.sleep(check_interval * 60)
