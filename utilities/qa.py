import drqa.tokenizers as dk
import drqa.retriever as ret
import drqa.reader as dr
import numpy as np
import torch
import pytorch_lightning as pl
from utilities.adapter_bert import AdapterBert, setup_adapters
from transformers import BertTokenizer

corenlp_path = './model/DrQA/data/corenlp/*'  # CoreNLP path (should be installed along with DrQA- included in those instructions: https://github.com/facebookresearch/DrQA)
tfidf_path = "./data/docs-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz"  # tfidf model from processing step
model_path = './model/DrQA/data/reader/multitask.mdl'  # DrQA pretrained model from https://github.com/facebookresearch/DrQA

docs_json_path = "./data/docs.json"  # json file containing all docs from preprocessing step

db_path = "./data/docs.db"  # db file from processing step


results_csv_path = "./two_step/physics-logistic-question-results_two-step_normalize_question-only_no-question-answers.csv"  # output containing csv of top 5 potential answers to each question


# answerability files
model_name = "bert-base-uncased"
load_name = "./model/bert-base-uncased_0.1_32_adapter_8_epochs_20_SQuAD_transfer_NQ_4-cands-per-example__ckpt_epoch_19.ckpt"


MAX_LEN = 300

# settings
num_predictions = 5
GROUP_LENGTH = 500  # character cutoff for a new paragraph

class Model(pl.LightningModule):

    def __init__(self):
        super(Model, self).__init__()
        setup_adapters(8)
        model = AdapterBert.from_pretrained(model_name, num_labels=2)  # , cache_dir=cache_directory)
        # model = BertForSequenceClassification.from_pretrained(model_name, num_labels=2, cache_dir=cache_directory)
        self.model = model

    def forward(self):
        pass


