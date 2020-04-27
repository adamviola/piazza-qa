import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Notifications:

    def __init__(self, email, password, recipients, automatically_reply):
        self.email = email
        self.password = password
        self.recipients = recipients
        self.automatically_reply = automatically_reply

    # Builds and sends email using suggestions 
    def send_suggestions(suggestions):
        message = "Message_you_need_to_send"

        for suggestion in suggestion_queue:
            message += str(suggestion)
        
        try:
            s = smtplib.SMTP('smtp.gmail.com', 587) 
            s.starttls() 

            s.login(email, password) 
            
            s.sendmail(email, recipients, message) 
            
            s.quit()
        except:
            return False

        return True
