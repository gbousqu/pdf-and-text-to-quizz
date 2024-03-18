# PDF to Quiz

## Important

this code is based on the project of Farid Bellame : https://github.com/fbellame/pdf-to-quizz

## Usage

Upload a multiple page PDF or give a text and generate a quiz.
Through a streamlit form, uou can :

- choose the number of questions generated for each "page" of the document (pdf or text)
- choose, create or modify the "context", i.e the extra exact instructions to pass to openAI
- choose the type of questions for all the quizz : MCQ with one correct option, MCQ with 2 or 3 exact answers, True/false

The UI is based on Streamlit

## Pre-requisite

You need an OpenAI API key from https://platform.openai.com/account/api-keys

Keep in mind this is not free BUT the with the usage of **gpt-3.5-turbo** it's not expensive at all unless you drop really big PDF (more than 100 pages).

![Open AI key](img/OPENAI-KEY.png)

Once you have your API key you can install it in your terminal like this:

```sh
export OPENAI_API_KEY=[Your-API-key]
```

## Instructions

To install:

```sh
pip install -r requirements.txt
```

## Run

To run:

```sh
streamlit run ui.py
```

To run on docker

```sh
docker build -t pdf-to-quizz .
docker run -e OPENAI_API_KEY=[your-api-key] -p 8501:8501 pdf-to-quizz
```
