import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
  

suggestion_queue = []


# Builds and sends email from suggestion_queue to notification recipient
# Returns true if successful and false otherwise
def send_notification():
    # package up email based on contents from queue and send
    message = "Message_you_need_to_send"

    for suggestion in suggestion_queue:
        message += str(suggestion)
    
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587) 
        s.starttls() 

        s.login("qapiazzabot@gmail.com", "") 
        
        s.sendmail("qapiazzabot@gmail.com", "qapiazzabot@gmail.com", message) 
        
        s.quit()
    except:
        print("Email notification failed...")
        return False

    suggestion_queue.clear()
    
    return True



# Adds a question with the corresponding set of suggested answers to the suggestion queue
def enqueue_suggestion(question, answers, link):
    suggestion_queue.append({
        "question": question,
        "answers": answer,
        "link": link
    })


send_notification()