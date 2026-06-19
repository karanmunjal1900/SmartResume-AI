from utils.gemini_helper_new import score_resume_direct


def score_resume(resume_text):
    """
    Scores the resume. Now delegates to the combined Gemini call
    via gemini_helper to avoid using a second API quota slot.
    """
    return score_resume_direct(resume_text)
