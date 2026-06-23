import google.generativeai as genai
import streamlit as st

# -----------------------------------
# Configure Gemini
# -----------------------------------

genai.configure(api_key = st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# -----------------------------------
# AI Response Function
# -----------------------------------

def ask_copilot(question, report):

    prompt = f"""
You are an intelligent traffic management officer.

Current Incident Details:

Impact Class:
{report['Impact Class']}

Delay Seconds:
{report['Delay Seconds']}

Affected Roads:
{report['Affected Roads']}

Critical Junctions:
{report['Critical Junctions']}

Police Deployment:
{report['Police Deployment']}

Route Changed:
{report['Route Changed']}

Recommendation:
{report['Recommendation']}

User Question:
{question}

Provide professional operational guidance.
"""

    response = model.generate_content(
        prompt
    )

    return response.text