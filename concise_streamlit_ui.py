import requests
import streamlit as st

#  make it main to use the streamlit UI 
def main():    
    # this was outside the main function, moved here for cleaner code
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.title('Concise')
    #st.set_page_config(page_title='Better than Stackoverflow')
    issue_text = st.text_area("Describe your issue, or copy paste error logs. ", value="", height=160)
    col1, col2, col3, col4, col5, col6 = st.columns([3,4,3,3,3,3])

    m = st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #0099ff;
            color:#ffffff;
        }
        
        </style>""", unsafe_allow_html=True)

    concise_solution=""

    api_end_point = "http://localhost:8080/answers"

    query = { "query": issue_text }

    if st.button("Find a fix", key="search_fix", help=None, on_click=None, args=None, kwargs=None, disabled=False):
        st.write("The most relevant solutions:")
        concise_solution = requests.post(api_end_point, data=query).text
        st.write(concise_solution) 

if __name__ == '__main__':
    main()
