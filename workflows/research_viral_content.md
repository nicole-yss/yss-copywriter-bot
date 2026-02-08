# Workflow: Research Viral Content

## Objective
Scrape and store viral content from Instagram, TikTok, and YouTube in the salon/beauty niche for use as RAG context in copy generation.

## Inputs Required
- Search terms/hashtags for each platform
- Max results per platform (default: 100)

## Recommended Search Terms

**Instagram hashtags:**
salonowner, hairstylist, salonmarketing, salontips, beautybusiness, salonbusiness, hairsalonowner, salonlife, beautyentrepreneur, salonsoftware

**TikTok hashtags:**
salontok, salonowner, beautybusiness, hairtok, salonmarketing, salontips, hairstylistlife, beautyentrepreneur

**YouTube search terms:**
salon marketing tips, salon business growth, salon owner advice, hair salon social media, beauty business marketing, salon client retention

## Steps

1. **Run Instagram scraper**
   ```
   python tools/scrape_instagram.py --mode viral --hashtags "salonowner,hairstylist,salonmarketing,beautybusiness,salontips" --limit 100
   ```

2. **Run TikTok scraper**
   ```
   python tools/scrape_tiktok.py --mode viral --hashtags "salontok,salonowner,beautybusiness,salonmarketing" --limit 100
   ```

3. **Run YouTube scraper**
   ```
   python tools/scrape_youtube.py --mode search --terms "salon marketing tips,salon business growth,salon owner social media" --limit 50
   ```

4. **Generate embeddings for all new content**
   ```
   python tools/generate_embeddings.py --batch --unembedded
   ```

5. **Verify results**
   - Check Supabase `scraped_content` table for new rows
   - Run a test vector search: `python tools/search_vectors.py --query "salon growth tips" --limit 5`

## Error Handling
- If Apify rate-limits: wait 60 seconds and retry once
- If Apify actor fails: log error, continue with other platforms
- If embedding fails: content is stored without embedding, run `--batch --unembedded` again later

## Schedule
Run weekly (Mondays) to keep the research corpus fresh.

## Cost Estimates
- Apify: ~$5-15 per full run (depends on results count)
- Voyage AI embeddings: ~$0.01-0.05 per batch of 300 texts
