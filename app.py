import os
import re
import sys
import urllib.parse
import json
import urllib.request
import requests
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import openai
import time
from bs4 import BeautifulSoup
from bs4.element import Comment
# from serpapi import GoogleSearch
from stackapi import StackAPI
from urllib.parse import urlencode
from flask import Flask, jsonify, request
from multiprocessing import Pool
from transformers import GPT2TokenizerFast
from concurrent.futures import ThreadPoolExecutor
# from serpapi import GoogleSearch


import streamlit_google_oauth as oauth

app = Flask(__name__)

client_id = os.environ['GOOGLE_CLIENT_ID']
client_secret = os.environ['GOOGLE_CLIENT_SECRET']
redirect_uri = os.environ['REDIRECT_URI']

openai.api_key = os.getenv("OPENAI_API_KEY")

SITE = StackAPI('stackoverflow', version='2.3', key='STACK_API_KEY', access_token='STACK_TOKEN')
SITE.max_pages=1
SITE.page_size=20
data = list()
fine_tune_file = open('fine_tune_SO.json', 'w') 


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
    # if element.parent.name in ['title', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts) 
    visible_text = " ".join(t.strip() for t in visible_texts)
    # print("\n\n\n Visible text ==== ", visible_text, "\n\n\n")
    return visible_text


def search_fix_SO(query, tag):
    query = urllib.parse.quote_plus(query)
    questions = SITE.fetch(f'search/advanced?order=desc&sort=relevance&q={query}')
    print(f'Google_query == search/advanced?order=desc&sort=relevance&q={query}')
    print(f"questions: {questions}")

    # if 'backoff' in questions:
    #     self.backoff = questions.get('backoff')
    #     self.quota_remaining = questions.get('quota_remaining')
    # else:
    #     self.backoff = 0

    question_answer = {}

    question_link=""
    question_tags=""

    for quest in questions['items'][:3]:

        # check if quest contains

        if 'title' not in quest or quest['is_answered'] == False:
            continue
        title = quest['title']
        print('Question :{0}'.format(title))
        question_id = quest['question_id']
        print('Question ID :{0}'.format(question_id))
        question_link = "https://stackoverflow.com/questions/"+str(question_id)
        question_tags = quest['tags']
        print("tags == ", question_tags)
        question_answer= {'question_title': title, 'question_id': question_id}
        top_answers = SITE.fetch('questions/' + str(question_id) + '/answers', order = 'desc', sort='votes',filter='withbody')
        
        # print("top_answers === ",top_answers)

        # if 'backoff' in top_answers:
        #     self.backoff = top_answers.get('backoff')
        #     self.quota_remaining = questions.get('quota_remaining')
        # else:
        #     self.backoff = 0

        question_answer['answers'] = []
        for top_answer in top_answers['items'][:3]:
            # print(f"top answer: {top_answer}")
            soup = BeautifulSoup(top_answer['body'], features="html.parser")
            top_answer_body = soup.get_text().replace("\"","\'")
            # print('Top answer body :{0}'.format(top_answer_body))
            question_answer['answers'].append({
                'answer_id': top_answer['answer_id'],
                'answer_body': top_answer_body
            })
        break
    return question_answer, question_tags, question_link

# TODO
def search_github(question, tag):
    return



