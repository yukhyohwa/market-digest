# Market Digest

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

`market-digest` is a standalone market-data collection and financial opportunity monitoring tool. It contains only the market workflow extracted from the former combined `news-market-digest` application.

The project collects market indicators, fund and bond data, and arbitrage signals, stores them in a market-only SQLite database, and produces a Markdown market report with supporting charts.

News RSS collection, article translation, news categorization, news persistence, and news reports are maintained in the separate [`news-digest`](../news-digest) project.

## Features

### Market and macro data

- Global market indices, including the FTSE 100
- Foreign-exchange rates collected from the configured market data sources
- US 10-year Treasury yield through Yahoo Finance's `^TNX` symbol
- Gold, silver, oil, and other configured commodity prices
- Historical trend charts for selected market series

The Yahoo Finance `^TNX` value is scaled by `0.1` to represent the Treasury yield percentage correctly.

### Fund and arbitrage monitoring

- QDII OTC subscription-limit status monitoring through Eastmoney fund information

### Economic calendar

- High- and medium-impact CNY, USD, JPY, and GBP events
- Remaining events in the current calendar week including today, with event times converted to China Standard Time
- Explicit distinction between no matching events and a failed calendar source

### Bond monitoring

- New bond issuance tracking

### Reporting and delivery

The market report is written as Markdown and includes market tables, strategy sections, source notes, and chart links. Email delivery is optional and is performed only after a report has been generated successfully.

## Project structure

```text
market-digest/
├── main.py
├── app/
│   ├── __init__.py
│   ├── collectors/
│   │   ├── market_indices.py      # Global indices and FTSE 100
│   │   ├── forex.py               # FX rates and US 10Y Treasury yield
│   │   ├── commodities.py         # Commodity prices
│   │   ├── economic_calendar.py   # Important events remaining this week
│   │   ├── qdii_otc_limits.py      # Eastmoney OTC subscription status
│   │   └── bond_issuance.py        # New bond issuance
│   └── core/
│       ├── db.py                   # Market-only SQLite schema and persistence
│       ├── arb_reporter.py         # Market opportunity formatting
│       ├── unified_reporter.py     # Market Markdown report generation
│       └── mailer.py               # Optional SMTP delivery
├── config/
│   └── settings.py                 # Strategy and local mail settings
├── data/
│   └── finance_data.db             # Market-only SQLite database
├── output/
│   ├── Market_Digest_YYYY-MM-DD.md
│   └── images/                     # Generated market charts
├── scripts/
│   ├── run_manual.bat              # Manual Windows launcher
│   ├── run_task.bat                # Task Scheduler launcher
│   └── update_env.bat              # Environment helper
└── requirements.txt
```

## Requirements

- Windows, Linux, or macOS
- Python 3.11 or newer recommended
- Network access to the configured market-data providers
- Access to the configured public market-data endpoints; providers may enforce rate limits
- Optional SMTP access for email delivery

Dependencies are declared in `requirements.txt`. The project uses packages including `requests`, `beautifulsoup4`, `yfinance`, `curl_cffi`, `python-dotenv`, and `markdown`.

## Installation

From the project directory:

```bash
python -m pip install -r requirements.txt
```

A virtual environment is recommended:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

On macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage

Run the complete market collection and report pipeline:

```bash
python main.py
```

Generate the market report and send it by email:

```bash
python main.py --mail
```

Display command-line options:

```bash
python main.py --help
```

The current entry point intentionally has no `--news`, `--arb`, or unified-news options. It runs the market collectors, initializes the market database, generates the market report, optionally sends it, and removes market chart images older than 30 days.

## Collection pipeline

A normal run performs these stages:

1. Initialize `data/finance_data.db`.
2. Run the configured new-bond, FX, commodity, index, economic-calendar, and QDII OTC-limit collectors.
3. Persist collector results in market-specific tables.
4. Build the market report from the stored/current market data.
5. Write the report to `output/` and charts to `output/images/`.
6. If `--mail` was supplied and mail credentials are configured, send the report.
7. Remove PNG chart files older than 30 days.

