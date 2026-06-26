"""FastAPI service layer for daily-stock-analysis.

Wraps the existing engine (data_fetcher, news_fetcher, analyzer, shared.gaps)
behind a REST API. US + EU only, local run.
"""
