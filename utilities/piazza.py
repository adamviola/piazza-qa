from piazza_api import Piazza
import os.path

class PiazzaInterface:

    def __init__(self, username, password, course_id):
        self.__username = username
        self.__password = password
        self.course_id = course_id

        self.p = Piazza()

        self.__login()

        self.__load_seen_posts()

    def __login(self):
        self.p.user_login(self.__username, self.__password)
        self.course = self.p.network(self.course_id)

    def __load_seen_posts(self):
        self.seen_posts = {}
        if os.path.exists('./data/seen_posts.txt'):
            with open('./data/seen_posts.txt', 'r') as f:
                for line in f.readlines():
                    args = line.split()
                    self.seen_posts[args[0]] = int(args[1])

    def __save_seen_posts(self):
        with open('./data/seen_posts.txt', 'w') as f:
            for post_id, version in self.seen_posts.items():
                f.write('{} {}\n'.format(post_id, version))

    def __filter_questions(self, questions):
        filtered_questions = []
        for q in questions:
            # TODO: actually filter the questions
            filtered_questions.append(q)

        return filtered_questions


    def fetch_new_questions(self):
        new_questions = []
        
        # Fetch and iterate through feed for new questions
        feed = self.course.get_feed()['feed']
        for post in feed:
            post_id = post['id']

            # Investigates a top-level post if any of the following are true:
            # 1. It's a new question
            # 2. It's an already-seen question that has unanswered followups and the 'version' (thread history) has updated
            if (post_id not in self.seen_posts and post['type'] == 'question') or \
               (post_id in self.seen_posts and post['no_answer_followup'] > 0 and self.seen_posts[post_id] != post['version']):

                post_details = self.course.get_post(post_id)

                # Adds top-level post to new_questions if not already seen
                if post_id not in self.seen_posts:
                    new_questions.append(post_details['history'][0]['content'])

                # Marks top-level post as seen
                self.seen_posts[post_id] = int(post['version'])

                for subpost in post_details['children']:
                    # Adds followup question if it has no answer and hasn't already been seen
                    if subpost['id'] not in self.seen_posts and subpost['type'] == 'followup' and subpost['no_answer'] == 1:
                        new_questions.append(subpost['subject'])
                        # Marks followup post as seen
                        self.seen_posts[subpost['id']] = -1

        # Save seen posts
        self.__save_seen_posts()     

        # Filter out non-logistic questions and return the result
        return self.__filter_questions(new_questions)


    def reply_to_question(self, question):
        pass


    

    

    








    


