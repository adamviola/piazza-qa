import fitz
import glob
import os
import shutil
import datetime
import numpy as np

import pandas as pd
import docx2txt
import html2text

top_dir = "./documents/"  # directory from which to recursively search downward for documents
processed_dir = "./data/documents/"  # directory where preprocessed files will be stored
out_json_filepath = "./data/docs.json"  # this is the main output from this script, used in the next step of database creation
processed_documents_filepath = "./data/processed_documents.txt" # file containing the filenames and last modified timestamps of the previously processed documents

GROUP_LENGTH = 220  # character cutoff for a new paragraph

def write_to_file(txt, doc_name, doc_date=None, original_name=None, post_subject=None):
    assert doc_date is not None or original_name is not None
    pars = [txt]  ####split_to_paragraphs(txt)

    i = 0
    for par in pars:
        if post_subject is not None:
            par = post_subject + ".\t" + par

        doc_name_temp = doc_name.replace(".txt", "_" + str(i) + ".txt")
        new_filename = processed_dir + doc_name_temp

        with open(new_filename, "wb") as txt_file:
            txt_file.write(par.encode('utf-8', 'ignore'))

        i += 1

def process_documents():
    """Processes emails (html), pdf, docx, xlsx, and txt files for DrQA use

    This function maintains a list of previously processed files and their
    last modification timestamps. If any change is detected, the files are
    converted to text and built into a json file for DrQA.

    Returns:
        True if the document set changed and processing completed.
        False if the document set has not changed.
    """

    # Read filenames and last modified timestamp of last processed documents
    processed_documents = None
    with open(processed_documents_filepath, 'r') as f:
        processed_documents = f.readlines()

    # Read filenames and last modified timestamp of current documents
    documents = []
    for filepath in glob.glob(top_dir + "**/*.*", recursive=True):
        documents.append(filepath + ' ' + str(os.path.getmtime(filepath)) + '\n')

    # Skip processing if documents haven't changed
    if processed_documents == documents:
        return False

    # Convert pdf files to txt
    for pdf_name in glob.glob(top_dir + "**/*.pdf", recursive=True):
        try:
            pdf = fitz.open(pdf_name)

            doc_name = pdf_name.replace('.pdf', '.txt').split("/")[-1]

            pdf_text = ""
            for i in range(pdf.pageCount):
                pdf_page = pdf[i]
                pdf_text += pdf_page.getText("text") + " "  # "html"

            write_to_file(pdf_text, doc_name, original_name=pdf_name)
        except:
            pass

    # Convert html files (emails) to txt
    h = html2text.HTML2Text()
    h.ignore_links = True
    for html_name in glob.glob(top_dir + "**/*.html", recursive=True):
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
                write_to_file(email_content, doc_name, doc_date=email_date)

                email_index += 1

        except:
            pass

    # Convert docx files to txt
    for docx_name in glob.glob(top_dir + "**/*.docx", recursive=True):
        try:
            docx_txt = docx2txt.process(docx_name)
            doc_name = docx_name.replace('.docx', '.txt').split("/")[-1]

            write_to_file(docx_txt, doc_name, original_name=docx_name)
        except:
            pass

    # Convert xlsx files to txt
    for xlsx_name in glob.glob(top_dir + "**/*.xlsx", recursive=True):
        try:
            xlsx = pd.read_excel(xlsx_name)
            xlsx_txt = xlsx.to_string()

            doc_name = xlsx_name.replace('.xlsx', '.txt').split("/")[-1]

            write_to_file(xlsx_txt, doc_name, original_name=xlsx_name)
        except:
            pass

    # Include txt documents in output
    for txt_name in glob.glob(top_dir + "**/*.txt", recursive=True):
        shutil.copy(txt_name, processed_dir)

    # Read all output txt files and build them into a json for database creation
    with open(out_json_filepath, "w", encoding="utf-8") as docs_file:
        for txt_name in glob.glob(processed_dir + "*.txt"):
            short_name = txt_name.replace(".txt", "").split("\\")[-1]

            with open(txt_name, encoding="utf-8") as doc_txt_file:
                docs_file.write("{\"id\": \"" + short_name + "\", \"text\": \"" + doc_txt_file.read().replace("\t", " ").replace("\\", "\\\\").replace("\n", "\\n").replace("\"", "\\\"") + "\"}\n")

    # Clear out temporary txt files
    for txt_name in glob.glob(processed_dir + "**/*.txt", recursive=True):
        os.remove(txt_name)

    # Save filenames and last modified timestamps of processed documents
    with open(processed_documents_filepath, 'w') as f:
        f.writelines(documents)

    return True