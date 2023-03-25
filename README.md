# Concisefix
Stackoverflow+Google combo is great for troubleshooting, but has many limitations, including:
- By copying only part of your error logs, you may miss important keywords that impact the quality of Google search results
- Cleaning the query might remove key parameters that could impact the quality of search results, in addition to being an annoying manual task
- You could spend hours reading and trying solutions from Stackoverflow and forums

Concisefix is a troubleshooting search engine, where you can drop your error logs, as is, without cleaning or cut, and get a summary of the most relevant answers on the web. Benefits of Concisefix include:
- No hallucinations since it is hooked to Google
- Cites sources
- Larger query size than Google search
- Robust to bad log formats etc

Read more details here: https://medium.com/p/520e557bdefa/edit

If you find this repo useful or cool, please give us a star ⭐️  :D

# Get started
1. Clone this repo
2. Install requirements 
```
pip3 install -r requirements
```
3. Start the API
```
python3 concisefix/app.py
```
4. Start the UI
```
streamlit run concisefix/streamlit_ui.py
```

# Be careful
The summarisation function is miltithreaded which may uses a large number of tokens if the Google query returns a large content 

# Next steps
If someone can clean the code using LangChain or LlamaIndex, that would be nice 

# Support
Open an issue, a PR or DM on twitter @hadiazouni

# License
Just do whatever with the code 
