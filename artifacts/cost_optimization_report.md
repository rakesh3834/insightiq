# Cost Optimization Report

- Baseline monthly cost: INR 4,500,000
- Optimized monthly cost: INR 2,400,000
- Monthly savings: INR 2,100,000
- Savings percentage: 46.7%

## Levers
- prompt caching for repeated business context
- batch processing for review and release summarization
- ThreadPoolExecutor for parallel IO-bound enrichment
- RAG metadata filtering before LLM calls
- response caching for stable dashboard narratives
- SQL-first metric computation before generation