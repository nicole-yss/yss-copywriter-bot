CAROUSEL_TEMPLATE = """Generate copy for a multi-slide carousel post.

Output as JSON with this exact structure:
{
    "cover_slide": {
        "headline": "Bold headline (5-8 words max)",
        "subheadline": "Supporting line (optional, 1 short sentence)"
    },
    "slides": [
        {
            "slide_number": 1,
            "headline": "Slide headline (3-6 words)",
            "body": "1-2 sentences of content per slide",
            "design_note": "Optional visual suggestion for the designer"
        }
    ],
    "final_slide": {
        "cta_headline": "Clear call to action headline",
        "cta_body": "What to do next (follow, save, DM, etc.)",
        "handle": "@yoursalonsupport"
    },
    "caption": "The post caption to accompany the carousel (with hook + CTA)",
    "hashtags": ["list", "of", "relevant", "hashtags"]
}

Guidelines:
- 5-10 slides total (including cover and final CTA slide)
- Each slide delivers ONE clear idea or tip
- Use progressive revelation (build the story slide by slide)
- Headlines should make sense even without the body text
- Cover slide must be scroll-stopping and curiosity-inducing
- Final slide must drive action
- Caption should complement, not repeat, the carousel content"""
