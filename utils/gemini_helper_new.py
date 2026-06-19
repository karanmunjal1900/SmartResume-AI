import google.generativeai as genai
import os
import time
import json
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        import streamlit as st
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        raise ValueError("GEMINI_API_KEY not found in .env or Streamlit secrets.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config=genai.types.GenerationConfig(
        temperature=0.0,
        top_p=1.0,
        top_k=1,
    )
)

# ═══════════════════════════════════════════════════
# DEFAULTS
# ═══════════════════════════════════════════════════
_DEFAULT_PARSED = {
    "name": "", "email": "", "phone": "",
    "skills":         [],
    "education":      [],
    "experience":     [],
    "projects":       [],
    "certifications": [],
    "achievements":   [],
}
_DEFAULT_SCORE = {
    "score":      0,
    "strengths":  [],
    "weaknesses": [],
    "verdict":    "",
}


# ═══════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════
def _clean_json(raw: str) -> str:
    return raw.replace("```json", "").replace("```", "").strip()


def _safe_score(score_raw: dict) -> dict:
    merged = {**_DEFAULT_SCORE, **score_raw}
    merged["score"] = int(merged.get("score") or 0)
    return merged


def _safe_parsed(parsed_raw: dict) -> dict:
    return {**_DEFAULT_PARSED, **parsed_raw}


def _quota_score(message: str) -> dict:
    return {
        "score": 0,
        "strengths": [],
        "weaknesses": [f"QUOTA_EXCEEDED: {message}"],
        "verdict": "API quota limit reached.",
    }


# ═══════════════════════════════════════════════════
# CORE API CALL WITH RETRY
# ═══════════════════════════════════════════════════
def ask_gemini(prompt: str, retries: int = 3, wait: int = 20) -> str:
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            error_msg = str(e)
            is_quota = (
                "429"               in error_msg or
                "ResourceExhausted" in error_msg or
                "quota"             in error_msg.lower()
            )
            if is_quota:
                if attempt < retries - 1:
                    time.sleep(wait)
                    continue
                return json.dumps({"error": "QUOTA_EXCEEDED"})
            return json.dumps({"error": error_msg})

    return json.dumps({"error": "Unknown error after retries."})


# ═══════════════════════════════════════════════════
# COMBINED PARSE + SCORE  (1 API call)
# ═══════════════════════════════════════════════════
def parse_resume_and_score(resume_text: str) -> tuple[dict, dict]:
    prompt = f"""
You are an expert ATS Resume Parser and Reviewer.
Analyze the resume and return ONE valid JSON object with two top-level keys:
  1. "parsed"     — structured resume data
  2. "score_data" — ATS quality review

STRICT RULES:
- Extract ONLY what is present in the resume. Never invent data.
- Empty fields use "" or [].
- certifications: scan for ANY section labelled Certifications, Licenses,
  Courses, Training, Online Courses, Professional Development, Credentials,
  or similar. Extract EVERY item found. If issuer or date is absent use "".
- score_data: COMPLETELY IGNORE all dates everywhere — certification dates,
  education dates, experience dates, project dates. Do NOT comment on any
  date being future, recent, invalid, or suspicious. Treat all dates as
  valid regardless of the year. A certificate dated 2025 or 2026 is VALID
  and must NEVER appear in weaknesses.
- Calculate "score" using this EXACT point system out of 100, then sum:
  * Skills section present and relevant (0-20 points)
  * Experience OR Projects section with clear descriptions (0-20 points)
  * Education section complete (0-15 points)
  * Quantified achievements / metrics present anywhere (0-15 points)
  * Certifications present (0-10 points)
  * Clear formatting / contact info complete (0-10 points)
  * Strong action verbs used (0-10 points)
- Add up the points exactly as defined above. Do not adjust the sum based
  on overall "feel" — the sum of the point categories IS the final score.
- Show your point allocation reasoning internally but output ONLY the
  final numeric sum as "score".
- Return ONLY raw JSON — no markdown, no backticks, no explanation text.

Required structure:

{{
  "parsed": {{
    "name":  "",
    "email": "",
    "phone": "",
    "skills": ["skill1", "skill2"],
    "education": [
      {{"degree": "", "institution": "", "date": ""}}
    ],
    "experience": [
      {{"role": "", "company": "", "duration": "", "description": ""}}
    ],
    "projects": [
      {{"title": "", "description": ""}}
    ],
    "certifications": [
      {{"name": "", "issuer": "", "date": ""}}
    ],
    "achievements": ["achievement 1"]
  }},
  "score_data": {{
    "score":      0,
    "strengths":  ["clear strength from the resume"],
    "weaknesses": ["one real improvement area — do NOT mention dates"],
    "verdict":    "Honest 2-sentence ATS readiness summary — do NOT mention dates."
  }}
}}

Resume Text:
\"\"\"{resume_text}\"\"\"
"""

    raw   = ask_gemini(prompt)
    clean = _clean_json(raw)

    try:
        err_check = json.loads(clean)
        if err_check.get("error") == "QUOTA_EXCEEDED":
            return _safe_parsed({}), _quota_score(
                "Free tier limit (20 req/day) reached. "
                "Wait 24 h or upgrade at https://ai.dev/rate-limit"
            )
    except (json.JSONDecodeError, AttributeError):
        pass

    try:
        result     = json.loads(clean)
        parsed     = _safe_parsed(result.get("parsed",     {}))
        score_data = _safe_score( result.get("score_data", {}))
        return parsed, score_data

    except json.JSONDecodeError:
        error_score = {
            **_DEFAULT_SCORE,
            "weaknesses": ["Could not parse Gemini response. Please try again."],
            "verdict":    "Parsing failed.",
        }
        return _safe_parsed({}), error_score


