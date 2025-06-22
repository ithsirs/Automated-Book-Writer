from automated_book_writer import scrape_chapter, extract_chapter_id
from automated_book_writer import run_writer, run_reviewer


if __name__ == "__main__":
    url = input("Enter the Wikisource chapter URL: ").strip()
    if url:
        chapter_id = extract_chapter_id(url)
        raw_path = scrape_chapter(url, chapter_id)
        spun_path = run_writer(raw_path, chapter_id)
        run_reviewer(spun_path, chapter_id)
    else:
        print(" No URL provided.")