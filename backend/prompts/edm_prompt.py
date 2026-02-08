EDM_TEMPLATE = """Generate email/direct message marketing copy.

Output as JSON with this exact structure:
{
    "subject_line": "Compelling subject line (under 50 characters)",
    "preview_text": "Preview/preheader text (under 90 characters)",
    "greeting": "Personalized opening line",
    "body_sections": [
        {
            "heading": "Section heading (optional, can be null)",
            "content": "Section body copy (1-3 short paragraphs)"
        }
    ],
    "cta": {
        "button_text": "Button/link text (2-5 words)",
        "surrounding_copy": "Copy around the CTA button for context"
    },
    "sign_off": "Closing line and signature",
    "ps_line": "Optional P.S. line (high-impact afterthought, can be null)"
}

Guidelines:
- Subject line must create curiosity or urgency (avoid spam trigger words)
- Keep paragraphs to 2-3 sentences maximum
- One primary CTA only (avoid decision fatigue)
- Write as if talking to one salon owner, not a crowd
- P.S. lines have very high read rates - use them for a bonus insight or secondary CTA
- Mobile-first: short paragraphs, scannable format
- Avoid ALL CAPS and excessive exclamation marks"""
