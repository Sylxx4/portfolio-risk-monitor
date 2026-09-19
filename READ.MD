# Portfolio Risk Monitor

A tool that pulls real market data and reports how a stock portfolio is
performing and how risky it is. Built for CIS 4930 (Programming for FinTech).

Given a set of tickers and weights, it computes returns, volatility,
correlations, inflation-adjusted performance, and a Monte Carlo projection of
future balances, then serves them through an API and a dashboard.

## Data sources

- Alpaca Market Data API — daily price bars
- FRED API — risk-free rate and CPI

## Requirements

- Python 3.10 or higher

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the tests

```bash
pytest
```

## Project status

In development. Built in phases: data layer, analytics, API, dashboard, then
containerized and deployed.