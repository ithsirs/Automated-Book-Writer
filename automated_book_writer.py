from playwright.sync_api import sync_playwright
import json, os
from datetime import datetime
from urllib.parse import urlparse, unquote
import ollama

# Scraping 

def extract_chapter_id(url):
    path = urlparse(url).path
    parts = [part for part in path.split("/") if part]
    return unquote("_".join(parts[-3:])).replace(" ", "_")

def scrape_chapter(url, chapter_id):
    raw_path = f"data/raw/{chapter_id}.json"
    screenshot_path = f"data/screenshots/{chapter_id}.png"

    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

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

        print(f"Scraped chapter saved to {raw_path}")
        browser.close()

    return raw_path

#  AI Writer 

def spin_text(text, model="llama3.1:8b", temperature=0.8):
    prompt = (
        "Rewrite the following historical fiction passage in a clearer, modern style "
        "while keeping the original meaning and tone:\n\n" + text
    )
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": "You are a skilled creative writer."},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": temperature}
    )
    return response['message']['content'].strip()

def run_writer(raw_path, chapter_id):
    with open(raw_path, "r", encoding="utf-8") as f:
        chapter = json.load(f)

    spun_text = spin_text(chapter["original_text"])
    chapter["spun_text"] = spun_text
    chapter["status"] = "spun"

    out_path = f"data/processed/spun/{chapter_id}_spun.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chapter, f, indent=4, ensure_ascii=False)

    print(f"Spun chapter saved to {out_path}")
    return out_path

# AI Reviewer


def review_text(original_text, spun_text, model="llama3.1:8b", temperature=0.8):
    system_prompt = "You are a professional editor and creative writing coach."
    user_prompt = (
        "An AI Writer has rewritten a chapter. As an AI Reviewer, you need to:\n"
        "1. Provide a refined version of the rewritten (spun) text.\n"
        "2. Write a short review report on how well the AI did in terms of clarity, tone, fluency, and originality.(Review Report:).\n\n"
        f"Original Text:\n{original_text}\n\n"
        f"Spun Text:\n{spun_text}"
    )

    stream = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=True,
        options={
            "temperature": temperature
        }
    )

    full_response = ""
    for chunk in stream:
        content = chunk['message']['content']
        print(content, end="", flush=True) 
        full_response += content

    print()  
    return full_response.strip()

def run_reviewer(spun_path, chapter_id):
    with open(spun_path, "r", encoding="utf-8") as f:
        chapter = json.load(f)

    review_response = review_text(chapter["original_text"], chapter["spun_text"])

    if "Review Report:" in review_response:
        reviewed_text, review_notes = review_response.split("Review Report:", 1)
    else:
        reviewed_text, review_notes = review_response, "N/A"

    chapter["reviewed_text"] = reviewed_text.strip()
    chapter["review_notes"] = review_notes.strip()
    chapter["status"] = "reviewed"

    out_path = f"data/processed/reviewed/{chapter_id}_reviewed.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chapter, f, indent=4, ensure_ascii=False)

    print(f"Reviewed chapter saved to {out_path}")

