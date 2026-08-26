import os
import re
import html as html_lib
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


def get_llm():
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Please set it in your .env file.")

    return ChatGroq(
        model_name="openai/gpt-oss-20b",
        groq_api_key=api_key,
        temperature=0.2,
    )


def get_embeddings():
    """Get HuggingFace embeddings forced to CPU — works on all machines."""
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    return "\n\n".join(doc.page_content for doc in docs)


# ── MODULE 1 + 2: GenAI + RAG ─────────────────────────────────────────
def build_qa_chain(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = get_llm()

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are an expert career coach and resume reviewer.
You have access to the resume content below.
Answer questions based on the resume. If asked for suggestions,
improvements, or feedback — analyze the resume and give helpful,
specific advice like a career coach would.

Resume content:
{context}

Question: {question}
Answer:"""
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


# ── MODULE 1 + 2: GenAI + RAG — Resume vs JD Analysis ─────────────────
def analyze_resume(pdf_path: str, job_description: str) -> dict:
    resume_text = extract_text_from_pdf(pdf_path)
    llm = get_llm()

    prompt = f"""You are an expert career coach and ATS system.

Compare this resume against the job description below.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Respond in exactly this format — nothing else:
SCORE: [a number from 0 to 100]
MISSING_SKILLS: [comma separated list of skills in the JD that are missing from the resume]
FEEDBACK: [3 to 5 specific, actionable suggestions to improve the resume for this role]
"""

    response = llm.invoke(prompt).content

    score = 50
    missing_skills = "Could not extract"
    feedback = response

    try:
        score_match = re.search(r"SCORE:\s*(\d+)", response)
        if score_match:
            score = min(100, max(0, int(score_match.group(1))))

        skills_match = re.search(
            r"MISSING_SKILLS:\s*(.+?)(?:\n|FEEDBACK:)", response, re.DOTALL)
        if skills_match:
            missing_skills = skills_match.group(1).strip()

        feedback_match = re.search(r"FEEDBACK:\s*(.+)", response, re.DOTALL)
        if feedback_match:
            feedback = feedback_match.group(1).strip()
    except Exception as e:
        feedback = response

    return {
        "score": score,
        "missing_skills": missing_skills,
        "feedback": feedback,
        "resume_text": resume_text
    }


# ── MODULE 3: Agentic AI — Auto Improve Loop ──────────────────────────
def improve_resume(resume_text: str, job_description: str, current_score: int) -> dict:
    llm = get_llm()

    prompt = f"""You are an expert resume writer and career coach.

The resume below scored {current_score}/100 against the job description.
Your job is to rewrite and improve the resume to score higher.

Instructions:
- Rewrite weak bullet points using strong action verbs
- Add missing keywords from the job description naturally
- Keep all facts true — do not invent experience
- Make it ATS-friendly

JOB DESCRIPTION:
{job_description}

CURRENT RESUME:
{resume_text}

Respond in exactly this format:
NEW_SCORE: [estimated new score from 0 to 100]
IMPROVED_RESUME:
[the full improved resume text]
"""

    response = llm.invoke(prompt).content

    new_score = current_score
    improved_text = resume_text

    score_match = re.search(r"NEW_SCORE:\s*(\d+)", response)
    if score_match:
        new_score = int(score_match.group(1))

    resume_match = re.search(r"IMPROVED_RESUME:\s*(.+)", response, re.DOTALL)
    if resume_match:
        improved_text = resume_match.group(1).strip()

    return {
        "new_score": new_score,
        "improved_text": improved_text
    }


# ── ATS Keyword Heatmap ───────────────────────────────────────────────────
def extract_keywords(job_description: str) -> list:
    """Extract must-have keywords from JD using LLM."""
    llm = get_llm()
    prompt = f"""Extract the most important technical skills, tools, and keywords from this job description.

JOB DESCRIPTION:
{job_description}

Respond in exactly this format — nothing else:
KEYWORDS: keyword1, keyword2, keyword3, keyword4, keyword5, keyword6, keyword7, keyword8, keyword9, keyword10
"""
    response = llm.invoke(prompt).content
    keywords = []
    match = re.search(r"KEYWORDS:\s*(.+)", response)
    if match:
        keywords = [k.strip().lower()
                    for k in match.group(1).split(",") if k.strip()]
    return keywords


def build_heatmap(resume_text: str, keywords: list):
    """Highlight matched keywords in green, list missing ones separately."""
    if not keywords or not resume_text:
        return html_lib.escape(resume_text), [], []

    resume_lower = resume_text.lower()
    matched = []
    missing = []

    for kw in keywords:
        if kw.lower() in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    # Escape HTML in resume text first
    highlighted = html_lib.escape(resume_text)

    # Highlight matched keywords in green
    for kw in matched:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        highlighted = pattern.sub(
            lambda m: f'<mark style="background:#14532d;color:#4ade80;border-radius:3px;padding:1px 4px;font-weight:600">{m.group()}</mark>',
            highlighted
        )

    return highlighted, matched, missing
