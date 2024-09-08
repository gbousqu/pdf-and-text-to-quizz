import streamlit as st

# def check_password():
#     """Returns `True` if the user had the correct password."""

#     def password_entered():
#         """Checks whether a password entered by the user is correct."""
#         if st.session_state["password"] == st.secrets["password"]:
#             st.session_state["password_correct"] = True
#             del st.session_state["password"]  # don't store password
#         else:
#             st.session_state["password_correct"] = False

#     if "password_correct" not in st.session_state:
#         # First run, show input for password.
#         st.text_input(
#             "Password", type="password", on_change=password_entered, key="password"
#         )
#         return False
#     elif not st.session_state["password_correct"]:
#         # Password not correct, show input + error.
#         st.text_input(
#             "Password", type="password", on_change=password_entered, key="password"
#         )
#         st.error("😕 Password incorrect")
#         return False
#     else:
#         # Password correct.
#         return True
    
def transform(input_dict):
    import streamlit as st
    type_question = st.session_state['type_question']
    new_list = []
    # print(f"\nType de question: {type_question}")
    # print(f"\nInput list: {input_dict}")
    
    for i in range(1, 11):
        question_key = f'question{i}'
        if question_key in input_dict:
            question_dict = {}
            question_dict['question'] = input_dict[question_key]
            if type_question == "Vrai/Faux":
                question_dict['reponse'] = input_dict.get(f'reponse{i}', 'N/A')
                question_dict['explication'] = input_dict.get(f'explication{i}', 'N/A')
            else:
                question_dict['A'] = input_dict.get(f'A_{i}', 'N/A')
                question_dict['B'] = input_dict.get(f'B_{i}', 'N/A')
                question_dict['C'] = input_dict.get(f'C_{i}', 'N/A')
                question_dict['D'] = input_dict.get(f'D_{i}', 'N/A')
                question_dict['reponse'] = input_dict.get(f'reponse{i}', 'N/A')
            new_list.append(question_dict)
            # print(f"\nAppended question_dict: {question_dict}")
    
    # print(f"\nTransformed list: {new_list}")
    return new_list