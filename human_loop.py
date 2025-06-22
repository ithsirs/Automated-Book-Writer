import streamlit as st
import json
import os
from datetime import datetime

# Load reviewed JSON
def load_chapter(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Save finalized or reviewed version
def save_chapter(data, comments, final_text):
    is_final = comments.strip().lower() == "final"
    output_dir = "data/processed/final" if is_final else "data/processed/reviewed"
    os.makedirs(output_dir, exist_ok=True)

    data["final_text"] = final_text.strip()
    data["finalized_on"] = datetime.now().isoformat()
    data["human_comments"] = comments
    data["status"] = "final" if is_final else "reviewed"

    filename = f"{data['chapter_id']}_{'final' if is_final else 'reviewed'}.json"
    save_path = os.path.join(output_dir, filename)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return save_path, is_final

# Streamlit App
st.set_page_config(page_title="Chapter Editor", layout="wide")
st.title(" Human-in-the-Loop Chapter Editor")

# Upload JSON file
json_file = st.file_uploader("Upload reviewed chapter JSON", type=["json"])

if json_file:
    chapter_data = json.load(json_file)

    st.subheader("Chapter Metadata")
    st.write(f"Title: {chapter_data['title']}")
    st.write(f"Status: {chapter_data['status']}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original Text")
        st.text_area("Original", chapter_data.get("original_text", ""), height=300)

        st.subheader("Spun Text")
        st.text_area("Spun", chapter_data.get("spun_text", ""), height=300)

    with col2:
        st.subheader("AI Reviewed Text")
        reviewed = st.text_area("Reviewed Text (editable)", chapter_data.get("reviewed_text", ""), height=300)

        st.subheader("Review Notes")
        st.text_area("AI Review Notes", chapter_data.get("review_notes", ""), height=150)

        st.subheader("Your Feedback")
        comments = st.text_area("Editor Comments:'final'for saving the final version", "", height=150)

    if st.button("Finalize and Save"):
        path, is_final = save_chapter(chapter_data, comments, reviewed)
        if is_final:
            st.success(f"Finalized chapter saved to: {path}")
        else:
            st.info(f"Chapter saved for further review at: {path}")
