from piazza_api import Piazza
import os.path
import html2text

class PiazzaInterface:

    FETCH_LIMIT = 10

    def __init__(self, username, password, course_id):
        self.__username = username
        self.__password = password
        self.course_id = course_id

        self.__h = html2text.HTML2Text()
        self.p = Piazza()

        self.__login()

        self.__load_seen_posts()
        


    def __login(self):
        self.p.user_login(self.__username, self.__password)
        self.course = self.p.network(self.course_id)

    def __load_seen_posts(self):
        self.seen_posts = {}
        if os.path.exists('./data/seen_posts.csv'):
            with open('./data/seen_posts.csv', 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    self.seen_posts[row[0]] = int(row[1])


            # with open('./data/seen_posts.txt', 'r') as f:
            #     for line in f.readlines():
            #         args = line.split()
            #         self.seen_posts[args[0]] = int(args[1])

    def __save_seen_posts(self):
        with open('./data/seen_posts.csv', 'w') as f:
            writer = csv.writer(f)
            for post_id, version in self.seen_posts.items():
                writer.writerow([post_id, version])


        # with open('./data/seen_posts.txt', 'w') as f:
        #     for post_id, version in self.seen_posts.items():
        #         f.write('{} {}\n'.format(post_id, version))

    def __filter_questions(self, questions):
        filtered_questions = []
        for q in questions:
            # TODO: actually filter the questions
            filtered_questions.append(q)

        return filtered_questions

    # Returns a list of question tuples
    # Each tuple takes the form (question_id, content, post_type)
    def fetch_new_questions(self):
        new_questions = []
        fetched_posts = 0
        
        # Fetch and iterate through feed for new questions
        feed = self.course.get_feed()['feed']
        for post in feed:
            post_id = post['id']

            # Investigates a top-level post if either of the following are true:
            # 1. It's an unseen and unanswered question
            # 2. It's has unanswered followups and either we haven't seen the question before or the 'main_version' (thread history) has updated
            if (post_id not in self.seen_posts and post['type'] == 'question' and post['no_answer'] == 1) or \
               (post['no_answer_followup'] > 0 and (post_id not in self.seen_posts or self.seen_posts[post_id] != post['main_version'])):

                post_details = self.course.get_post(post_id)
                fetched_posts += 1

                # Adds top-level post to new_questions if it is an unseen and unanswered question
                if post_id not in self.seen_posts and post['type'] == 'question' and post['no_answer'] == 1:
                    new_questions.append((post_id, h.handle(post_details['history'][0]['content']).strip(), 'post'))

                # Marks top-level post as seen
                self.seen_posts[post_id] = int(post['main_version'])

                for subpost in post_details['children']:
                    # Adds followup question if it has no answer and hasn't already been seen
                    if subpost['id'] not in self.seen_posts and subpost['type'] == 'followup' and subpost['no_answer'] == 1:
                        new_questions.append((subpost['id'], h.handle(subpost['subject']).strip(), 'followup'))
                        # Marks followup post as seen
                        self.seen_posts[subpost['id']] = -1

                # Enforce a post fetch limit so Piazza doesn't get angry at us
                if fetched_posts >= self.FETCH_LIMIT:
                    break

        # Save seen posts
        self.__save_seen_posts()     

        # Filter out non-logistic questions and return the result
        return self.__filter_questions(new_questions)


    def reply_to_questions(self, questions, answers):
        
        for i, q in enumerate(questions):
            # If question was a top-level post, create an instructor answer
            if q[2] == 'post':
                self.course.create_instructor_answer({'id': q[0]}, answers[i], 0)

            # If the question was a followup, reply to the followup
            elif q[2] == 'followup':
                self.course.create_reply({'id': q[0]}, answers[i])
        


    

    

    








    


