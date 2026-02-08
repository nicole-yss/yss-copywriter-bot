# Workflow: Generate Reports

## Objective
Generate analytics reports that provide actionable insights for improving YSS's social media presence.

## Prerequisites
- Viral content has been scraped (see `research_viral_content.md`)
- Brand voice has been analyzed (see `analyze_brand_voice.md`)
- Some generated content exists for meaningful audit (optional)

## Report Types

### 1. Content Audit
Analyzes viral content patterns and benchmarks YSS performance.
```
python tools/generate_report.py --type content_audit
```

### 2. Competitor Analysis
Identifies top performers in the salon niche and their strategies.
```
python tools/generate_report.py --type competitor_analysis
```

### 3. Content Strategy
Provides a full strategic content plan with pillars, calendar, and KPIs.
```
python tools/generate_report.py --type strategy
```

## Via API
```bash
# Trigger report generation (runs in background)
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"report_type": "strategy"}'

# List reports
curl http://localhost:8000/api/v1/reports/

# Get specific report
curl http://localhost:8000/api/v1/reports/{report_id}
```

## Outputs
- Stored in Supabase `reports` table
- Markdown file saved to `.tmp/reports/`
- Viewable at `http://localhost:3000/reports`

## Schedule
- **Content Audit**: Monthly
- **Competitor Analysis**: Quarterly
- **Strategy Report**: Quarterly (or after major viral content research refresh)

## Cost Estimates
- Claude API (report generation): ~$0.20-0.50 per report (large context)
