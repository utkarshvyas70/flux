from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
import re
import os

router = APIRouter(tags=["advisor"])


class AdvisorRequest(BaseModel):
    prompt_text: str


class ModelRecommendation(BaseModel):
    model: str
    provider: str
    score: float
    reasons: List[str]
    best_for: str
    cost_tier: str
    context_window: str


class AdvisorResponse(BaseModel):
    task_type: str
    task_confidence: float
    recommendations: List[ModelRecommendation]
    summary: str


MODELS = [
    {
        "model": "gpt-4o",
        "provider": "OpenAI",
        "best_for": "Complex reasoning, analysis, long documents",
        "cost_tier": "High ($5/1M input tokens)",
        "context_window": "128K tokens",
        "strengths": ["reasoning", "analysis", "code", "math", "long_context", "creative", "multilingual"],
    },
    {
        "model": "gpt-4o-mini",
        "provider": "OpenAI",
        "best_for": "Fast, affordable tasks with good quality",
        "cost_tier": "Low ($0.15/1M input tokens)",
        "context_window": "128K tokens",
        "strengths": ["speed", "cost", "summarization", "classification", "qa", "support"],
    },
    {
        "model": "claude-opus-4-6",
        "provider": "Anthropic",
        "best_for": "Long documents, nuanced writing, safety-critical tasks",
        "cost_tier": "High ($15/1M input tokens)",
        "context_window": "200K tokens",
        "strengths": ["long_context", "writing", "analysis", "safety", "nuance", "reasoning"],
    },
    {
        "model": "claude-sonnet-4-6",
        "provider": "Anthropic",
        "best_for": "Balanced performance and cost for most tasks",
        "cost_tier": "Medium ($3/1M input tokens)",
        "context_window": "200K tokens",
        "strengths": ["writing", "code", "analysis", "speed", "reasoning", "support"],
    },
    {
        "model": "gemini-1.5-pro",
        "provider": "Google",
        "best_for": "Multimodal tasks, very long contexts",
        "cost_tier": "Medium ($3.5/1M input tokens)",
        "context_window": "1M tokens",
        "strengths": ["long_context", "multimodal", "code", "analysis", "multilingual"],
    },
    {
        "model": "gemini-1.5-flash",
        "provider": "Google",
        "best_for": "Fast, cheap tasks at scale",
        "cost_tier": "Very Low ($0.075/1M input tokens)",
        "context_window": "1M tokens",
        "strengths": ["speed", "cost", "summarization", "classification", "qa"],
    },
    {
        "model": "llama-3.1-70b",
        "provider": "Meta (via Groq/Together)",
        "best_for": "Open source, data privacy, self-hosting",
        "cost_tier": "Very Low (self-hosted free)",
        "context_window": "128K tokens",
        "strengths": ["open_source", "privacy", "code", "reasoning", "cost"],
    },
    {
        "model": "mistral-large",
        "provider": "Mistral AI",
        "best_for": "European data compliance, multilingual",
        "cost_tier": "Medium ($2/1M input tokens)",
        "context_window": "128K tokens",
        "strengths": ["multilingual", "code", "reasoning", "privacy", "european_compliance"],
    },
]

TASK_KEYWORDS = {
    "code": ["code", "function", "debug", "programming", "script", "api", "implement", "refactor", "bug", "syntax", "python", "javascript", "typescript", "sql", "html", "css", "algorithm"],
    "writing": ["write", "draft", "essay", "blog", "article", "story", "creative", "narrative", "prose", "email", "letter", "report", "document"],
    "summarization": ["summarize", "summary", "tldr", "brief", "shorten", "condense", "overview", "key points", "extract"],
    "analysis": ["analyze", "analysis", "evaluate", "assess", "review", "compare", "contrast", "examine", "investigate", "research"],
    "math": ["calculate", "math", "equation", "solve", "formula", "number", "compute", "arithmetic", "statistics", "probability"],
    "reasoning": ["reason", "logic", "think", "step by step", "explain why", "cause", "effect", "deduce", "infer", "conclude"],
    "support": ["customer", "support", "help", "assist", "service", "respond", "answer", "reply", "ticket", "complaint", "issue"],
    "classification": ["classify", "categorize", "label", "tag", "identify", "detect", "determine", "decide", "is this"],
    "translation": ["translate", "translation", "language", "multilingual", "french", "spanish", "german", "chinese", "japanese", "hindi"],
    "long_context": ["document", "pdf", "long", "entire", "full text", "whole", "all of", "throughout", "book", "report", "contract"],
    "qa": ["question", "answer", "what is", "how does", "explain", "tell me", "describe", "define", "faq"],
    "safety": ["safe", "appropriate", "harmful", "toxic", "moderate", "filter", "policy", "compliance", "sensitive"],
}