class QASystem:

    def __init__(self):
        dk.set_default('corenlp_classpath', corenlp_path)
        dr.set_default('model', model_path)

        # DrQA retriever
        self.retriever = ret.get_class('tfidf')(tfidf_path=tfidf_path)

        # DrQA reader
        self.reader = dr.Predictor(model_path, "corenlp", normalize=True)

        # Answerability classifier
        self.tokenizer = BertTokenizer.from_pretrained(model_name, do_lower_case="uncased" in model_name)  # , cache_dir=cache_directory)
        self.pretrained_model = Model()

        checkpoint = torch.load(load_name, map_location=lambda storage, loc: storage)
        self.pretrained_model.load_state_dict(checkpoint['state_dict'])

        self.pretrained_model.zero_grad()
        self.pretrained_model.eval()
        self.pretrained_model.freeze()
        torch.set_grad_enabled(False)

        # Creates a map from document id to 
        self.docs_txt = {}
        with open(docs_json_path, encoding='utf-8') as docs_text:
            for line in docs_text:
                line = eval(line)
                self.docs_txt[line["id"]] = line["text"]


    def __closest_docs(self, query, k=5):
        """Closest docs by dot product between query and documents
        in tfidf weighted word vector space.
        """

        try:
            spvec = self.retriever.text2spvec(query)
        except Exception:
            return [], []
        res = spvec * self.retriever.doc_mat
        query_magnitude = np.sqrt(spvec.multiply(spvec).sum())
        doc_magnitude = np.array((self.retriever.doc_mat).multiply(self.retriever.doc_mat).sum(axis=0)).flatten()
        doc_magnitude = np.sqrt(doc_magnitude)[res.indices]
        denominator = np.array(query_magnitude * doc_magnitude).flatten()
        res.data /= denominator

        if len(res.data) <= k:
            o_sort = np.argsort(-res.data)
        else:
            o = np.argpartition(-res.data, k)[0:k]
            o_sort = o[np.argsort(-res.data[o])]

        doc_scores = res.data[o_sort]
        doc_ids = [self.retriever.get_doc_id(i) for i in res.indices[o_sort]]
        return doc_ids, doc_scores

    
    # Returns predictions given a document and question
    def __provide_answer(self, document, question, candidates=None, top_n=3):
        predictions = self.reader.predict(document, question, candidates, top_n)
        # table = prettytable.PrettyTable(['Rank', 'Span', 'Score'])
        # for i, p in enumerate(predictions, 1):
        #     table.add_row([i, p[0], p[1]])
        return predictions

    # for answerability classifier
    def __preprocess(self, tokenizer, x):
        # Given two sentences, x["string1"] and x["string2"], this function returns BERT ready inputs.
        inputs = tokenizer.encode_plus(
                x["question"],
                x["context"],
                add_special_tokens=True,
                max_length=MAX_LEN,
                )

        # First `input_ids` is a sequence of id-type representation of input string.
        # Second `token_type_ids` is sequence identifier to show model the span of "string1" and "string2" individually.
        input_ids, token_type_ids = inputs["input_ids"], inputs["token_type_ids"]
        attention_mask = [1] * len(input_ids)

        # BERT requires sequences in the same batch to have same length, so let's pad!
        padding_length = MAX_LEN - len(input_ids)

        pad_id = tokenizer.pad_token_id
        input_ids = input_ids + ([pad_id] * padding_length)
        attention_mask = attention_mask + ([0] * padding_length)
        token_type_ids = token_type_ids + ([pad_id] * padding_length)

        # Super simple validation.
        assert len(input_ids) == MAX_LEN, "Error with input length {} vs {}".format(len(input_ids), MAX_LEN)
        assert len(attention_mask) == MAX_LEN, "Error with input length {} vs {}".format(len(attention_mask), MAX_LEN)
        assert len(token_type_ids) == MAX_LEN, "Error with input length {} vs {}".format(len(token_type_ids), MAX_LEN)

        # Convert them into PyTorch format.
        input_ids = torch.tensor([input_ids])
        attention_mask = torch.tensor([attention_mask])
        token_type_ids = torch.tensor([token_type_ids])

        # DONE!
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids
        }




    def get_answers(self, questions):
        answers = []
        for question in questions:
            doc_names, doc_scores = self.__closest_docs(question, k=10)



            doc_index = {}
            all_predictions = []

            paragraph_txts = set()
            for i in range(len(doc_names)): # LOOP OVER ALL RETRIEVED DOCUMENTS
                doc_index[doc_names[i]] = {"score": doc_scores[i]} # ADD DOCUMENT SCORE AND DATE TO INDEX

                # get text of document and split into paragraphs
                curr_txt = self.docs_txt[doc_names[i]]   # SAVE DOCUMENT TEXT TO CURR_TEXT

                paragraphs = []
                curr_paragraph = []
                curr_len = 0
                for split in curr_txt.split("\n"): # FOR EACH WORD IN TEXT
                    split = split.strip()
                    if len(split) == 0:
                        continue

                    # Once paragraph reaches group length, end paragraph and start a new one
                    if len(curr_paragraph) > 0 and curr_len + len(split) > GROUP_LENGTH:
                        new_paragraph = " ".join(curr_paragraph)
                        if new_paragraph not in paragraph_txts:
                            paragraphs.append(new_paragraph)
                            paragraph_txts.add(new_paragraph)

                        curr_paragraph = []
                        curr_len = 0
                    curr_paragraph.append(split)
                    curr_len += len(split)

                # Once document is finished being read, officially add the last paragraph
                if len(curr_paragraph) > 0:
                    paragraphs.append(" ".join(curr_paragraph))

                # Gets answer for each paragraph
                best_score = 0
                best_prediction = None
                for paragraph in paragraphs:
                    predictions = self.__provide_answer(paragraph, question, top_n=1)
                    predictions = list(map(lambda e: (e[0], e[1], doc_names[i], paragraph), predictions))

                    for p in predictions:
                        if p[1] > best_score:
                            best_score = p[1]
                            best_prediction = p

                all_predictions.append(best_prediction)

            # Sort predictions by answer score and truncate
            all_predictions = sorted(all_predictions, key=lambda r: r[1], reverse=True)[:num_predictions]

            top_answers = []
            if len(all_predictions) > 0:
                for i, p in enumerate(all_predictions, 1):
                    rank = i
                    ans = p[0]
                    doc_name = p[2]
                    ans_score = p[1]
                    context = p[3]

                    preprocessed = self.__preprocess(self.tokenizer, {"question": question, "context": context})
                    input_ids = preprocessed["input_ids"]
                    attention_mask = preprocessed["attention_mask"]
                    token_type_ids = preprocessed["token_type_ids"]

                    logits = self.pretrained_model.model(
                        input_ids,
                        token_type_ids=token_type_ids,
                        attention_mask=attention_mask
                    )
                    answerability_score = torch.nn.functional.softmax(logits[0][0], dim=0)[1]

                    doc_score = doc_index[doc_name]["score"]
                    # table.add_row([rank, ans, doc_name, ans_score, doc_score, doc_date])

                    top_answers.append({
                        'answer': p[0],                             # Short answer
                        'context': p[3],                            # Answer context
                        'doc_name': p[2],                           # Document name
                        'doc_score': doc_index[doc_name]['score'],  # DrQA retrieval document score
                        'ans_score': p[1],                          # DrQA answer score
                        'answerability': answerability_score        # Answerability classifier score   
                    })

            answers.append(top_answers)

        return answers

            













