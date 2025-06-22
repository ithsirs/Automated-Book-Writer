import streamlit as st
import json
import os
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

#Setup ChromaDB
client = chromadb.PersistentClient(path="chroma_store")
collection = client.get_or_create_collection(name="chapter_versions")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


#  Utility Functions
def add_final_chapter_to_chroma(data):
    chapter_id = data["chapter_id"]
    text = data["final_text"]
    metadata = {
        "title": data["title"],
        "finalized_on": data.get("finalized_on", ""),
        "comments": data.get("human_comments", ""),
        "url": data["url"]
    }

    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[chapter_id]
    )
    return chapter_id


def search_chapters_exact(query_text, top_k=5):
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k
    )

    result_list = []
    for doc, meta, score in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        result_list.append({
            "excerpt": doc,
            "title": meta.get("title", ""),
            "finalized_on": meta.get("finalized_on", ""),
            "comments": meta.get("comments", ""),
            "url": meta.get("url", ""),
            "similarity": round(1 - score, 4)
        })

    return result_list


#Streamlit UI
st.set_page_config(page_title="Chapter Manager", layout="wide")
st.title("📚 Final Chapter Manager ")

tab1, tab2 = st.tabs(["📄 Upload & Store", "🔍 Exact Search"])

#Tab 1: Upload & Store
with tab1:
    st.header(" Upload Finalized Chapter JSON")

    uploaded_file = st.file_uploader("Upload a final chapter `.json` file", type="json")

    if uploaded_file:
        try:
            json_data = json.load(uploaded_file)
            chapter_id = add_final_chapter_to_chroma(json_data)
            st.success(f" Chapter `{chapter_id}` stored in ChromaDB successfully!")
        except Exception as e:
            st.error(f"Error: {e}")

#Tab 2: Exact Search
with tab2:
    st.header("🔍Chapter Search ")

    query = st.text_input("Enter exact chapter ID, title, or keywords:")
    top_k = st.slider("How many top results?", 1, 10, 3)

    if query:
        with st.spinner("Searching..."):
            results = search_chapters_exact(query, top_k)

        if not results:
            st.warning("No chapters found.")
        else:
            st.success("Results found:")
            for i, res in enumerate(results, 1):
                st.subheader(f" Result {i}: {res['title']}")
                st.write(f"**Similarity:** {res['similarity']}")
                st.write(f"**Finalized On:** {res.get('finalized_on', '')}")
                st.write(f"**Comments:** {res.get('comments', '')}")
                st.markdown(f"**Excerpt:**\n> {res['excerpt']}")
                if res.get("url"):
                    st.markdown(f"🔗 [Source]({res['url']})")
                st.markdown("---")