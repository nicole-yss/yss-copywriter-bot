REEL_SCRIPT_TEMPLATE = """Generate a script for a 15-60 second reel or TikTok video.

Output as JSON with this exact structure:
{
    "hook": {
        "text": "Opening line (said in first 1-3 seconds - this is EVERYTHING)",
        "on_screen_text": "Text overlay for the hook",
        "visual_note": "What's shown on screen during the hook",
        "duration_seconds": 3
    },
    "scenes": [
        {
            "scene_number": 1,
            "voiceover": "What is said (spoken script)",
            "on_screen_text": "Text overlay (keep short, 5-8 words max)",
            "visual_note": "What's shown/happening on screen",
            "duration_seconds": 5
        }
    ],
    "cta": {
        "text": "Closing CTA (spoken)",
        "on_screen_text": "CTA text overlay",
        "visual_note": "Final visual",
        "duration_seconds": 3
    },
    "caption": "Post caption for the reel",
    "hashtags": ["relevant", "hashtags"],
    "audio_suggestion": "Trending audio recommendation or music style",
    "total_duration_seconds": 30
}

Guidelines:
- HOOK is everything - first 3 seconds determine if viewers stay or scroll
- Use pattern interrupts (unexpected statements, questions, reveals)
- Keep total duration 15-30 seconds (optimal for algorithm)
- On-screen text must be readable in the time shown (max 8 words per screen)
- Script should sound natural when spoken, not written/formal
- End with clear CTA + @yoursalonsupport branding
- Include transition cues between scenes
- Hook formulas that work: "Stop doing X", "The #1 mistake...", "POV:", "Here's why your salon..."
"""
