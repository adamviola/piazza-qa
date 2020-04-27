
class DocumentManager:


    def __init__(self):
        pass


    def __load_processed_documents(self):
        self.seen_posts = set()
        if os.path.exists('./data/processed_documents.txt'):
            with open('./data/processed_documents.txt', 'r') as f:
                for line in f.readlines():
                    args = line.split()
                    self.seen_posts[args[0]] = int(args[1])

    def __save_processed_documents(self):
        with open('./data/processed_documents.txt', 'w') as f:
            for post_id, version in self.seen_posts.items():
                f.write('{} {}\n'.format(post_id, version))

    def check_for_documents():
        pass