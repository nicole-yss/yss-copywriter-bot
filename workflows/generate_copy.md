# Workflow: Generate Content Copy

## Objective
Generate on-brand social media copy for YourSalonSupport using RAG context from viral content research and brand voice analysis.

## Prerequisites
- Viral content has been scraped and embedded (see `research_viral_content.md`)
- Brand voice has been analyzed (see `analyze_brand_voice.md`)
- Backend server is running

## Method 1: Chat Interface (Recommended)

1. Start the backend: `cd "/Users/macbook/YSS Brand Content Copywriter" && source .venv/bin/activate && uvicorn backend.main:app --reload --port 8000`
2. Start the frontend: `cd frontend && npm run dev`
3. Open `http://localhost:3000`
4. Select content type (Caption / Carousel / EDM / Reel Script)
5. Select platform (Instagram / TikTok / YouTube)
6. Type your request and chat with the AI

## Method 2: CLI Tool

```bash
# Caption
python tools/generate_copy.py --type caption --platform instagram --prompt "Post about 5 ways to increase salon bookings this month"

# Carousel
python tools/generate_copy.py --type carousel --platform instagram --prompt "7 mistakes salon owners make with their social media"

# EDM
python tools/generate_copy.py --type edm --prompt "Email announcing our new social media management package for salons"

# Reel Script
python tools/generate_copy.py --type reel_script --platform tiktok --prompt "Quick tip about why salons need a booking system"
```

## Method 3: API

```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Write a caption about salon growth"}], "contentType": "caption", "platform": "instagram"}'
```

## Content Types

| Type | Output Format | Best For |
|------|--------------|----------|
| Caption | Plain text (hook + body + CTA + hashtags) | Single posts |
| Carousel | JSON with cover, slides, CTA, caption | Educational content, tips lists |
| EDM | JSON with subject, body sections, CTA | Email marketing, DM campaigns |
| Reel Script | JSON with hook, scenes, voiceover, timing | Short-form video content |

## Tips for Best Results
- Be specific about the topic (not just "write a post")
- Mention the target audience if it differs from general salon owners
- Specify any constraints (e.g., "keep it under 150 characters for TikTok")
- For carousels, mention how many slides you want
- For reels, mention the desired duration (15s, 30s, 60s)
