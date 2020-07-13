import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Builds and sends email using suggestions 
def send_email(email, password, recipients, qa_pairs, automatically_reply):
    
    if automatically_reply:
        body = 'Hi,\n\nI automatically replied to the following logistics question(s):\n\n'
    else:
        body = 'Hi,\n\nI have answer suggestion(s) for the following logistics question(s):\n\n'

    for qa_pair in qa_pairs:
        body += 'Question: ' + qa_pair['question'] + '\n'
        body += 'Answer: ' + qa_pair['answer'] + '\n'
        body += 'Context: ' + qa_pair['context'] + '\n\n'

    body += 'Hope this helps,\nPiazza Bot'
    
    message = 'Subject: {}\n\n{}'.format('Piazza Logistics Questions', body)
    
    s = smtplib.SMTP('smtp.gmail.com', 587) 
    s.starttls() 

    s.login(email, password) 

    s.sendmail(email, recipients, message) 
    
    s.quit()
