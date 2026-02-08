# Workflow: Setup Supabase Database

## Objective
Initialize the Supabase database with the required schema for the YSS Content Copywriter system.

## Prerequisites
- Supabase project created at supabase.com
- Project URL and service role key added to `.env`

## Steps

1. **Log into Supabase Dashboard**
   - Go to your project > SQL Editor

2. **Run the migration**
   - Open `supabase/migrations/001_initial_schema.sql`
   - Paste the entire contents into the SQL Editor
   - Click "Run"

3. **Verify tables were created**
   - Go to Table Editor
   - Confirm these tables exist: `platforms`, `content_types`, `scraped_content`, `brand_voice_profiles`, `chat_sessions`, `chat_messages`, `generated_content`, `scrape_jobs`, `reports`

4. **Verify lookup data**
   - Check `platforms` has 3 rows (Instagram, TikTok, YouTube)
   - Check `content_types` has 4 rows (Caption, Carousel, EDM, Reel Script)

5. **Verify vector extension**
   - Run: `SELECT * FROM pg_extension WHERE extname = 'vector';`
   - Should return 1 row

6. **Verify RPC function**
   - Run: `SELECT routine_name FROM information_schema.routines WHERE routine_name = 'match_content';`
   - Should return 1 row

## Troubleshooting
- If `vector` extension fails: Enable it in Supabase Dashboard > Database > Extensions > Search "vector" > Enable
- If permission errors: Ensure you're using the service role key, not the anon key