def classify_task(prompt_text: str) -> tuple[str, float]:
    text_lower = prompt_text.lower()
    scores = {}

    for task, keywords in TASK_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text_lower:
                score += 1
        if score > 0:
            scores[task] = score / len(keywords)

    if not scores:
        return "general", 0.5

    top_task = max(scores, key=scores.get)
    confidence = min(scores[top_task] * 10, 1.0)
    return top_task, confidence


def score_model(model: dict, task: str, prompt_text: str) -> tuple[float, List[str]]:
    score = 0.5
    reasons = []
    text_lower = prompt_text.lower()

    if task in model["strengths"]:
        score += 0.3
        reasons.append(f"Excellent at {task.replace('_', ' ')} tasks")

    word_count = len(prompt_text.split())
    if word_count > 500 and "long_context" in model["strengths"]:
        score += 0.15
        reasons.append("Handles long prompts exceptionally well")

    if any(lang in text_lower for lang in ["translate", "french", "spanish", "german", "chinese", "japanese", "hindi", "arabic"]):
        if "multilingual" in model["strengths"]:
            score += 0.15
            reasons.append("Strong multilingual capabilities")

    if any(word in text_lower for word in ["cheap", "cost", "affordable", "scale", "millions", "bulk"]):
        if model["cost_tier"].startswith("Very Low") or model["cost_tier"].startswith("Low"):
            score += 0.1
            reasons.append("Very cost-effective for high-volume use")

    if any(word in text_lower for word in ["fast", "quick", "realtime", "real-time", "latency", "speed"]):
        if "speed" in model["strengths"]:
            score += 0.1
            reasons.append("Optimized for low latency responses")

    if any(word in text_lower for word in ["private", "privacy", "gdpr", "compliance", "on-premise", "self-host"]):
        if "privacy" in model["strengths"] or "open_source" in model["strengths"]:
            score += 0.15
            reasons.append("Good for privacy-sensitive deployments")

    if any(word in text_lower for word in ["safe", "moderate", "harmful", "appropriate", "policy"]):
        if "safety" in model["strengths"]:
            score += 0.1
            reasons.append("Strong safety and content moderation")

    if task in ["reasoning", "math", "analysis"] and "reasoning" in model["strengths"]:
        score += 0.1
        reasons.append("Strong logical reasoning capabilities")

    if not reasons:
        reasons.append(f"Capable general-purpose model for {task.replace('_', ' ')} tasks")

    return min(score, 1.0), reasons


def get_llm_advice(prompt_text: str) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-placeholder":
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""Analyze this prompt and in one sentence tell what type of task it is and what makes it unique:

Prompt: {prompt_text[:500]}

Respond in one sentence, max 30 words."""
            }],
            max_tokens=60,
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


@router.post("/advisor/recommend", response_model=AdvisorResponse)
def recommend_models(data: AdvisorRequest):
    if not data.prompt_text or len(data.prompt_text.strip()) < 10:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Prompt too short to analyze")

    task_type, confidence = classify_task(data.prompt_text)

    scored_models = []
    for model in MODELS:
        score, reasons = score_model(model, task_type, data.prompt_text)
        scored_models.append({
            "model": model["model"],
            "provider": model["provider"],
            "score": round(score, 2),
            "reasons": reasons[:3],
            "best_for": model["best_for"],
            "cost_tier": model["cost_tier"],
            "context_window": model["context_window"],
        })

    scored_models.sort(key=lambda x: x["score"], reverse=True)
    top_models = scored_models[:4]

    llm_summary = get_llm_advice(data.prompt_text)
    if not llm_summary:
        task_label = task_type.replace("_", " ").title()
        llm_summary = f"This appears to be a {task_label} task. Top recommendation is {top_models[0]['model']} based on task requirements and cost efficiency."

    return AdvisorResponse(
        task_type=task_type,
        task_confidence=round(confidence, 2),
        recommendations=top_models,
        summary=llm_summary,
    )