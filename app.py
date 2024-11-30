# -*- coding: utf-8 -*-
"""Codebase_RAG_Completed.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/github/team-headstart/CodebaseRAG/blob/main/Codebase_RAG_Completed.ipynb

![Img](https://app.theheadstarter.com/static/hs-logo-opengraph.png)

# Headstarter Codebase RAG Project

![Screenshot 2024-11-25 at 7 12 58 PM](https://github.com/user-attachments/assets/0bd67cf0-43d5-46d2-879c-a752cae4c8e3)

# Install Necessary Libraries
"""




from sklearn.metrics.pairwise import cosine_similarity

import tempfile

from dotenv import load_dotenv
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
# modules import
from modules.clone_repository import clone_repository
from modules.embeddings import get_huggingface_embeddings
from modules.get_files_content import get_main_files_content
from modules.perform_rag import perform_rag
from openai import OpenAI
import os
from pinecone import Pinecone
# from pinecone import IndexSpec
from pathlib import Path
load_dotenv()

# Access the API keys
pinecone_api_key = os.getenv("PINECONE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

path = clone_repository("https://github.com/CoderAgent/SecureAgent")

print(path)




file_content = get_main_files_content(path)

file_content





"""# Setting up Pinecone
**1. Create an account on [Pinecone.io](https://app.pinecone.io/)**

**2. Create a new index called "codebase-rag" and set the dimensions to 768. Leave the rest of the settings as they are.**

![Screenshot 2024-11-24 at 10 58 50 PM](https://github.com/user-attachments/assets/f5fda046-4087-432a-a8c2-86e061005238)



**3. Create an API Key for Pinecone**

![Screenshot 2024-11-24 at 10 44 37 PM](https://github.com/user-attachments/assets/e7feacc6-2bd1-472a-82e5-659f65624a88)


**4. Store your Pinecone API Key within Google Colab's secrets section, and then enable access to it (see the blue checkmark)**

![Screenshot 2024-11-24 at 10 45 25 PM](https://github.com/user-attachments/assets/eaf73083-0b5f-4d17-9e0c-eab84f91b0bc)


"""

# Set the PINECONE_API_KEY as an environment variable
# pinecone_api_key = userdata.get("PINECONE_API_KEY")
os.environ['PINECONE_API_KEY'] = pinecone_api_key

# Initialize Pinecone
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"], environment="us-west1-gcp")



# Connect to your Pinecone index
pinecone_index = pc.Index("codebase-rag")
stats = pinecone_index.describe_index_stats()
print(f"stats is {stats}")

vectorstore = PineconeVectorStore(index_name="codebase-rag", embedding=HuggingFaceEmbeddings())

documents = []

for file in file_content:
    doc = Document(
        page_content=f"{file['name']}\n{file['content']}",
        metadata={"source": file['name']}
    )

    documents.append(doc)


vectorstore = PineconeVectorStore.from_documents(
    documents=documents,
    embedding=HuggingFaceEmbeddings(),
    index_name="codebase-rag",
    namespace="https://github.com/CoderAgent/SecureAgent"
)



"""# Perform RAG

1. Get your Groq API Key [here](https://console.groq.com/keys)

2. Paste your Groq API Key into your Google Colab secrets, and make sure to enable permissions for it

![Screenshot 2024-11-25 at 12 00 16 AM](https://github.com/user-attachments/assets/e5525d29-bca6-4dbd-892b-cc770a6b281d)

"""

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=groq_api_key
)

query = "How are python files parsed?"

raw_query_embedding = get_huggingface_embeddings(query)

raw_query_embedding

# Feel free to change the "top_k" parameter to be a higher or lower number
top_matches = pinecone_index.query(vector=raw_query_embedding.tolist(), top_k=5, include_metadata=True, namespace="https://github.com/CoderAgent/SecureAgent")

top_matches

contexts = [item['metadata']['text'] for item in top_matches['matches']]

contexts

augmented_query = "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[ : 10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query

print(augmented_query)

system_prompt = f"""You are a Senior Software Engineer, specializing in TypeScript.

Answer any questions I have about the codebase, based on the code provided. Always consider all of the context provided when forming a response.
"""

llm_response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": augmented_query}
    ]
)

response = llm_response.choices[0].message.content

response





response = perform_rag("How is the javascript parser used?", pinecone_index, client)

print(response)

"""# Web APP Chatbot

"""



# Commented out IPython magic to ensure Python compatibility.

import streamlit as st

# Import your RAG function
# from your_rag_module import perform_rag  # Replace with the correct module name

# Streamlit App Title
st.title("Codebase Chatbot")
st.write("Ask questions about your codebase, and I'll fetch the best answers using Retrieval-Augmented Generation (RAG).")

# User Input
query = st.text_input("Enter your question:")

# Button to submit query
if st.button("Submit"):
    if query:
        with st.spinner("Fetching the answer..."):
            # Call your RAG function
            response = perform_rag(query, pinecone_index, client)
            st.write("### Answer:")
            st.write(response)
    else:
        st.warning("Please enter a question!")

