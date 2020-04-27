import fitz
import glob
import os
import datetime
import numpy as np

import pandas as pd
import docx2txt
import html2text

class Parser:

    top_dir = "./documents/"  # directory from which to recursively search downward for documents
    processed_dir = "./data/documents/"  # directory where preprocessed files will be stored
    out_json_filepath = "./data/docs.json"  # this is the main output from this script, used in the next step of database creation

    GROUP_LENGTH = 220  # character cutoff for a new paragraph

    def __init__(self):
        self.paragraph_txts = set()
        self.seen_files = {}

        # with open()

    # def write_file_timestamp(self, out_file, cur_file, date=None, original_name=None):
    #     if date is not None:
    #         creation_time = date
    #     else:
    #         if original_name is not None:
    #             creation_time = os.stat(original_name).st_ctime
    #         else:
    #             creation_time = os.stat(cur_file).st_ctime
    #         # print(creation_time)
    #         creation_time = str(datetime.date.fromtimestamp(creation_time))
    #     out_file.write(cur_file + "," + creation_time + "\n")


    def split_to_paragraphs(self, curr_txt):
        paragraphs = []
        curr_paragraph = []
        curr_len = 0
        for split in curr_txt.split("\n"):
            split = split.strip()
            if len(split) == 0:
                continue

            if len(curr_paragraph) > 0 and curr_len + len(split) > self.GROUP_LENGTH:
                new_paragraph = " ".join(curr_paragraph)
                if new_paragraph not in self.paragraph_txts:
                    paragraphs.append(new_paragraph)
                    self.paragraph_txts.add(new_paragraph)

                curr_paragraph = []
                curr_len = 0
            curr_paragraph.append(split)
            curr_len += len(split)
        if len(curr_paragraph) > 0:
            paragraphs.append(" ".join(curr_paragraph))

        return paragraphs


    def write_to_file(self, txt, doc_name, doc_date=None, original_name=None, post_subject=None):
        assert doc_date is not None or original_name is not None
        pars = [txt]  ####split_to_paragraphs(txt)

        i = 0
        for par in pars:
            if post_subject is not None:
                par = post_subject + ".\t" + par

            doc_name_temp = doc_name.replace(".txt", "_" + str(i) + ".txt")
            new_filename = self.processed_dir + doc_name_temp

            with open(new_filename, "wb") as txt_file:
                txt_file.write(par.encode('utf-8', 'ignore'))

            i += 1

    def process_documents(self):

        post_lengths = []
        with open(self.timestamps_filepath, "w", encoding='utf-8') as self.timestamps_file:

            for pdf_name in glob.glob(self.top_dir + "**/*.pdf", recursive=True):
                try:
                    pdf = fitz.open(pdf_name)

                    doc_name = pdf_name.replace('.pdf', '.txt').split("/")[-1]

                    pdf_text = ""
                    for i in range(pdf.pageCount):
                        pdf_page = pdf[i]
                        pdf_text += pdf_page.getText("text") + " "  # "html"

                    self.write_to_file(pdf_text, doc_name, original_name=pdf_name)
                except:
                    print("skipping")
                    pass

            h = html2text.HTML2Text()
            h.ignore_links = True
            for html_name in glob.glob(self.top_dir + "**/*.html", recursive=True):
                try:
                    with open(html_name) as html_file:
                        html_txt = h.handle(html_file.read())

                    # print(html_txt)
                    html_txt = html_txt.split("=====================================================================================  \n|\n\n")[1:]
                    email_index = 0
                    for email in html_txt:
                        # print(email)
                        email_name = email.split("\n\nby")[0]
                        email_parts = email.split("---|---")[0].split("\n\nby")[-1].strip()
                        # print(email_parts)
                        email_author = email_parts.split(" - ")[0].strip()
                        email_date = email_parts.split(" - ")[1].split(", ", 1)[1]
                        # print(email_date)
                        email_date = str(datetime.datetime.strptime(email_date, "%B %d, %Y, %I:%M %p"))
                        # print(email_date)
                        email_content = email.split("---|---")[1].split("|",1)[1].strip()

                        doc_name = str(email_index)+"_"+email_name+"_"+email_author+'.txt'
                        # print(html_name)
                        # print(email_date)
                        self.write_to_file(email_content, doc_name, doc_date=email_date)

                        email_index += 1

                except:
                    print("skipping")
                    pass

            for docx_name in glob.glob(self.top_dir + "**/*.docx", recursive=True):
                try:
                    docx_txt = docx2txt.process(docx_name)
                    doc_name = docx_name.replace('.docx', '.txt').split("/")[-1]

                    self.write_to_file(docx_txt, doc_name, original_name=docx_name)
                except:
                    print("skipping")
                    pass

            for xlsx_name in glob.glob(self.top_dir + "**/*.xlsx", recursive=True):
                try:
                    xlsx = pd.read_excel(xlsx_name)
                    xlsx_txt = xlsx.to_string()

                    doc_name = xlsx_name.replace('.xlsx', '.txt').split("/")[-1]

                    self.write_to_file(xlsx_txt, doc_name, original_name=xlsx_name)
                except:
                    print("skipping")
                    pass

            with open(self.out_json_filepath, "w", encoding="utf-8") as docs_file:
                for txt_name in glob.glob(self.processed_dir + "*.txt"):
                    short_name = txt_name.replace(".txt", "").split("\\")[-1]

                    with open(txt_name, encoding="utf-8") as doc_txt_file:
                        docs_file.write("{\"id\": \"" + short_name + "\", \"text\": \"" + doc_txt_file.read().replace("\t", " ").replace("\\", "\\\\").replace("\n", "\\n").replace("\"", "\\\"") + "\"}\n")