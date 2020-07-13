"""System for interacting with Piazza."""

from piazza_api import Piazza
import re
import csv
import os.path
import html2text

class PiazzaInterface:
    """Interface for reading and replying to Piazza questions."""

    FETCH_LIMIT = 10
    FILTER_KEYWORDS = set(["due", "credit", "grade", "email", "time", "available", "day",
        "date", "upload", "location", "when", "where", "renew", "purchase", "payment",
        "today", "format", "tonight", "buy", "account", "folder", "evaluation",
        "lecture", "slide", "class", "survey", "syllabus", "calendar"])

    def __init__(self, username, password, course_id):
        self.__username = username
        self.__password = password
        self.__course_id = course_id
        self.__path = './data/' + course_id + '.csv'

        self.__h = html2text.HTML2Text()
        self.p = Piazza()

        self.__login()
        self.__load_seen_posts()

    def __login(self):
        self.p.user_login(self.__username, self.__password)
        self.course = self.p.network(self.__course_id)


    """
    Managing Seen Posts:

    To prevent the system from finding answers to the same posts multiple times,
    the system maintains a file with the name `course_id`.csv. Each row of the csv
    corresponds to either a top-level post or a followup that has been examined.
    The row contains the id of the post and its 'version'. Followups have -1 version.
    Piazza's "feed" gives the subject and a bit of the content of every top-level
    post. To see the rest of the content or the followup posts of a top-level post,
    an additional network call must be made. Luckily, in the feed, Piazza provides
    a 'version' field for each top-level post, which is increased with each new
    post on a thread, and an 'unresolved followups' field for each top-level post,
    which tells us the number of unresolved followup posts. These two fields are
    provided for every top-level post with no extra network calls.
    
    Here's how we identify which top-level posts to examine:
    
    We choose to examine (aka make the extra network call to) a top-level post if
    any of the following are true:
        - It's unanswered and we've never seen it before (we check the csv for this)
        - It has unresolved followups and either we haven't seen it before (check csv)
          or we have seen it and its version has updated (check version in csv)

    Once we make the network call to see the details of a top-level post, we see
    all of its followup posts. We move forward with the top-level posts and all
    the unresolved followups that are not already in our csv.
    
    """

    def __load_seen_posts(self):
        self.seen_posts = {}
        if os.path.exists(self.__path):
            with open(self.__path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    self.seen_posts[row[0]] = int(row[1])

    def __save_seen_posts(self):
        with open(self.__path, 'w') as f:
            writer = csv.writer(f)
            for post_id, version in self.seen_posts.items():
                writer.writerow([post_id, version])

    def __filter_questions(self, questions):
        filtered_questions = []
        for q in questions:
            tokens = re.split(r'\W+', q[1].lower())
            print(q[1])
            print(tokens)

            matches = 0
            for token in tokens:
                if token in self.FILTER_KEYWORDS:
                    matches += 1
                    if matches == 2:
                        filtered_questions.append(q)
                        break            

        return filtered_questions

    def fetch_new_questions(self):
        """Fetches new questions from Piazza.
        
        This function makes a request to Piazza for the course's feed.
        New question posts and followup questions that are deemed to
        be logistics-related are returned. 
        
        Returns:
            List of question tuples of the form (id, content, 'post' or 'followup')
        """

        new_questions = []
        fetched_posts = 0
        
        # Fetch and iterate through feed for new questions
        feed = self.course.get_feed()['feed']
        for post in feed:
            post_id = post['id']

            # Investigates a top-level post if either of the following are true:
            # 1. It's an unseen and unanswered question
            # 2. It has unanswered followups and either we haven't seen the question before or the 'main_version' (thread history) has updated
            if (post_id not in self.seen_posts and post['type'] == 'question' and post['no_answer'] == 1) or \
               (post['no_answer_followup'] > 0 and (post_id not in self.seen_posts or self.seen_posts[post_id] != post['main_version'])):

                # Fetches entire thread of top-level post
                post_details = self.course.get_post(post_id)
                fetched_posts += 1

                # Adds top-level post to new_questions if it is an unseen and unanswered question
                if post_id not in self.seen_posts and post['type'] == 'question' and post['no_answer'] == 1:
                    new_questions.append((post_id, self.__h.handle(post_details['history'][0]['content']).strip(), 'post'))

                # Marks top-level post as seen
                self.seen_posts[post_id] = int(post['main_version'])

                for subpost in post_details['children']:
                    # Adds followup question if it has no answer and hasn't already been seen
                    if subpost['id'] not in self.seen_posts and subpost['type'] == 'followup' and subpost['no_answer'] == 1:
                        new_questions.append((subpost['id'], self.__h.handle(subpost['subject']).strip(), 'followup'))
                        # Marks followup post as seen
                        self.seen_posts[subpost['id']] = -1

                # Enforce a post fetch limit so Piazza doesn't get angry at us
                if fetched_posts >= self.FETCH_LIMIT:
                    break

        # Save seen posts
        self.__save_seen_posts()     

        # Filter out non-logistic questions and return the result
        return self.__filter_questions(new_questions)


    def reply_to_questions(self, qa_pairs):
        """Replies to a list of questions on Piazza.
        
        Given a list of questions and answer pairs, this function
        makes a request to Piazza to reply to each question with its
        corresponding answer.
        
        Args:
            qa_pairs: list of question-answer pair dicts of the form
            {
                'id': string id of question,
                'question': string question,
                'type': 'post' or 'followup',
                'answer': string short answer,
                'context': string answer context
            }
        """
        
        for qa_pair in qa_pairs:
            answer_text = 'I found this: ' + qa_pair['answer'] + '\n\n' + qa_pair['context']

            # If question was a top-level post, create an instructor answer
            if qa_pair['type'] == 'post':
                self.course.create_instructor_answer({'id': qa_pair['id']}, answer_text, 0)

            # If the question was a followup, reply to the followup
            elif qa_pair['type'] == 'followup':
                self.course.create_reply({'id': qa_pair['id']}, answer_text)
        


    

    

    








    


