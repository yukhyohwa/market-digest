
import os
import datetime
from app.core.arb_reporter import fetch_daily_data, fetch_daily_status, format_table, get_previous_otc_status
import re

def extract_quota(status_str):
    if not status_str:
        return 'Unknown'
    match = re.search(r'上限([\d\.]+)元', status_str)
    if match:
        return match.group(1)
    if '暂停' in status_str:
        return 'Suspended'
    if '开放' in status_str:
        return 'Open'
    return status_str

def generate_unified_report(include_arb=True):
    """
    Generate the market-only Markdown report.
    """
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"Market_Digest_{today}.md")
    
    report_content = f"# Market_Digest_{today}\n\n"
    
    # 1. Arbitrage Section (from DB)
    if include_arb:
        # 1. Market Indices (Global)
        report_content += "### 1. Market Indices (Global)\n"
        indices_chart_path = os.path.join(output_dir, 'images', f'market_indices_{today}.png')
        if os.path.exists(indices_chart_path):
            report_content += f'<img src="images/market_indices_{today}.png" alt="Market Indices 30-Day Trend" style="width:66.67%;max-width:100%;height:auto;">\n\n'
        else:
            report_content += "*No market index data or chart available.*\n\n"

        # 2. Commodities
        report_content += "### 2. Commodities\n"
        commodities_chart_path = os.path.join(output_dir, 'images', f'commodities_{today}.png')
        if os.path.exists(commodities_chart_path):
            report_content += f'<img src="images/commodities_{today}.png" alt="Commodities 30-Day Trend" style="width:66.67%;max-width:100%;height:auto;">\n\n'
        else:
            report_content += "*No commodities chart available.*\n\n"

        # 3. Forex Rates & US 10Y Treasury Yield
        report_content += "### 3. Global Forex Rates & US 10Y Treasury Yield\n"
        forex_chart_path = os.path.join(output_dir, 'images', f'forex_rates_{today}.png')
        if os.path.exists(forex_chart_path):
            report_content += f'<img src="images/forex_rates_{today}.png" alt="Global Forex Rates and US 10Y Treasury Yield 30-Day Trend" style="width:66.67%;max-width:100%;height:auto;">\n\n'
        else:
            report_content += "*No forex chart available.*\n\n"

        # 4. QDII OTC Fund Limits Monitor
        report_content += "### 4. QDII OTC Fund Limits Monitor\n"
        rows, cols = fetch_daily_data('fund_otc_limits', today)
        if rows:
            display_rows = []
            for r in rows:
                fund_code, fund_name, nav, status = r[1], r[2], r[3], r[4]
                prev_status = get_previous_otc_status(fund_code, today)
                # Only show if status has changed
                if prev_status is None or status != prev_status:
                    old_quota = extract_quota(prev_status)
                    new_quota = extract_quota(status)
                    diff_str = f"{old_quota} -> {new_quota}"
                    display_rows.append([fund_code, fund_name, f"{nav:.4f}", status, diff_str])
                    
            if display_rows:
                report_content += format_table(display_rows, ['Fund Code', 'Fund Name', 'NAV', 'Status', 'Quota Diff'], ['left', 'left', 'right', 'left', 'left']) + "\n\n"
            else:
                report_content += "*No limit changes detected since last week.*\n\n"
        else:
            report_content += "*No OTC Fund status data available today.*\n\n"

        # 5. Bond Issuance
        report_content += "### 5. Bond Issuance & Listing\n"
        rows, cols = fetch_daily_data('bond_issuance', today)
        if rows:
            display_rows = [[r[1], r[2], r[3], r[4], r[5]] for r in rows]
            report_content += format_table(display_rows, ['Code', 'Name', 'Sub Date', 'List Date', 'Details'], ['left', 'left', 'left', 'left', 'left']) + "\n\n"
        else:
            report_content += "*No new bond events for today.*\n\n"

        # 6. Important Economic Events (last report section)
        report_content += "### 6. 本周剩余重要经济事件（含今日）\n"
        rows, cols = fetch_daily_data(
            'economic_calendar',
            today,
            "event_time, country, impact, title, forecast, previous",
        )
        if rows:
            display_rows = [[r[0], r[1], r[2], r[3], r[4], r[5]] for r in rows]
            report_content += format_table(
                display_rows,
                ['北京时间', '地区', '影响', '事件', '预期', '前值'],
                ['left', 'center', 'center', 'left', 'right', 'right'],
            ) + "\n\n"
            report_content += "> 事件来自 Fair Economy 公开周历并转换为北京时间；仅覆盖本周，预期值可能更新，重要事件请再核对官方公告。\n\n"
        else:
            calendar_status = fetch_daily_status('economic_calendar_status', today)
            if calendar_status and calendar_status['ok']:
                report_content += "*当前周历未发现本周剩余的中高影响事件。*\n\n"
            else:
                report_content += "*经济日历源本次失败或尚未运行，不能解释为本周没有重要事件。*\n\n"

    # Sources
    report_content += "## 📚 Sources\n"
    report_content += "- **Market Data**: Yahoo Finance, Bank of China, Eastmoney, Fair Economy\n"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return filename
