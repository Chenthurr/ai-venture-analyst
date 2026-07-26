"""
AI analysis orchestration.

Retrieves the most relevant document chunks for a project (hybrid search),
feeds them to the OpenAI chat model as grounding context, and asks for a
structured JSON response covering the core VC analysis modules. Every
generated claim is required (via the prompt contract) to reference the
source chunk(s) it came from, which we surface as `citations`.

This is a single well-structured LLM call rather than a 12-agent LangGraph
graph -- that orchestration is the natural next increment once this
grounded-generation core is proven out (see README "Roadmap").
"""
from __future__ import annotations

import json
from typing import Dict, List

from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.services.embeddings import get_openai_client, hybrid_search

SCORE_CATEGORIES = [
    "founder_strength",
    "market_size",
    "product_quality",
    "traction",
    "competition",
    "financial_health",
    "business_model",
    "technology",
    "scalability",
    "investment_readiness",
]

RISK_CATEGORIES = [
    "management_risk",
    "stage_of_business_risk",
    "legislation_political_risk",
    "manufacturing_risk",
    "sales_marketing_risk",
    "funding_capital_raising_risk",
    "competition_risk",
    "technology_risk",
    "litigation_risk",
    "international_risk",
    "reputation_risk",
    "exit_value_risk",
]

SYSTEM_PROMPT = """You are a Principal analyst at a top-tier venture capital firm \
(in the style of Sequoia, a16z, and YC partners). You write rigorous, skeptical, \
evidence-based investment analysis. You are never generic or promotional -- you \
call out weak evidence and missing information explicitly rather than filling gaps \
with generic startup-advice language.

You will be given: (1) structured facts about a startup, and (2) numbered excerpts \
retrieved from the startup's own uploaded documents (pitch deck, financials, market \
research, etc). Ground every substantive claim in the excerpts or the structured \
facts provided. If the documents don't support a claim, say the evidence is missing \
rather than inventing detail.

Respond with ONLY valid JSON (no markdown fences, no preamble) matching this schema:
{
  "executive_summary": "3-5 sentence summary of the company, market, and investment thesis",
  "swot": {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "opportunities": ["..."],
    "threats": ["..."]
  },
  "scores": {
    "<category>": {"score": <0-100 integer>, "reasoning": "1-2 sentences, cite excerpt numbers like [3]"}
    ... one entry for each of: founder_strength, market_size, product_quality, traction,
    competition, financial_health, business_model, technology, scalability, investment_readiness
  },
  "risk_scores": {
    "<category>": {"score": <0-100 integer, where 100 = very low risk>, "reasoning": "..."}
    ... one entry for each of: management_risk, stage_of_business_risk, legislation_political_risk,
    manufacturing_risk, sales_marketing_risk, funding_capital_raising_risk, competition_risk,
    technology_risk, litigation_risk, international_risk, reputation_risk, exit_value_risk
  },
  "investment_memo": "A full multi-paragraph investment memo in markdown, with sections: \
Overview, Market Analysis (TAM/SAM/SOM if derivable, else note it's not derivable from \
the provided materials), Team Assessment, Product & Technology, Competitive Landscape, \
Financial Analysis, Key Risks, Funding Recommendation (invest / pass / more diligence needed, with reasoning).",
  "citations": [
    {"claim": "short paraphrase of the claim", "excerpt_number": <int>}
  ]
}
"""


def build_context_block(project: models.Project, financial_metrics: dict) -> str:
    parts = [
        f"Company: {project.company_name}",
        f"Industry: {project.industry or 'Not specified'}",
        f"Country: {project.country or 'Not specified'}",
        f"Stage: {project.stage or 'Not specified'}",
        f"Founders: {project.founders or 'Not specified'}",
        f"One-liner: {project.one_liner or 'Not specified'}",
    ]
    if financial_metrics:
        parts.append("Computed financial metrics:")
        for k, v in financial_metrics.items():
            parts.append(f"  - {k}: {v}")
    return "\n".join(parts)


