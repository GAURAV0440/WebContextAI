# 🌐 WebContextAI Chatbot

A smart chatbot that can **read any website and answer questions based on its content**.

This project combines **web scraping + AI (GPT via OpenRouter)** to create a system that understands website data and responds accurately — just like a human reading the page.

---

## 🚀 What This Project Does

- Takes a **website URL**
- Extracts content from the website (even JavaScript-heavy sites)
- Understands the content
- Lets users **ask questions**
- Gives answers **only based on that website**

---

## 🎯 Problem We Solved

Most chatbots:
- ❌ Use general knowledge (not website-specific)
- ❌ Miss hidden data (like GitHub links behind buttons)
- ❌ Fail on modern JavaScript websites

### Our Solution:
We built a chatbot that:
- ✅ Works on **real websites**
- ✅ Extracts **hidden links (GitHub, LinkedIn, Email, etc.)**
- ✅ Handles **JavaScript-heavy sites using Playwright**
- ✅ Answers strictly from website content (no hallucination)

---

## 🧠 How It Works (Step-by-Step)

### 1. Web Scraping
- First tries using **Requests + BeautifulSoup**
- If content is too small → switches to **Playwright (browser automation)**

👉 This ensures **maximum content extraction**

---

### 2. Data Processing
- Extracted text is split into **small chunks**
- This helps in better understanding and retrieval

---

### 3. Smart Retrieval (TF-IDF)
- Uses **TF-IDF (Term Frequency–Inverse Document Frequency)**
- Finds the most relevant parts of the website for each question

---

### 4. AI Answer Generation
- Uses **GPT via OpenRouter API**
- Sends only relevant content (not entire website)
- Ensures:
  - ✅ Accurate answers
  - ❌ No hallucination
  - ❌ No external knowledge

---

### 5. Special Link Extraction System 🔥
We built a **custom extractor** to detect:
- Email
- GitHub
- LinkedIn
- Phone numbers

👉 Even if they are hidden in buttons/icons

---

## 🛠️ Tech Stack

- **Python**
- **Streamlit** (Frontend UI)
- **OpenRouter API (GPT)**
- **BeautifulSoup** (HTML parsing)
- **Requests** (basic scraping)
- **Playwright** (JavaScript rendering)
- **Scikit-learn (TF-IDF)**

---

## ⚡ Features

- 🌐 Works with **any website**
- 🧠 Context-aware answers
- 🔍 Smart content retrieval
- 🔗 Extracts hidden links (GitHub, email, etc.)
- ⚡ Handles JavaScript-heavy sites
- 🎯 Accurate and controlled responses
- 💬 Clean chat interface

---

## 🧩 Challenges We Faced

### 1. Website Not Returning Content
- Problem: Some sites returned very small content using Requests  
- Fix: Added **Playwright fallback**

---

### 2. GitHub/LinkedIn Not Detected
- Problem: Links were hidden behind icons/buttons  
- Fix: Extracted all `<a href="">` links from HTML

---

### 3. Wrong / No Answers for Simple Questions
- Problem: Queries like *"what is this?"* failed  
- Fix:
  - Improved question preprocessing
  - Sent more relevant context to GPT

---

### 4. Too Strict AI Responses
- Problem: GPT was rejecting valid answers  
- Fix: Changed prompt from  
  ❌ "exact match required"  
  ✅ "reasonably inferred from context"

---

### 5. Messy Output (Hard to Read)
- Problem: Long paragraphs  
- Fix: Structured answers into **clean bullet points**

---

## 🧪 Example Queries

- `What is this website?`
- `Any GitHub links?`
- `What services do they provide?`
- `Any contact information?`

---

## 📦 How to Run Locally

```bash
# Clone the repository
git clone https://github.com/your-username/WebContextAI.git

# Move into project folder
cd WebContextAI

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

## 🔑 Environment Variables

Create a `.env` file in the root directory and add:

```env
OPENROUTER_API_KEY=your_api_key_here
BASE_URL=https://openrouter.ai/api/v1
MODEL=openai/gpt-3.5-turbo

# Run the app
streamlit run streamlit_app.py


🔐 Important Note
.env file is not included for security reasons
Add your own OpenRouter API key
📈 Future Improvements
Add Embeddings + FAISS for better semantic search
Add multi-page crawling
Add chat memory
Improve UI/UX
