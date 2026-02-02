import streamlit as st
from groq import Groq

st.write("Checking Groq Connection...")
client = Groq(api_key="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")

try:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say hello!"}]
    )
    st.success(f"Connection Successful: {completion.choices[0].message.content}")
except Exception as e:
    st.error(f"Connection Failed: {e}")
