# Workflow: Analyze Brand Voice

## Objective
Extract a structured brand voice profile from @yoursalonsupport's Instagram posts and website, storing it in Supabase for use in RAG-powered copy generation.

## When to Run
- **Initially**: Run once to create the first brand voice profile
- **Monthly**: Re-run to keep the voice profile current
- **After brand pivot**: Run if YSS changes their tone, messaging, or visual identity

## Steps

1. **Run the brand voice analysis tool**
   ```
   python tools/analyze_brand_voice.py --ig-limit 30 --website-pages 10
   ```

   This tool automatically:
   - Scrapes the latest 30 posts from @yoursalonsupport
   - Crawls yoursalonsupport.com (up to 10 pages)
   - Sends content to Claude for structured analysis
   - Generates an embedding of the analysis
   - Stores the profile in `brand_voice_profiles` table

2. **Review the analysis**
   - Check `.tmp/brand_voice_analysis.json`
   - Verify tone_attributes match what you'd expect from YSS
   - Confirm vocabulary_patterns include actual YSS terminology
   - Ensure writing_guidelines are specific (not generic marketing advice)

3. **Verify in Supabase**
   - Check `brand_voice_profiles` table has a new row
   - Confirm `analysis_embedding` is populated (1024 dims)

## Inputs
- Instagram handle: `yoursalonsupport` (hardcoded)
- Website: `https://yoursalonsupport.com` (hardcoded)

## Outputs
- `brand_voice_profiles` record in Supabase
- `.tmp/brand_voice_analysis.json` file

## Cost Estimates
- Apify (Instagram scraping): ~$2-5
- Claude API (analysis): ~$0.10-0.30
- Voyage AI (1 embedding): < $0.01

## Troubleshooting
- If Instagram scraping fails: Check Apify dashboard for actor status
- If website crawling returns little text: Some pages may be JS-rendered; consider using Apify web scraper instead
- If Claude JSON parsing fails: The tool has a fallback JSON extractor, but check Claude's output in logs