def gather_all_chunks(db: Session, project_id: str) -> List[dict]:
    chunks = (
        db.query(models.DocumentChunk, models.Document.filename)
        .join(models.Document, models.DocumentChunk.document_id == models.Document.id)
        .filter(models.DocumentChunk.project_id == project_id)
        .all()
    )
    return [
        {
            "content": chunk.content,
            "embedding": chunk.embedding,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "filename": filename,
        }
        for chunk, filename in chunks
    ]


def run_full_analysis(db: Session, project: models.Project, financial_metrics: dict) -> dict:
    """
    Runs the retrieval + generation pipeline and returns a dict matching
    the AnalysisReport JSON fields.
    """
    all_chunks = gather_all_chunks(db, str(project.id))

    retrieval_query = (
        f"{project.company_name} {project.industry or ''} business model, market, "
        f"team, traction, competition, financials, risks"
    )

    if all_chunks:
        top_chunks = hybrid_search(retrieval_query, all_chunks, top_k=12)
    else:
        top_chunks = []

    numbered_excerpts = []
    for i, (chunk, score) in enumerate(top_chunks, start=1):
        numbered_excerpts.append(
            f"[{i}] (from {chunk['filename']}, relevance={score:.2f}): {chunk['content']}"
        )

    context_block = build_context_block(project, financial_metrics)
    excerpts_block = (
        "\n\n".join(numbered_excerpts)
        if numbered_excerpts
        else "No documents have been uploaded yet -- base the analysis only on the "
        "structured facts above and explicitly note where evidence is missing."
    )

    user_prompt = (
        f"STRUCTURED FACTS:\n{context_block}\n\n"
        f"RETRIEVED DOCUMENT EXCERPTS:\n{excerpts_block}"
    )

    client = get_openai_client()
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    # Resolve excerpt_number citations back to real document/filename/chunk_index
    resolved_citations = []
    for c in parsed.get("citations", []):
        idx = c.get("excerpt_number")
        if idx and 1 <= idx <= len(top_chunks):
            chunk, score = top_chunks[idx - 1]
            resolved_citations.append({
                "claim": c.get("claim"),
                "filename": chunk["filename"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "relevance_score": round(score, 3),
            })

    return {
        "executive_summary": parsed.get("executive_summary"),
        "swot": parsed.get("swot"),
        "scores": parsed.get("scores"),
        "risk_scores": parsed.get("risk_scores", {}),
        "investment_memo": parsed.get("investment_memo"),
        "citations": resolved_citations,
        "model_used": settings.openai_chat_model,
    }


def answer_question(db: Session, project: models.Project, question: str) -> dict:
    """Powers the AI chat feature: retrieves relevant chunks for the specific
    question and answers with citations, rather than reusing the full report."""
    all_chunks = gather_all_chunks(db, str(project.id))
    top_chunks = hybrid_search(question, all_chunks, top_k=8) if all_chunks else []

    numbered_excerpts = [
        f"[{i}] (from {chunk['filename']}): {chunk['content']}"
        for i, (chunk, _) in enumerate(top_chunks, start=1)
    ]
    excerpts_block = "\n\n".join(numbered_excerpts) if numbered_excerpts else "No documents uploaded."

    context_block = build_context_block(project, {})

    client = get_openai_client()
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a VC analyst assistant. Answer the user's question about this "
                    "specific startup using ONLY the structured facts and excerpts given. "
                    "Cite excerpts inline like [2]. If the answer isn't supported by the "
                    "provided material, say so explicitly rather than guessing. Respond with "
                    "ONLY valid JSON: {\"answer\": \"...\", \"cited_excerpt_numbers\": [1,2]}"
                ),
            },
            {
                "role": "user",
                "content": f"STRUCTURED FACTS:\n{context_block}\n\nEXCERPTS:\n{excerpts_block}\n\nQUESTION: {question}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    parsed = json.loads(response.choices[0].message.content)

    citations = []
    for idx in parsed.get("cited_excerpt_numbers", []):
        if 1 <= idx <= len(top_chunks):
            chunk, score = top_chunks[idx - 1]
            citations.append({
                "filename": chunk["filename"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "relevance_score": round(score, 3),
            })

    return {"answer": parsed.get("answer", ""), "citations": citations}