# ═══════════════════════════════════════════════════
# JD MATCHER  (1 API call)
# ═══════════════════════════════════════════════════
def match_jd(resume_text: str, jd_text: str) -> dict:
    prompt = f"""
You are an expert ATS Job Description Matcher.

Compare the resume against the job description and return ONLY valid JSON.

RULES:
- match_score: integer 0-100 based on skills, keywords, experience overlap.
- matched_keywords: skills/keywords found in BOTH resume and JD.
- missing_keywords: important JD keywords NOT present in the resume.
- recommended_keywords: extra keywords the candidate should add for this role.
- match_verdict: 2-3 sentence summary of how well the candidate fits.
- All keyword lists: short clean terms only e.g. "Python", "REST APIs".
- Return ONLY raw JSON — no markdown, no backticks.

{{
  "match_score": 0,
  "matched_keywords": [],
  "missing_keywords": [],
  "recommended_keywords": [],
  "match_verdict": ""
}}

Job Description:
\"\"\"{jd_text}\"\"\"

Resume:
\"\"\"{resume_text}\"\"\"
"""

    raw   = ask_gemini(prompt)
    clean = _clean_json(raw)

    _default = {
        "match_score":          0,
        "matched_keywords":     [],
        "missing_keywords":     [],
        "recommended_keywords": [],
        "match_verdict":        "",
    }

    try:
        err_check = json.loads(clean)
        if err_check.get("error") == "QUOTA_EXCEEDED":
            return {**_default, "match_verdict": "QUOTA_EXCEEDED"}
    except (json.JSONDecodeError, AttributeError):
        pass

    try:
        result = json.loads(clean)
        return {**_default, **result}
    except json.JSONDecodeError:
        return {**_default, "match_verdict": "Could not parse response. Try again."}


# ═══════════════════════════════════════════════════
# INTERVIEW QUESTION GENERATOR  (1 API call)
# ═══════════════════════════════════════════════════
def generate_interview_questions(resume_text: str, jd_text: str = "") -> list:
    jd_section = f"""
Job Description (use this to tailor questions to the role):
\"\"\"{jd_text}\"\"\"
""" if jd_text.strip() else ""

    prompt = f"""
You are an expert technical interviewer preparing questions for a candidate.

{jd_section}
Analyze the resume below and generate exactly 10 interview questions.

RULES:
- Mix question types: Technical, Behavioral, Project-Based, Situational.
- Questions must be specific to THIS candidate's actual projects, skills,
  and experience — not generic.
- If a JD is provided, bias questions toward that role's requirements.
- Each question should be clear, concise, and interview-ready.
- Return ONLY valid raw JSON — no markdown, no backticks, no explanation.

{{
  "questions": [
    {{"number": 1, "type": "Technical",     "question": "..."}},
    {{"number": 2, "type": "Project-Based", "question": "..."}},
    {{"number": 3, "type": "Behavioral",    "question": "..."}},
    {{"number": 4, "type": "Situational",   "question": "..."}},
    {{"number": 5, "type": "Technical",     "question": "..."}},
    {{"number": 6, "type": "Project-Based", "question": "..."}},
    {{"number": 7, "type": "Behavioral",    "question": "..."}},
    {{"number": 8, "type": "Technical",     "question": "..."}},
    {{"number": 9, "type": "Situational",   "question": "..."}},
    {{"number": 10,"type": "Project-Based", "question": "..."}}
  ]
}}

Resume:
\"\"\"{resume_text}\"\"\"
"""

    raw   = ask_gemini(prompt)
    clean = _clean_json(raw)

    try:
        err_check = json.loads(clean)
        if err_check.get("error") == "QUOTA_EXCEEDED":
            return [{"number": 1, "type": "Error",
                     "question": "QUOTA_EXCEEDED: Free tier limit reached. Wait 24h or upgrade."}]
    except (json.JSONDecodeError, AttributeError):
        pass

    try:
        result = json.loads(clean)
        return result.get("questions", [])
    except json.JSONDecodeError:
        return [{"number": 1, "type": "Error",
                 "question": "Could not parse Gemini response. Please try again."}]


