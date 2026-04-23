import streamlit as st
from urllib.parse import urlparse
from src.chatbot import (
    scrape_website,
    chunk_text,
    get_relevant_chunks,
    ask_gpt,
    preprocess_question,
    extract_links
)

st.set_page_config(page_title="WebContextAI", layout="centered")

# ==========================
# HEADER
# ==========================

st.title("WebContextAI Chatbot")
st.markdown("Ask questions based on website content")

# ==========================
# SESSION STATE
# ==========================

if "chunks" not in st.session_state:
    st.session_state.chunks = None

if "processed" not in st.session_state:
    st.session_state.processed = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==========================
# HELPERS
# ==========================

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"] and parsed.netloc != ""
    except:
        return False

def is_extraction_query(q):
    q = q.lower()
    intent_words = [
        "contact", "reach", "connect", "touch",
        "email", "mail", "phone", "number",
        "github", "repo", "code",
        "linkedin", "profile",
        "social", "links"
    ]
    return any(word in q for word in intent_words)

# ==========================
# URL INPUT
# ==========================

url = st.text_input("Enter Website URL")

if st.button("Process Website"):

    if not url.strip() or not is_valid_url(url):
        st.warning("Please enter a valid URL (include http/https).")

    else:
        st.session_state.chunks = None
        st.session_state.processed = False
        st.session_state.chat_history = []

        with st.spinner("Scraping website..."):

            text = scrape_website(url)

            if not text:
                st.error("Failed to fetch website content.")
                st.stop()

            if len(text) < 200:
                st.error("Not enough content found.")
                st.stop()

            st.session_state.chunks = chunk_text(text)
            st.session_state.processed = True

        st.success("Website processed successfully.")

# ==========================
# CHAT INPUT
# ==========================

if st.session_state.processed:

    st.divider()

    query = st.chat_input("Ask your question")

    if query and query.strip():

        with st.spinner("Thinking..."):

            extracted = []
            is_extract = is_extraction_query(query)

            # ==========================
            # STEP 1: EXTRACTION
            # ==========================

            if is_extract:
                extracted = extract_links(st.session_state.chunks, query)

                if extracted:
                    answer = "\n".join([f"- {item}" for item in extracted])
                else:
                    answer = "Information not available on the website."

            # ==========================
            # STEP 2: RAG FLOW
            # ==========================

            else:
                processed_query = preprocess_question(query)

                relevant_chunks = get_relevant_chunks(
                    st.session_state.chunks,
                    processed_query,
                    top_k=15
                )

                if not relevant_chunks:
                    relevant_chunks = st.session_state.chunks[:5]

                context = " ".join(relevant_chunks)

                # 🔥 improved fallback (critical fix)
                if len(context.strip()) < 150:
                    context = " ".join(st.session_state.chunks[:10])

                answer = ask_gpt(context, processed_query)

        # ==========================
        # SAVE CHAT
        # ==========================

        st.session_state.chat_history.append({
            "question": query,
            "answer": answer
        })

        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history.pop(0)

    # ==========================
    # DISPLAY CHAT
    # ==========================

    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(chat["question"])

        with st.chat_message("assistant"):
            st.markdown(chat["answer"])

else:
    st.info("Enter a URL and click 'Process Website' to begin.")