A failure in one collector is logged and does not automatically prevent the remaining collectors from running. A provider may still return incomplete data because of network errors, login limits, anti-bot checks, maintenance, or delayed market updates.

## Market database

The market database is:

```text
data/finance_data.db
```

It contains market-specific tables such as:

- `market_indices`
- `forex_rates`
- `commodities`
- `economic_calendar`
- `economic_calendar_status`
- `fund_otc_limits`
- `bond_issuance`

The database is intentionally separate from `news-digest/data/news_data.db`. Do not point either project at the other project's database.

## Configuration

Strategy thresholds and local settings are maintained in `config/settings.py`. Review the configuration before changing production or scheduled runs, especially:

- Output and email behavior

### Email configuration

Do not store passwords, app passwords, API keys, or tokens in source files. Configure the market mail settings through environment variables:

```text
MARKET_DIGEST_SENDER_EMAIL=[REDACTED]
MARKET_DIGEST_SENDER_PASSWORD=[REDACTED]
MARKET_DIGEST_RECEIVERS=recipient@example.com
```

For multiple recipients:

```text
MARKET_DIGEST_RECEIVERS=one@example.com,two@example.com
```

The default SMTP configuration uses Gmail SMTP over SSL. Change `SMTP_SERVER` and `SMTP_PORT` in `config/settings.py` when using a different provider.

### External data-source notes

- Yahoo Finance supplies the index and Treasury-yield series used by the report.
- The Eastmoney fund API supplies the current QDII OTC subscription status, including fields such as `SGZT`.
- Fair Economy supplies the public current-week economic calendar. Events are converted to China Standard Time and filtered from today through the end of the available week.
- A current OTC status is compared with local history to identify changes; the collector does not reconstruct a complete historical announcement archive from Eastmoney.

## Windows automation

The `scripts/` directory contains Windows batch launchers. Before using a batch file in Task Scheduler, verify that its command-line options match the current `main.py` entry point and that the **Start in** directory is the project root.

For a direct Task Scheduler action, the reliable equivalent is:

```text
Program/script: C:\Path\To\Python\python.exe
Arguments: main.py --mail
Start in: C:\Users\5xgames\Desktop\github\market-digest
```

Redirect logs to `output/` if a scheduled run needs persistent diagnostics. Ensure the scheduled account has access to the Python environment, database directory, and output directory.

## Troubleshooting

### A collector returns no data

Check network connectivity, provider availability, response changes, anti-bot protection, and request limits. Run the collector from the project root so relative paths resolve correctly.

### Yahoo Finance data is unavailable

Check the symbol, network access, and the installed `yfinance`/`curl_cffi` versions. The report can still be generated while one data source is unavailable, but the affected section may be empty or stale.

### The Treasury yield looks ten times too high or too low

The `^TNX` Yahoo value uses a different scale from a normal percentage display. The collector must retain the `0.1` conversion used by this project.

### Email delivery fails

Confirm that the `MARKET_DIGEST_*` variables are set in the same environment used by the command or Task Scheduler. Verify SMTP host, port, sender authorization, recipient formatting, and network access. Never expose the password in logs or issue reports.

## Relationship with news-digest

The responsibilities and databases are deliberately separated:

| Responsibility | Project | Database |
|---|---|---|
| RSS feeds, translation, filtering, categorization, news reports | `news-digest` | `data/news_data.db` |
| Market data, funds, bonds, commodities, arbitrage, market reports | `market-digest` | `data/finance_data.db` |

`market-digest` must not import the news fetcher, translator, processor, renderer, or news database. Use `news-digest` when the desired output is a news report.

## Data quality and investment disclaimer

Market data comes from third-party services and may be delayed, incomplete, unavailable, or subject to provider-specific definitions. Arbitrage calculations and screening results are informational and may omit fees, taxes, liquidity constraints, execution risk, settlement rules, subscription restrictions, and corporate-action details.

This project is for research and information purposes only. It is not investment advice, a solicitation, or a guarantee of returns. Verify all figures and conditions independently before making any financial decision.
