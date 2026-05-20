## BBC Article Acquisition Pipeline

Current implementation supports BBC sitemap-based article acquisition.

### Current Flow

BBC sitemap index  
→ child sitemap discovery  
→ article URL extraction  
→ publication-date filtering  
→ ingestion into PostgreSQL

---

### Run the Pipeline

```bash
python3 -m sentiment_analysis.articles.discover