# ═══════════════════════════════════════════════════
# BULLET REWRITER  (1 API call)
# ═══════════════════════════════════════════════════
def rewrite_bullets(bullets_text: str) -> list:
    """
    Rewrite weak resume bullet points into stronger, ATS-friendly,
    quantified versions. Returns list of {original, improved}.
    """

    prompt = f"""
You are an expert resume coach. Rewrite each resume bullet point below
to be more impactful, ATS-friendly, and quantified where reasonable.

Input bullets (one per line):
\"\"\"{bullets_text}\"\"\"

RULES:
- Treat each non-empty line as one separate bullet to rewrite.
- Use strong action verbs (Led, Built, Optimized, Architected, Reduced, etc.).
- Add realistic metrics/numbers ONLY where it makes sense — do not invent
  wildly implausible numbers.
- Keep each improved bullet under 25 words.
- Preserve the original meaning — do not change what the person actually did.
- Return ONLY valid raw JSON — no markdown, no backticks, no explanation.

{{
  "rewrites": [
    {{"original": "...", "improved": "..."}}
  ]
}}
"""

    raw   = ask_gemini(prompt)
    clean = _clean_json(raw)

    try:
        err_check = json.loads(clean)
        if err_check.get("error") == "QUOTA_EXCEEDED":
            return [{"original": "—", "improved": "QUOTA_EXCEEDED: Free tier limit reached."}]
    except (json.JSONDecodeError, AttributeError):
        pass

    try:
        result = json.loads(clean)
        return result.get("rewrites", [])
    except json.JSONDecodeError:
        return [{"original": "—", "improved": "Could not parse response. Please try again."}]


# ═══════════════════════════════════════════════════
# COVER LETTER GENERATOR  (1 API call)
# ═══════════════════════════════════════════════════
def generate_cover_letter(resume_text: str, jd_text: str, tone: str = "Professional",
                          company_name: str = "", role_title: str = "") -> dict:
    """
    Generate a tailored cover letter from resume + job description.
    Returns {"cover_letter": str} or {"error": "QUOTA_EXCEEDED"}.
    """

    company_line = f"The company is: {company_name}.\n" if company_name.strip() else ""
    role_line    = f"The role is: {role_title}.\n" if role_title.strip() else ""

    prompt = f"""
You are an expert career coach writing a cover letter on behalf of a candidate.

{company_line}{role_line}
Write a tailored, compelling cover letter using ONLY the candidate's actual
resume content below — do not invent experience, skills, or achievements
that are not present in the resume.

TONE: {tone}

RULES:
- 3-4 paragraphs: opening hook, relevant experience/skills tied to the JD,
  why this company/role specifically, confident closing with call to action.
- Reference 2-3 SPECIFIC things from the resume (a real project, a real
  skill, a real achievement) — not generic filler.
- Do not use placeholder text like "[Company Name]" if company_name was
  given above — use the real name. If no company name was given, write
  generically without brackets (e.g. "your team" instead of "[Company]").
- Keep it under 350 words.
- Do not include a letterhead, date, or address block — body text only.
- Return ONLY valid raw JSON — no markdown, no backticks.

{{
  "cover_letter": "Full cover letter text here, with paragraphs separated by \\n\\n"
}}

Job Description:
\"\"\"{jd_text}\"\"\"

Resume:
\"\"\"{resume_text}\"\"\"
"""

    raw   = ask_gemini(prompt)
    clean = _clean_json(raw)

    try:
        err_check = json.loads(clean)
        if err_check.get("error") == "QUOTA_EXCEEDED":
            return {"cover_letter": "QUOTA_EXCEEDED"}
    except (json.JSONDecodeError, AttributeError):
        pass

    try:
        result = json.loads(clean)
        return {"cover_letter": result.get("cover_letter", "")}
    except json.JSONDecodeError:
        return {"cover_letter": "Could not parse response. Please try again."}


# ═══════════════════════════════════════════════════
# BACKWARD-COMPATIBILITY SHIMS
# ═══════════════════════════════════════════════════
def parse_resume(resume_text: str) -> str:
    parsed, _ = parse_resume_and_score(resume_text)
    return json.dumps(parsed)


def score_resume_direct(resume_text: str) -> dict:
    _, score_data = parse_resume_and_score(resume_text)
    return score_data