def search_google_custom(query):
    params = {
        "key": "AIzaSyBoe003gU2DVkf0AOSe1hthkksvYqOTfyk",
        "cx": "227a7cec4600f4427",
        "q": query,
        "gl": "us",
        "hl": "en"
    }
    search_url = "https://www.googleapis.com/customsearch/v1?" + urlencode(params)
    search_results = requests.get(search_url, timeout=2)
    # print("Number of google search results  ----> ", search_results.json()["searchInformation"]["totalResults"])
    
    # if the size of search results is less than 3 (which means the query is probably bad), then call the compose_search_query function
    if int(search_results.json()["searchInformation"]["totalResults"]) < 3:
        query = compose_search_query(query)
        params = {
            "key": "AIzaSyBoe003gU2DVkf0AOSe1hthkksvYqOTfyk",
            "cx": "227a7cec4600f4427",
            "q": query,
            "gl": "us",
            "hl": "en"
        }
        search_url = "https://www.googleapis.com/customsearch/v1?" + urlencode(params)
        search_results = requests.get(search_url)

    results = search_results.json()
    global top_links 
    top_links = []
    for i in range(0, 3):
        try:    
            top_links.append(results["items"][i]["link"])
            # print("Snippet ===============> ", results["items"][i]["snippet"])
        except Exception as e:
            print(e)

    top_results = ""
    for link in top_links:
        print("link ===> ", link)
        req = Request(
            url=link,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        # domain = urlparse(link).netloc
        # print("domain ===> ", domain)
        # if domain != "stackoverflow.com":  # uncomment this line to remove stackoverflow from results
        if ".pdf" in link: # here add content-types to be excluded
            continue
        else:
            try:
                top_results += text_from_html(urlopen(req).read())
            except Exception as e:
                print(e)        
    return top_results, top_links





def search_google_serp(question):

    query = question 
    
    params = {
        "api_key": "83872a6da6494f4c3151cc74c05760a67e9de1551a05ceab42dc2a284ac55832",
        "device": "desktop",
        "engine": "google",
        "q": query,
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    top_links = []
    for i in range(0, 3):
        try:
            top_links.append(results["organic_results"][i]["link"])
        except Exception as e:
            print("Exception ---->",e)
    top_results = ""
    for link in top_links:
        # print("link ===> ", link)
        req = Request(
            url=link, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        domain = urlparse(link).netloc
        # print("domain ===> ", domain)
        if domain != "stackoverflow.com":
            try:
                top_results += text_from_html(urlopen(req).read())
            except Exception as e:
                print(e)    
    return top_results, top_links


def compose_search_query(question):

    prompt_issue_class = f"""The logs are: {user_introduced_question} 
    Does the question contain an issue description or does it just contain the error logs?\n\n"    
    """
    prompt_main_tech = f"""The issue description is the following:{user_introduced_question} 
    Answer in one word, what is the main technology involved in the question and what is it's version? 
    If the version is not explicitly mentioned in the issue description then leave it blank\n\n"
    """
    tech_and_version=openai_complete("text-davinci-003", prompt_main_tech)
    prompt_get_query = f"""The issue description is the following:{user_introduced_question} 
    Compose a Google query to find a solution to the issue\n\n"
    """
    google_query=openai_complete("text-davinci-003", prompt_get_query)

    print ("The search_query ==> ", google_query)
    return google_query.replace('"','')


def summarise_chunk(text_chunk):
    text_chunk=re.sub(' +', ' ', text_chunk)
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    number_of_tokens = len(tokenizer(text_chunk)['input_ids'])
    if number_of_tokens > 4097:
        print("number_of_tokens ==> ", number_of_tokens)
        print("\n\ntext_chunk ==> ", text_chunk)

    # prompt_summarise_chunk = f"""
    # Summarise the following text: {text_chunk}
    # Please summarise the text above, by emphasising the steps that may solve the issue described in the question. 
    # Please include any links or code snippets from the text in your summary. 
    # Please present the answer in bullet points whenever possible and each bullet point in a line."
    # """

    # prompt_summarise_chunk = f"""The issue description is:
    # {parsed_query['main_message']}
    # The text containing the solution is the following:
    # {text_chunk}
    # From the text above, how can I solve the issue described earlier? 
    # If the text above contains multiple solutions, please summarise the most relevant ones.
    # If the text above does not contain a solution, please leave the answer empty (don't say anything).
    # Please put code snippets and commands in markdown code blocks. 
    # \n\n
    # """

    prompt_summarise_chunk = f"""The issue description is:
    {parsed_query['main_message']}
    The following text may contain one of more proposed solutions to the issue above (solutions are usually separated with "|"):
    {text_chunk}
    Please summarise the best solution that seemed to solve the issue described earlier.
    Please keep the answer concise and to the point focusing mainly on commands and code snippets (not logs).
    If the text above does not contain a solution, please leave the answer empty (don't say anything).
    Please put code snippets and commands in markdown code blocks. 
    \n\n
    """

    print ("prompt_summarise_chunk =====> ", prompt_summarise_chunk)
  
    # print ("prompt =====> ", prompt_summarise_chunk)
    chunk_summary=""
    try:
        chunk_summary = openai_complete("text-davinci-003", prompt_summarise_chunk, temperature=0)
    except Exception as e:
        print(e)
    print("\n\nchunk_summary =====> ", chunk_summary)
    return chunk_summary

def summarise_answers(question, answers):
    # Calculate the number of tokens in the answers and split the answers into chunks of 2048 tokens
    chunk_size = 4097*3-250-200 # use this when question is not used in the prompt
    answers_chunks = [answers[i:i+chunk_size] for i in range(0, len(answers), chunk_size)]

    # # Use a Pool to process the chunks concurrently (legacy)
    # pool = Pool(4)                         
    # concise_answer_map=pool.map(summarise_chunk, answers_chunks)
    # print("\n\n\n\n\n\nconcise_answer_map =====> ", concise_answer_map)
    # pool.close()

    # Use a ThreadPoolExecutor to process the chunks concurrently
    with ThreadPoolExecutor() as executor:
        concise_answer_map = list(executor.map(summarise_chunk, answers_chunks))

    # Concatenate the results into a single string
    concise_answer_map = '\n'.join(concise_answer_map)
    print("\n\n\n\n\n\nconcise_answer_map =====> ", concise_answer_map)

    # Generate the prompt for the completion model
    prompt = f"""The issue description is: {question}\n
    A collection of possible solutions is:
    {str(concise_answer_map)}
    From the text above (possible solutions), summarise how to solve the issue in a few numbered bullet points (keep the same order as original text), make sure you give code snippets and commands if any. 
    If the issue is a bug, then identify and tell what version is impacted by this bug and tell if it is resolved or not. 
    Solution (fomatted in rich markdown text): 
    \n\n
    """
    # Use the OpenAI API to generate the summary
    # concise_answer_reduce=json.loads(
    #         openai_complete("text-davinci-003", prompt)
    #     )
    concise_answer_reduce = openai_complete("text-davinci-003", prompt)
    # print("concise_answer_reduce =====> ", concise_answer_reduce)   
    return concise_answer_reduce


def clean_answers(answers):
    # @TODO
    return 

def ask_follow_up(question, answer):
    prompt = f"""The question is: 
    {question}
    The answer is: 
    {answer}
    Please ask 3 follow up questions."
    """
    Follow_up_questions=openai_complete("text-davinci-003", prompt)
    return Follow_up_questions

def openai_complete(model, prompt, max_tokens=250, temperature=0, top_p=1, best_of=1, frequency_penalty=0, presence_penalty=0, stop=["#", ";"]):
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        best_of=best_of,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=stop
    )
    print("response ========>", response)
    completetion = response.choices[0].text
    # if completion does not end with a stop token, then add a stop token - this is to remediate a bug in the API 
    # see example of response https://stackoverflow.com/questions/55638597/kafka-stream-subscription-error-invalid-version 
    # openai API does not correctly escape the double quotes in the response
    if completetion[-1] not in ["}"]:
        completetion = completetion + "\"}"
    print("response.choices[0].text =====> ", completetion)
    return completetion

def sem_parse(error_message):
    prompt = f"""
    {error_message}\n\nThe text above represent log messages. 
    If these logs describe an issue, then extract the following information from the logs, in json format. Make sure you escape all double quotes in the json output:
    
    Technology: the technology that generated the error 
    
    Stack: the likely stack is composed of the following technologies
    
    code_command: the code or command that generated the error (if not present in the logs, then value is N/A)
    
    main_message: the main error or warning message 
    
    common_causes: the common causes for this error message (in a list of strings)
    
    best_practices: the best practices to troubleshoot this issue (in a list of strings)
    
    google_query: a google search query that may help to troubleshoot this issue 
    \n\n
    """
    
    parsed_query=json.loads(
            openai_complete("text-davinci-003", prompt)
        )
    # print ("google_query =====> ", parsed_query["google_query"])
    # print ("parsed_query == ", parsed_query)
    return parsed_query

@app.route("/")
def hello():
    return "Hello World!"

# @TODO: 
@app.route("/semparse", methods=["GET", 'POST'])
def get_semparse():
    dict = request.form
    query = dict["query"]
    query = query.replace("%", " ")
    re.sub(' +', ' ', query)
    # print("query ==== ", query)
    global user_introduced_question 
    user_introduced_question = query
    global parsed_query
    parsed_query = sem_parse(query)
    # print("parsed_query ==== ", parsed_query)
    return parsed_query

@app.route("/answers", methods=["GET", 'POST'])
def get_answer():
    # @TODO: need an algorithm to pick or the other or combine both
    google_query=user_introduced_question 
    # google_query=parsed_query["google_query"]  

    start_time = time.time()
    answers_google, google_links = search_google_custom(google_query)
    print("--- %s seconds ---" % (time.time() - start_time))

    # answers = answers_SO + answers_googles
    start_time = time.time()
    concise_solution = summarise_answers(user_introduced_question, answers_google)
    print("--- %s seconds ---" % (time.time() - start_time))

    print("concise_solution == ", concise_solution)

    # @TODO: put concise_solution and google_links in a single json then return it
    Sources=""
    for source in google_links:
        Sources+=source+"\n\n"

    return concise_solution+"\n\nSources:\n\n"+Sources

# main function to run the flask app
def main():
    app.run(debug=True, host='0.0.0.0', port=8080) 
    
if __name__ == '__main__':
    main()
