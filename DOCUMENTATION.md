# YSS Brand Content Copywriter

AI-powered social media content copywriter for **YourSalonSupport** (@yoursalonsupport). Generates on-brand captions, carousels, EDMs, and reel scripts using Claude, informed by scraped viral content, brand voice analysis, web research, and user feedback.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Getting Started](#getting-started)
4. [Environment Variables](#environment-variables)
5. [Backend](#backend)
   - [API Endpoints](#api-endpoints)
   - [Chat Streaming Flow](#chat-streaming-flow)
   - [RAG Pipeline](#rag-pipeline)
   - [Services](#services)
   - [System Prompt & Brand Guide](#system-prompt--brand-guide)
6. [Frontend](#frontend)
   - [Pages & Routes](#pages--routes)
   - [Chat Interface](#chat-interface)
   - [Authentication](#authentication)
7. [Tools (CLI)](#tools-cli)
8. [Database Schema](#database-schema)
   - [Tables](#tables)
   - [Vector Search Functions](#vector-search-functions)
9. [Content Types](#content-types)
10. [Deployment](#deployment)
11. [Workflows](#workflows)

---

## Architecture Overview

The app follows a **WAT (Workflows, Agents, Tools)** architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 16)                 │
│    Chat UI  ·  Dashboard  ·  Reports  ·  Admin Panel    │
└───────────────────────┬─────────────────────────────────┘
                        │ /api/* proxy routes
┌───────────────────────▼─────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  Chat Router · Content Router · Scraping · Reports      │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │
│  │ Research  │  │   RAG    │  │    System Prompt +    │  │
│  │(Perplexity│  │ Service  │  │    Brand Guide        │  │
│  └──────────┘  └──────────┘  └───────────────────────┘  │
└───────┬────────────┬────────────────────┬───────────────┘
        │            │                    │
   ┌────▼────┐  ┌────▼──────┐     ┌──────▼──────┐
   │ Claude  │  │ Supabase  │     │  Voyage AI  │
   │ (LLM)  │  │ (pgvector)│     │ (Embeddings)│
   └─────────┘  └───────────┘     └─────────────┘
```

**Key data flows:**

1. **Content Generation**: User prompt → Perplexity research → RAG context (viral examples + brand voice + feedback) → Claude streaming response
2. **Feedback Loop**: User feedback → embedded & stored → retrieved via vector search → injected into future prompts
3. **Viral Research**: Apify scraping → Supabase storage → Voyage AI embeddings → vector similarity search

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 16, React 19, TypeScript | UI + SSR + API routes |
| UI | shadcn/ui, Tailwind CSS 4 | Component library + styling |
| Backend | FastAPI, Python 3.12+ | API server + business logic |
| LLM | Claude Sonnet 4 (Anthropic) | Content generation |
| Embeddings | Voyage AI (voyage-3.5, 1024 dims) | Semantic search |
| Database | Supabase (PostgreSQL + pgvector) | Storage + vector search |
| Research | Perplexity API | Real-time web research |
| Scraping | Apify | Social media data collection |
| Auth | Supabase Auth (email/password) | User authentication |
| Hosting | Vercel | Frontend + backend deployment |

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Supabase project with pgvector extension enabled
- API keys for: Anthropic, Voyage AI, Apify, Perplexity (optional)

### Backend

```bash
cd "YSS Brand Content Copywriter"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Fill in API keys
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Seed Data (First Time)

```bash
# 1. Scrape viral content from social platforms
python tools/scrape_instagram.py --mode viral --hashtags "salonowner,hairstylist,salonmarketing" --limit 100
python tools/scrape_tiktok.py --mode viral --hashtags "salontok,salonowner" --limit 100

# 2. Generate embeddings for scraped content
python tools/generate_embeddings.py --batch --unembedded

# 3. Analyze the YSS brand voice
python tools/analyze_brand_voice.py --ig-limit 30
```

---

## Environment Variables

```bash
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# Voyage AI (Embeddings)
VOYAGE_API_KEY=pa-...

# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Apify (Scraping)
APIFY_API_TOKEN=apify_api_...

# Perplexity (Research - optional, degrades gracefully)
PERPLEXITY_API_KEY=pplx-...

# Application URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Frontend-only (in frontend/.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## Backend

### API Endpoints

All endpoints are prefixed with `/api/v1`.

#### Chat

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat/stream` | Stream chat response with research + RAG |
| `POST` | `/chat/feedback` | Submit feedback on generated content |
| `POST` | `/chat/sessions` | Create a new chat session |
| `GET` | `/chat/sessions` | List sessions (most recent first, limit 50) |
| `GET` | `/chat/sessions/{id}/messages` | Get messages for a session |

#### Content

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/content/generated` | List generated content (with filters) |
| `POST` | `/content/generated/{id}/rate` | Rate content (1-5) |
| `POST` | `/content/generated/{id}/favorite` | Toggle favorite |
| `GET` | `/content/viral` | Browse scraped viral content |

#### Scraping

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/scraping/jobs` | Start a scraping job |
| `GET` | `/scraping/jobs` | List recent jobs |
| `GET` | `/scraping/jobs/{id}` | Check job status |
| `POST` | `/scraping/brand-analysis` | Trigger brand voice analysis |

#### Reports

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/reports/generate` | Generate analytics report |
| `GET` | `/reports` | List all reports |
| `GET` | `/reports/{id}` | Get report detail |

#### Utility

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/platforms` | List platforms |
| `GET` | `/content-types` | List content types |

### Chat Streaming Flow

The main content generation endpoint (`POST /chat/stream`) follows this pipeline:

```
User message + files
       │
       ▼
┌─────────────────┐
│ 1. Auto-create  │  If no sessionId, create one from the first message
│    session       │
└────────┬────────┘
         │
┌────────▼────────┐
│ 2. Detect       │  Check if user message is feedback (e.g. "too formal",
│    feedback      │  "love it") and save to content_feedback table
└────────┬────────┘
         │
┌────────▼────────┐
│ 3. Research     │  Call Perplexity API for real-time web research
│    (Perplexity) │  on the user's topic
└────────┬────────┘
         │
┌────────▼────────┐
│ 4. RAG context  │  Vector search for: viral examples, brand voice,
│                 │  positive/negative feedback from past sessions
└────────┬────────┘
         │
┌────────▼────────┐
│ 5. Build system │  Combine brand guide + viral examples + research
│    prompt       │  + feedback + content type context
└────────┬────────┘
         │
┌────────▼────────┐
│ 6. Stream from  │  Claude Sonnet 4 with async streaming
│    Claude       │  (text/plain, chunked transfer)
└────────┬────────┘
         │
┌────────▼────────┐
│ 7. Save to DB   │  Store user + assistant messages in chat_messages
│                 │  (best-effort, non-blocking)
└─────────────────┘
```

**Request body:**
```json
{
  "messages": [{ "role": "user", "content": "Write a caption about salon growth" }],
  "contentType": "caption",
  "platform": "instagram",
  "sessionId": "optional-uuid",
  "files": [{ "name": "ref.jpg", "type": "image/jpeg", "data": "base64..." }]
}
```

**Supported file types:**
- Images: JPEG, PNG, WebP, GIF (sent as Claude image blocks)
- Documents: PDF (sent as Claude document blocks)
- Text: .txt, .md, .csv (decoded and included as text blocks)

### RAG Pipeline

The `RAGService` builds context from four sources:

1. **Viral Examples** (up to 5): Vector search over `scraped_content` using `match_content()` RPC. Matches by cosine similarity (threshold 0.3) with optional platform filter.

2. **Brand Voice**: Latest `brand_voice_profiles` entry for @yoursalonsupport, containing tone attributes, vocabulary patterns, sentence structure, emoji usage, and CTA patterns.

3. **Positive Feedback** (up to 3): Vector search over `content_feedback` filtered to `rating='positive'`. Shows Claude what the user liked — "emulate these."

4. **Negative Feedback** (up to 2): Vector search over `content_feedback` filtered to `rating='negative'`. Shows Claude what to avoid — "don't do this."

All vector searches use **Voyage AI voyage-3.5** embeddings (1024 dimensions) with HNSW indexing for fast approximate nearest neighbor lookup.

### Services

| Service | File | Purpose |
|---------|------|---------|
| `RAGService` | `backend/services/rag_service.py` | Retrieves viral examples, brand voice, and feedback via vector search |
| `research_topic()` | `backend/services/research_service.py` | Calls Perplexity API for web research (degrades gracefully if unavailable) |
| `ScrapingService` | `backend/services/scraping_service.py` | Manages scraping jobs: creates records, runs Apify actors, generates embeddings |

### System Prompt & Brand Guide

The system prompt (`backend/prompts/system_prompt.py`) contains a 400+ line **YSS Brand Guide** covering:

- **Brand identity**: YourSalonSupport's mission, offerings (Hair Clubs, social strategy, marketing systems)
- **Voice traits**: Warmly confident, clubby, direct, "big sister energy"
- **Grammar rules**: Short punchy lines, fragments OK, line breaks over long sentences
- **Content structures**: Standard caption format, carousel format, EDM format, reel script format
- **Tone words**: Specific vocabulary to use and avoid
- **CTA patterns**: Platform-specific calls-to-action
- **Special scenarios**: Podcast highlights, celebrations, memes, educational content, POV posts

Content-type-specific templates are in separate files:

| File | Template |
|------|----------|
| `backend/prompts/caption_prompt.py` | Hook + body + CTA + hashtags |
| `backend/prompts/carousel_prompt.py` | Title slide + content slides + CTA slide |
| `backend/prompts/edm_prompt.py` | Subject + preview + greeting + body + CTA + P.S. |
| `backend/prompts/reel_script_prompt.py` | Hook (0-3s) + scenes (3-25s) + CTA (3-5s) |

---

## Frontend

### Pages & Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Main chat interface for content generation |
| `/dashboard` | Dashboard | Browse and manage generated content |
| `/reports` | Reports | View generated analytics reports |
| `/admin` | Admin | User management (admin-only) |
| `/login` | Login | Email/password sign in |
| `/auth/set-password` | Set Password | For invited users setting their password |

**API proxy routes** (forward to FastAPI backend):

| Route | Proxies to |
|-------|-----------|
| `/api/chat` | `/api/v1/chat/stream` |
| `/api/sessions` | `/api/v1/chat/sessions` |
| `/api/sessions/[id]/messages` | `/api/v1/chat/sessions/{id}/messages` |
| `/api/feedback` | `/api/v1/chat/feedback` |
| `/api/admin/users` | `/api/v1/admin/users` |

### Chat Interface

The main component (`src/components/chat/chat-interface.tsx`) provides:

- **Content type & platform selection**: Dropdowns for caption/carousel/EDM/reel script and Instagram/TikTok/YouTube
- **Message streaming**: Manual stream reading with `ReadableStream` (text/plain protocol from FastAPI)
- **File attachments**: Drag-and-drop or click to upload images, PDFs, and text files (base64 encoded, max 20MB)
- **Chat history sidebar**: Collapsible panel listing previous sessions; click to load
- **Auto-session management**: Sessions auto-created on first message; session ID tracked via `X-Session-Id` header
- **Content type switching**: Mid-conversation changes inject an acknowledgment message
- **Rotating suggestions**: 4 random prompts from a pool of 20 shown on empty chat
- **User profile dropdown**: Display name editing, admin settings link, sign out
- **Feedback on AI output**: Thumbs up/down on assistant messages, saved for RAG improvement
- **Error handling**: Specific messages for timeouts and payload-too-large errors

### Authentication

Authentication uses **Supabase Auth** with email/password:

- `src/lib/supabase/client.ts` — Browser-side Supabase client
- `src/lib/supabase/server.ts` — Server-side Supabase client (API routes, server components)
- `src/lib/supabase/admin.ts` — Admin client with service role key
- `src/lib/supabase/middleware.ts` — Session refresh + route protection
- `src/middleware.ts` — Next.js middleware that enforces auth on all routes except `/login`, `/auth/*`, and static assets

**Invite flow**: Admin creates user via admin panel → user receives email → sets password at `/auth/set-password`.

---

## Tools (CLI)

All tools are in `tools/` and can be run standalone from the command line.

### Content Generation

```bash
python tools/generate_copy.py --type caption --platform instagram --prompt "Write about salon growth tips"
python tools/generate_copy.py --type carousel --platform instagram --prompt "5 client retention strategies"
python tools/generate_copy.py --type edm --prompt "New package launch announcement"
python tools/generate_copy.py --type reel_script --platform tiktok --prompt "Day in the salon life"
```

### Scraping

```bash
# Instagram - viral content by hashtags
python tools/scrape_instagram.py --mode viral --hashtags "salonowner,hairstylist,salonmarketing" --limit 100

# Instagram - brand profile for voice analysis
python tools/scrape_instagram.py --mode brand --handle yoursalonsupport --limit 50

# TikTok
python tools/scrape_tiktok.py --mode viral --hashtags "salontok,salonowner,beautybusiness" --limit 100

# YouTube
python tools/scrape_youtube.py --mode search --terms "salon marketing,salon business growth" --limit 50
```

### Embeddings

```bash
# Generate embeddings for all unembedded scraped content
python tools/generate_embeddings.py --batch --unembedded

# Single text embedding
python tools/generate_embeddings.py --text "salon marketing tips"
```

### Vector Search

```bash
python tools/search_vectors.py --query "salon marketing" --limit 10
python tools/search_vectors.py --query "hair tips" --platform instagram --limit 5
```

### Brand Voice Analysis

```bash
python tools/analyze_brand_voice.py --ig-limit 30
```

Scrapes @yoursalonsupport posts, analyzes with Claude, outputs structured JSON with tone attributes, vocabulary patterns, sentence structure, emoji usage, hashtag strategy, and CTA patterns. Stores in `brand_voice_profiles` table with embedding.

### Report Generation

```bash
python tools/generate_report.py --type content_audit        # Performance analysis
python tools/generate_report.py --type competitor_analysis   # Competitive landscape
python tools/generate_report.py --type strategy              # Content strategy recommendations
```

### Utility Clients

| File | Purpose |
|------|---------|
| `tools/utils/supabase_client.py` | Supabase singleton (service role) |
| `tools/utils/claude_client.py` | Anthropic client singleton |
| `tools/utils/voyage_client.py` | Voyage AI client (voyage-3.5, 1024 dims) |
| `tools/utils/apify_client.py` | Apify actor client |

---

## Database Schema

Migrations are in `supabase/migrations/`.

### Tables

#### `platforms` (lookup)

| Column | Type | Example |
|--------|------|---------|
| id | serial | 1 |
| name | text | "instagram" |
| display_name | text | "Instagram" |

Values: instagram (1), tiktok (2), youtube (3)

#### `content_types` (lookup)

| Column | Type | Example |
|--------|------|---------|
| id | serial | 1 |
| name | text | "caption" |
| display_name | text | "Caption" |

Values: caption (1), carousel (2), edm (3), reel_script (4)

#### `scraped_content`

Viral content from social platforms — the primary RAG source.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| platform_id | int | FK to platforms |
| source_url | text | Original post URL |
| source_handle | text | Account handle |
| content_text | text | Full post text |
| likes_count, comments_count, shares_count, views_count, saves_count | int | Engagement metrics |
| hashtags | text[] | Post hashtags |
| posted_at | timestamptz | When posted |
| embedding | vector(1024) | Voyage AI embedding |
| virality_score | float | Computed engagement score |

**Indexes**: HNSW on embedding (cosine), B-tree on platform_id, virality_score, posted_at

#### `brand_voice_profiles`

Brand voice analysis results.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| brand_handle | text | "@yoursalonsupport" |
| tone_attributes | jsonb | `{ authoritative: 0.8, warm: 0.9, ... }` |
| vocabulary_patterns | jsonb | Power words, avoided words, signatures |
| sentence_structure | jsonb | Avg word count, style, fragment usage |
| emoji_usage | jsonb | Frequency, preferred emojis |
| hashtag_strategy | jsonb | Count, types, placement |
| cta_patterns | jsonb | Styles, frequency |
| analysis_text | text | Full prose analysis |
| analysis_embedding | vector(1024) | Embedding of analysis text |
| source_posts_count | int | Number of posts analyzed |

#### `chat_sessions`

Groups related chat messages into sessions.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| title | text | First message truncated to 80 chars |
| content_type_id | int | FK to content_types |
| platform_id | int | FK to platforms |
| created_at | timestamptz | Session start time |

#### `chat_messages`

Individual messages within a session.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| session_id | uuid | FK to chat_sessions (CASCADE delete) |
| role | text | "user", "assistant", or "system" |
| content | text | Message body |
| model_used | text | "claude-sonnet-4-20250514" |
| rag_context_used | boolean | Whether RAG was applied |

#### `content_feedback`

User feedback on generated content — feeds back into RAG for improvement.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| content_type | text | "caption", "carousel", etc. |
| platform | text | "instagram", "tiktok", etc. |
| user_message | text | What user asked for |
| assistant_message | text | What was generated |
| rating | text | "positive" or "negative" |
| feedback_note | text | User's feedback comment |
| embedding | vector(1024) | Embedding of assistant output |

**Auto-detection**: The chat router automatically detects conversational feedback (short messages like "love it", "too formal", "shorter") and saves it without requiring explicit thumbs up/down.

#### `generated_content`

Stored copy outputs from generation.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| content_type_id | int | FK to content_types |
| platform_id | int | FK to platforms |
| body | text | The generated copy |
| slides | jsonb | Structured data for carousels/reels |
| prompt_used | text | Original user prompt |
| rating | int | User rating (1-5) |
| is_favorite | boolean | Saved to favorites |

#### `scrape_jobs`

Background scraping job tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| platform_id | int | FK to platforms |
| job_type | text | "viral_research", "brand_analysis", "competitor" |
| status | text | "pending", "running", "completed", "failed" |
| search_terms | text[] | Search queries |
| results_count | int | Items scraped |

#### `reports`

Generated analytics reports.

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| report_type | text | "content_audit", "competitor_analysis", "strategy" |
| title | text | Report title |
| full_content | text | Complete markdown report |

### Vector Search Functions

#### `match_content()`

Cosine similarity search over `scraped_content` embeddings.

```sql
SELECT * FROM match_content(
  query_embedding := <vector>,
  match_threshold := 0.3,
  match_count := 5,
  filter_platform_id := 1  -- optional
);
```

Returns: id, content_text, source_url, source_handle, platform_id, virality_score, similarity

#### `match_feedback()`

Cosine similarity search over `content_feedback` embeddings.

```sql
SELECT * FROM match_feedback(
  query_embedding := <vector>,
  match_threshold := 0.3,
  match_count := 5,
  filter_rating := 'positive',      -- optional
  filter_content_type := 'caption'   -- optional
);
```

Returns: id, content_type, platform, user_message, assistant_message, rating, feedback_note, similarity

---

## Content Types

### Caption

**Output format**: Plain text
**Structure**: Hook (1 line) → Body (2-4 short sentences) → CTA → Hashtags

### Carousel

**Output format**: Markdown with `---` slide separators
**Structure**: Title slide → Content slides (1 idea each, 5-6 slides) → CTA slide

### EDM (Email)

**Output format**: Markdown
**Structure**: Subject line → Preview text → Greeting → Hook → Body → CTA button → Sign-off → P.S.

### Reel Script

**Output format**: Markdown with timing markers
**Structure**: Hook (0-3s) → Scenes (3-25s each with voiceover, on-screen text, visuals) → CTA (3-5s)

---

## Deployment

Both frontend and backend are deployed to **Vercel**.

### Frontend (Next.js)

- **Project**: `yss-copywriter`
- **URL**: `https://yss-copywriter.vercel.app`
- **Runtime**: Vercel Next.js optimized
- **Deploy**: `cd frontend && vercel --prod`

### Backend (FastAPI)

- **Project**: `yss-copywriter-api`
- **URL**: `https://yss-copywriter-api.vercel.app`
- **Runtime**: `@vercel/python` via `api/index.py`
- **Config** (`vercel.json`):
  - Max function duration: 60s
  - Max lambda size: 15MB
  - Routes: `/api/v1/*` → `api/index.py`
- **Deploy**: `vercel --prod` (from project root)

### Important deployment notes

- Environment variables must be set with `printf` (not `echo`) to avoid trailing newlines that break API keys
- CORS origins in `backend/main.py` must include the Vercel frontend URL
- Frontend `BACKEND_URL` env var must point to the backend Vercel URL
- Supabase redirect URLs must include the Vercel frontend domain

---

## Workflows

Markdown SOPs in `workflows/` define step-by-step procedures:

| Workflow | Description |
|----------|-------------|
| `generate_copy.md` | Content generation (3 methods: chat UI, CLI, API) |
| `research_viral_content.md` | Scraping viral content from 3 platforms + embedding |
| `analyze_brand_voice.md` | Brand voice extraction from @yoursalonsupport posts |
| `generate_report.md` | Analytics report generation (3 report types) |
| `setup_database.md` | Initial Supabase database setup |

---

## File Structure

```
YSS Brand Content Copywriter/
├── api/
│   └── index.py                          # Vercel Python entry point
├── backend/
│   ├── main.py                           # FastAPI app + CORS + routers
│   ├── config.py                         # Pydantic settings from .env
│   ├── models/                           # Request/response models
│   │   ├── chat.py
│   │   ├── content.py
│   │   └── scraping.py
│   ├── routers/                          # API route handlers
│   │   ├── chat.py                       # Streaming, sessions, feedback
│   │   ├── content.py                    # Content CRUD, viral browsing
│   │   ├── scraping.py                   # Scrape job management
│   │   └── reports.py                    # Report generation
│   ├── services/                         # Business logic
│   │   ├── rag_service.py                # Vector search + context building
│   │   ├── research_service.py           # Perplexity API integration
│   │   └── scraping_service.py           # Scrape job orchestration
│   └── prompts/                          # LLM prompt templates
│       ├── system_prompt.py              # Master brand guide + RAG injection
│       ├── caption_prompt.py
│       ├── carousel_prompt.py
│       ├── edm_prompt.py
│       └── reel_script_prompt.py
├── frontend/
│   ├── src/
│   │   ├── app/                          # Next.js App Router pages
│   │   │   ├── page.tsx                  # Home (chat)
│   │   │   ├── dashboard/page.tsx        # Content dashboard
│   │   │   ├── reports/page.tsx          # Reports viewer
│   │   │   ├── admin/page.tsx            # Admin panel
│   │   │   ├── login/page.tsx            # Login page
│   │   │   └── api/                      # API proxy routes
│   │   ├── components/
│   │   │   ├── chat/                     # Chat UI components
│   │   │   │   ├── chat-interface.tsx     # Main chat component
│   │   │   │   ├── message-bubble.tsx     # Message rendering
│   │   │   │   ├── content-type-selector.tsx
│   │   │   │   └── copy-output-card.tsx
│   │   │   └── ui/                       # shadcn/ui components
│   │   ├── lib/
│   │   │   └── supabase/                 # Auth clients
│   │   └── middleware.ts                 # Auth middleware
│   ├── package.json
│   └── next.config.ts
├── tools/                                # Python CLI tools
│   ├── generate_copy.py
│   ├── generate_embeddings.py
│   ├── search_vectors.py
│   ├── analyze_brand_voice.py
│   ├── generate_report.py
│   ├── scrape_instagram.py
│   ├── scrape_tiktok.py
│   ├── scrape_youtube.py
│   ├── scrape_website.py
│   └── utils/                            # Shared clients
│       ├── supabase_client.py
│       ├── claude_client.py
│       ├── voyage_client.py
│       └── apify_client.py
├── workflows/                            # Markdown SOPs
├── supabase/migrations/                  # Database schema
├── vercel.json                           # Backend deployment config
├── requirements.txt                      # Python dependencies
├── .env                                  # Environment variables
└── CLAUDE.md                             # AI agent instructions
```
