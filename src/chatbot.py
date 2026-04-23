import os
import re
import requests
import numpy as np
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from openai import OpenAI
from playwright.sync_api import sync_playwright

# ==========================
# LOAD ENV VARIABLES
# ==========================

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")

if not API_KEY:
    raise ValueError("API key not found. Set OPENROUTER_API_KEY in .env")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ==========================
# SCRAPER (HYBRID)
# ==========================

def scrape_website(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9"
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.extract()

            text = soup.get_text(separator=" ")

            # ✅ Extract links
            links = [a["href"] for a in soup.find_all("a", href=True)]
            text += " " + " ".join(links)

            text = re.sub(r"\s+", " ", text)

            print(f"[Requests] Content length: {len(text)}")

            if len(text) > 500:
                return text.strip()

    except Exception as e:
        print(f"[Requests] Error: {e}")

    print("[Fallback] Switching to Playwright")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        text = soup.get_text(separator=" ")

        # ✅ Extract links again
        links = [a["href"] for a in soup.find_all("a", href=True)]
        text += " " + " ".join(links)

        text = re.sub(r"\s+", " ", text)

        print(f"[Playwright] Content length: {len(text)}")

        return text.strip()

    except Exception as e:
        print(f"[Playwright] Error: {e}")
        return ""

# ==========================
# TEXT PROCESSING
# ==========================

def chunk_text(text: str, chunk_size: int = 300):
    words = text.split()
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]

# ==========================
# RETRIEVAL
# ==========================

def get_relevant_chunks(chunks, query, top_k=15):
    try:
        query_lower = query.lower()

        # 🔥 force homepage for vague queries
        if "what" in query_lower and "this" in query_lower:
            return chunks[:5]

        filtered = [c for c in chunks if len(c.strip()) > 100]

        if not filtered:
            return chunks[:top_k]

        vectorizer = TfidfVectorizer().fit(filtered + [query])
        vectors = vectorizer.transform(filtered + [query])

        query_vec = vectors[-1]
        chunk_vecs = vectors[:-1]

        scores = (chunk_vecs * query_vec.T).toarray().flatten()

        top_indices = np.argsort(scores)[::-1][:top_k]
        selected_chunks = [filtered[i] for i in top_indices]

        # 🔥 stronger fallback
        selected_chunks.extend(chunks[:5])

        return list(dict.fromkeys(selected_chunks))

    except Exception as e:
        print(f"[Retrieval] Error: {e}")
        return chunks[:top_k]

# ==========================
# LINK EXTRACTION
# ==========================

def extract_links(chunks, query):
    q = query.lower()

    # ==========================
    # CONTACT (CLEAN + FILTERED)
    # ==========================
    if any(k in q for k in ["contact", "reach", "connect"]):
        emails = set()
        github = set()
        linkedin = set()
        phones = set()

        for chunk in chunks:
            # emails
            emails.update(re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', chunk))

            # phones
            phones.update(re.findall(r'\+?\d[\d\s\-]{8,}', chunk))

            # 🔥 GitHub profile ONLY (ignore repos)
            matches = re.findall(r'https?://github\.com/([A-Za-z0-9_-]+)', chunk)
            for m in matches:
                github.add(f"https://github.com/{m}")

            # 🔥 LinkedIn profile ONLY
            linkedin.update(
                re.findall(r'https?://www\.linkedin\.com/in/[^\s]+', chunk)
            )

        results = []

        # clean structured output (sorted for consistency)
        if emails:
            results.extend(sorted([f"Email: {e}" for e in emails]))

        if github:
            results.extend(sorted([f"GitHub: {g}" for g in github]))

        if linkedin:
            results.extend(sorted([f"LinkedIn: {l}" for l in linkedin]))

        if phones:
            results.extend(sorted([f"Phone: {p}" for p in phones]))

        return results

    # ==========================
    # GITHUB (ALL LINKS)
    # ==========================
    elif any(k in q for k in ["github", "repo", "code"]):
        pattern = r'https?://[^\s]*github[^\s]*'

    # ==========================
    # LINKEDIN
    # ==========================
    elif any(k in q for k in ["linkedin", "profile"]):
        pattern = r'https?://[^\s]*linkedin[^\s]*'

    # ==========================
    # EMAIL
    # ==========================
    elif any(k in q for k in ["email", "mail"]):
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'

    # ==========================
    # PHONE
    # ==========================
    elif any(k in q for k in ["phone", "number"]):
        pattern = r'\+?\d[\d\s\-]{8,}'

    else:
        return []

    # ==========================
    # DEFAULT EXTRACTION
    # ==========================
    results = []

    for chunk in chunks:
        results.extend(re.findall(pattern, chunk))

    return list(set(results))
# ==========================
# QUESTION HANDLING
# ==========================

def preprocess_question(question: str) -> str:
    q = question.lower().strip()

    # 🔥 fix common typo
    q = q.replace("si", "is")

    vague_phrases = [
        "what is this", "what is this site", "what is this website",
        "tell me about this", "explain this", "what does it do",
        "about this", "describe this", "overview", "summary"
    ]

    weak_inputs = ["?", "??", "???", "this", "it", "site", "page", "website"]

    if q in weak_inputs or any(p in q for p in vague_phrases):
        return "Explain clearly what this website is about."

    return question

# ==========================
# LLM CALL
# ==========================

def ask_gpt(context: str, question: str) -> str:
    try:
        if not context or len(context.strip()) < 50:
            return "Information not available on the website."

        prompt = f"""
You are a precise AI assistant.

Rules:
- Use ONLY the provided website content
- Do NOT use outside knowledge
- Do NOT guess

Formatting:
- Use bullet points when possible
- Keep answers short and clear

STRICT:
If answer not found → return EXACTLY:
"Information not available on the website."

Website Content:
{context}

Question:
{question}
"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"API Error: {e}"

# ==========================
# MAIN
# ==========================

def main():
    print("Web Context Chatbot")

    url = input("Enter website URL: ").strip()

    print("Scraping website...")
    text = scrape_website(url)

    if not text or len(text) < 200:
        print("Failed or insufficient content scraped.")
        return

    print("Processing content...")
    chunks = chunk_text(text)

    print("Chatbot ready. Type 'exit' to quit.")

    while True:
        query = input("You: ")

        if query.lower() == "exit":
            break

        extracted = extract_links(chunks, query)

        if extracted:
            print("\nBot:")
            for item in extracted:
                print("-", item)
            print()
            continue

        processed_query = preprocess_question(query)

        relevant_chunks = get_relevant_chunks(chunks, processed_query)

        context = " ".join(relevant_chunks)

        # ✅ FIXED fallback (NO streamlit)
        if len(context.strip()) < 150:
            context = " ".join(chunks[:10])

        answer = ask_gpt(context, processed_query)

        print("\nBot:")
        print(answer)
        print()

if __name__ == "__main__":
    main()