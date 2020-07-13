# piazza-qa

This is an implementation for Piazza of the question-answering system described in the AIED 2020 paper [Exploring Automated Question Answering Methods for Teaching Assistance](https://rdcu.be/b5Aa2).

## Installation

Clone the repository.

```bash
git clone https://github.com/adamviola/piazza-qa.git
cd piazza-qa
```

Create a new conda environment with Python 3.6.10.

```bash
conda create --name piazza-qa python=3.6.10
```

Activate the conda environment and use pip to install the requirements.
```bash
conda activate piazza-qa
pip install -r requirements.txt 
```

Set up DrQA for development.

```bash
cd ./model/DrQA
python setup.py develop
cd ../..
```

Install CoreNLP. Select the defaults.

```bash
cd ./model/DrQA
chmod +x ./install_corenlp.sh
./install_corenlp.sh
cd ../..
```

Download the DrQA document reader multitask model. If the URL is broken, download the multitask model from [here](https://github.com/facebookresearch/DrQA#document-reader).

```bash
wget -P ./model/DrQA/data/reader "https://dl.fbaipublicfiles.com/drqa/multitask.mdl"
```

Download [this model checkpoint](https://drive.google.com/file/d/1loXHIBAIv3YcPPrS1aUv0QioU6MK6-oR/view) to the `./model` directory

Drop all course documents into the `./documents` directory and complete the configuration file, `./config.ini`.

Run start.py

```bash
python start.py
```

## License

[MIT](https://choosealicense.com/licenses/mit/) for everything outside of the DrQA folder. DrQA is BSD-licensed.
