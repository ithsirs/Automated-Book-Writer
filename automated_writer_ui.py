import streamlit as st
from playwright.sync_api import sync_playwright
import ollama
from urllib.parse import urlparse, unquote
import os, json
from datetime import datetime

import asyncio
import sys

st.set_page_config(page_title=" Automated Book Publication", layout="wide")
st.title("📚 Automated Book Publication")

def extract_chapter_id(url):
    path = urlparse(url).path
    parts = [part for part in path.split("/") if part]
    return unquote("_".join(parts[-3:])).replace(" ", "_")

def scrape_chapter(url, chapter_id):
    raw_path = f"data/raw/{chapter_id}.json"
    screenshot_path = f"data/screenshots/{chapter_id}.png"
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)


    if sys.platform.startswith('win') and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector("div.prp-pages-output")

            title = page.title()
            paragraphs = page.eval_on_selector_all(
                "div.prp-pages-output p",
                "elements => elements.map(p => p.innerText.trim()).filter(Boolean)"
            )
            full_text = "\n\n".join(paragraphs)

            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()

        data = {
            "chapter_id": chapter_id,
            "title": title,
            "url": url,
            "scraped_on": datetime.now().isoformat(),
            "original_text": full_text,
            "status": "raw"
        }

        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return data, raw_path, screenshot_path
    
def load_chapter(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_spun_chapter(data, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)    

def spin_text(text, model="llama3.1:8b"):
    # prompt = (
    #     "Rewrite the following passage in a clearer, modern literary style, without shortening or summarizing it.\n"
    #     "Keep all original story elements, events, and dialogue intact. Your goal is to rephrase the text for better readability "
    #     "while preserving the full length, tone, and narrative flow of the original.\n\n"
    #     "Do not omit any parts. Ensure the rewritten version feels contemporary yet faithful to the original.\n\n"
    #     "Now rewrite the following passage:\n\n" + text
    # )
    prompt = (
        "Rewrite the following historical fiction passage in a modern style, "
        "while preserving the original content, meaning ,and tone:\n\n" + text
    )
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": "You are a skilled creative writer."},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0.8}
    )
    return response['message']['content'].strip()
def run_writer(json_in="data/raw/book1_chapter1.json", json_out="data/processed/spun/book1_chapter1_spun.json"):
    chapter = load_chapter(json_in)
    original = chapter["original_text"]

    spun_text = spin_text(original)
    chapter["spun_text"] = spun_text
    chapter["status"] = "spun"

    os.makedirs(os.path.dirname(json_out), exist_ok=True)
    save_spun_chapter(chapter, json_out)

    print(f"Spun text saved to {json_out}")

def review_text(original, spun, model="llama3.1:8b"):
    prompt = (
        "An AI Writer has rewritten a chapter. As an AI Reviewer, you need to:\n"
        "1. Provide a refined version of the rewritten (spun) text.\n"
        "2. Write a short review report on how well the AI did in terms of clarity, tone, fluency, and originality.(Review Report:).\n\n"
        f"Original Text:\n{original}\n\n"
        f"Spun Text:\n{spun}\n\n"
    )


    stream = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": "You are a professional editor and creative writing coach."},
            {"role": "user", "content": prompt}
        ],
        stream=True,
        options={"temperature": 0.8}
    )

    full_response = ""
    for chunk in stream:
        full_response += chunk['message']['content']
    return full_response.strip()

# ------------- UI Flow -------------

url = st.text_input("📥 Enter Wikisource Chapter URL")

if st.button("🔁 Run Full Pipeline"):
    if not url.strip():
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Scraping chapter..."):
            chapter_id = extract_chapter_id(url)
            chapter_data, raw_path, screenshot_path = scrape_chapter(url, chapter_id)
        st.success("✅ Scraping complete!")

        st.subheader("📘 Chapter Title:")
        st.markdown(f"**{chapter_data['title']}**")

        st.subheader("📖 Original Text")
        st.text_area("Original", chapter_data["original_text"], height=300)

        with st.spinner("✍️ Spinning chapter using LLM..."):
            spun = spin_text(chapter_data["original_text"])
            chapter_data["spun_text"] = spun
            chapter_data["status"] = "spun"
        st.success("✅ Spinning complete!")
        spun_path = f"data/processed/spun{chapter_id}_spun.json"
        os.makedirs(os.path.dirname(spun_path), exist_ok=True)
        with open(spun_path, "w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=4, ensure_ascii=False)

        st.success(f"Spun chapter saved to `{spun_path}`")
        st.subheader("📝 Spun Text")
        st.text_area("Spun", spun, height=300)

        with st.spinner("🧐 Reviewing spun version..."):
            reviewed = review_text(chapter_data["original_text"], spun)
        st.success("✅ Review complete!")

        if "Review Report:" in reviewed:
            reviewed_text, review_notes = reviewed.split("Review Report:", 1)
        else:
            reviewed_text, review_notes = reviewed, "N/A"

        chapter_data["reviewed_text"] = reviewed_text.strip()
        chapter_data["review_notes"] = review_notes.strip()
        chapter_data["status"] = "reviewed"

        st.subheader("✅ Reviewed Text")
        st.text_area("Reviewed Text", reviewed_text.strip(), height=300)
        st.subheader("📋 Review Report")
        st.text_area("Review Notes", review_notes.strip(), height=150)

        reviewed_path = f"data/processed/reviewed/{chapter_id}_reviewed.json"
        os.makedirs(os.path.dirname(reviewed_path), exist_ok=True)
        with open(reviewed_path, "w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=4, ensure_ascii=False)

        st.success(f"Final reviewed chapter saved to `{reviewed_path}`")

        with open(reviewed_path, "rb") as f:
            st.download_button(
                label="Download Final JSON",
                data=f,
                file_name=os.path.basename(reviewed_path),
                mime="application/json"
            )
