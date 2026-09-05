from django.shortcuts import render
from .processor.loadReferential import loadStock
from django.http import HttpResponse, JsonResponse
# Create your views here.
from django.shortcuts import render, HttpResponseRedirect
import json
import math
import pandas as pd
import yfinance as yf
from .models import securitydescription
from .serializers import securitydescriptionSerializer
from historical_price.models import historical_price
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from strategy.models import strategy_backtested
from strategy.processor.backtest import computeResultBacktest ,computeResultBacktestbigdrop


def _build_indicator_summary(rows):
    if not rows:
        return {
            'trade_count': 0,
            'win_rate': 0.0,
            'avg_return': 0.0,
            'best_return': 0.0,
            'worst_return': 0.0,
            'params_label': 'No params',
        }

    return_pct_values = []
    params_label = 'No params'
    for row in rows:
        if row.get('buy_price') and row.get('sell_price'):
            return_pct = ((row['sell_price'] - row['buy_price']) / row['buy_price']) * 100
            if return_pct > 300 or return_pct < -80:
                continue
            return_pct_values.append(return_pct)
        if not params_label or params_label == 'No params':
            params_label = _format_strategy_params(row)

    trade_count = len(return_pct_values)
    if trade_count == 0:
        return {
            'trade_count': 0,
            'win_rate': 0.0,
            'avg_return': 0.0,
            'best_return': 0.0,
            'worst_return': 0.0,
            'params_label': params_label,
        }

    win_count = sum(1 for value in return_pct_values if value > 0)
    return {
        'trade_count': trade_count,
        'win_rate': round((win_count * 100.0) / trade_count, 2),
        'avg_return': round(sum(return_pct_values) / trade_count, 2),
        'best_return': round(max(return_pct_values), 2),
        'worst_return': round(min(return_pct_values), 2),
        'params_label': params_label,
    }


def _format_market_cap(value):
    if value is None:
        return 'N/A'
    if value >= 1e12:
        return f"{value / 1e12:.1f}T"
    if value >= 1e9:
        return f"{value / 1e9:.1f}B"
    if value >= 1e6:
        return f"{value / 1e6:.1f}M"
    return f"{value:,.0f}"


def _build_portfolio_summary(selected_positions, selected_indicator, min_trade_count, candidate_count):
    if not selected_positions:
        return {
            'headline': 'No portfolio candidates met the current quality floor.',
            'bullets': [
                'Try lowering the minimum trade threshold or widening the history window.',
                'The current filter is too strict for a sustainable retail basket.',
            ],
            'why_strategy': [
                'The portfolio engine needs at least one qualifying ticker to build a candidate list.',
            ],
        }

    average_score = round(sum(pos['score'] for pos in selected_positions) / len(selected_positions), 2)
    average_trade_count = round(sum(pos['trade_count'] for pos in selected_positions) / len(selected_positions), 2)
    average_win_rate = round(sum(pos['win_rate'] for pos in selected_positions) / len(selected_positions), 2)
    sector_names = sorted({pos.get('sector') or 'Unclassified' for pos in selected_positions if pos.get('sector')})
    sector_summary = ', '.join(sector_names[:4]) if sector_names else 'Diversified mix'
    if len(sector_names) > 4:
        sector_summary += f' + {len(sector_names) - 4} more'

    return {
        'headline': f'{selected_indicator} creates a retail-ready basket for the next 12 months',
        'bullets': [
            f'{len(selected_positions)} positions were selected from {candidate_count} qualified candidates.',
            f'Every position cleared the {min_trade_count}+ trade floor and stayed within the conservative return envelope used by the backtest screen.',
            f'The blend spans {len(sector_names)} sectors such as {sector_summary}.',
            'Weights favor repeatable winners over isolated spikes, which makes the portfolio more durable for a retail-style allocation.',
        ],
        'why_strategy': [
            f'The strategy produced an average of {average_trade_count:.1f} trades per ticker and a {average_win_rate:.1f}% win-rate across the selected basket.',
            f'With an average composite score of {average_score:.1f}, this mix is stronger than the raw leaderboard because it balances return and consistency.',
        ],
    }


def loadstatic(request):
    loadStock()
    return HttpResponse("OK")


@csrf_exempt
def get_data(request):
    data = securitydescription.objects.all()
    if request.method == 'GET':
        serializer = securitydescriptionSerializer(data, many=True)
        return JsonResponse(serializer.data, safe=False)
    
    
def viewDashboard(request):
    data2=securitydescription.objects.all().values()
    print(data2)
    
    histo=historical_price.objects.filter(yahoo_id='BTC').order_by('spot_date').values()
    df=pd.DataFrame(histo)
    labels=[]
    chartdata=[]
    for i in range(0, df['spot_date'].count()):
        labels.append(str(df['spot_date'][i]))
        chartdata.append(df['close_price'][i])
         
    chartLabel = "Historical Price"
     
    data ={ 
                     "labels":labels, 
                     "chartLabel":chartLabel, 
                     "chartdata":chartdata,
                     'name': 'BTC', 
             } 
    
    
    return render(request, 'dashboard.html',{'data2': data2, 'labels': labels,'histo': histo, 'data': data})

def viewsWelcome(request):
    data2=securitydescription.objects.filter(industry_level_1='Gambling').values()
    df=pd.DataFrame(data2)
    return HttpResponse(df.to_html())

def view_backtester(request):
    data2=computeResultBacktestbigdrop()
    
    data_result=data2.values()
    histo=historical_price.objects.filter(yahoo_id='ALK').order_by('spot_date').values()
    df=pd.DataFrame(histo)
    labels=[]
    chartdata=[]
    for i in range(0, df['spot_date'].count()):
        labels.append(str(df['spot_date'][i]))
        chartdata.append(df['close_price'][i])
         
    chartLabel = "Historical Price"
     
    data ={ 
                     "labels":labels, 
                     "chartLabel":chartLabel, 
                     "chartdata":chartdata,
                     'name': 'ALK', 
             } 
    
    
    return render(request, 'backtest_result.html',{'data_result': data_result, 'labels': labels,'histo': histo, 'data': data})


def view_indicator_compare(request):
    max_reasonable_return = 10.0
    ticker = request.GET.get('ticker')
    if not ticker:
        best_trade = None
        best_return = None
        for trade in strategy_backtested.objects.filter(
            name='indicator_2y',
            buy_price__isnull=False,
            sell_price__isnull=False,
        ).values('yahoo_id', 'buy_price', 'sell_price'):
            trade_return = None
            if trade['buy_price']:
                trade_return = (trade['sell_price'] - trade['buy_price']) / trade['buy_price']
            if trade_return is None or trade_return <= 0 or trade_return > max_reasonable_return:
                continue
            if best_return is None or trade_return > best_return:
                best_return = trade_return
                best_trade = trade
        if best_trade is None:
            return HttpResponse('No indicator backtest results found')
        ticker = best_trade['yahoo_id']

    histo = historical_price.objects.filter(yahoo_id=ticker).order_by('spot_date').values('spot_date', 'close_price')
    df = pd.DataFrame(histo)
    if df.empty:
        return HttpResponse('No historical price found for ' + ticker)

    labels = [str(d) for d in df['spot_date']]
    base_price = float(df['close_price'].iloc[0])
    stockdata = [round((float(price) / base_price) * 100, 4) for price in df['close_price']]

    trades = strategy_backtested.objects.filter(
        name='indicator_2y',
        yahoo_id=ticker,
        buy_price__isnull=False,
        sell_price__isnull=False,
    ).order_by('buy_date').values('buy_date', 'sell_date', 'buy_price', 'sell_price', 'indicator_name')

    trade_points = []
    for trade in trades:
        trade_points.append({
            'x': str(trade['buy_date']),
            'y': round((float(trade['buy_price']) / base_price) * 100, 4),
            'type': 'buy',
            'indicator': trade['indicator_name'],
        })
        trade_points.append({
            'x': str(trade['sell_date']),
            'y': round((float(trade['sell_price']) / base_price) * 100, 4),
            'type': 'sell',
            'indicator': trade['indicator_name'],
        })

    data = {
        'labels': labels,
        'stockdata': stockdata,
        'trade_points': trade_points,
        'base_price': base_price,
        'name': ticker,
    }
    return render(request, 'indicator_compare.html', {'data': data, 'ticker': ticker, 'trades': trades})


def view_indicator_review(request):
    ticker = request.GET.get('ticker') or ''
    indicator_name = request.GET.get('indicator') or 'multi_indicator_combo'
    payload = _build_indicator_review_payload(ticker, indicator_name)
    if payload.get('error'):
        return HttpResponse(payload['error'])

    chart_data_payload = {
        'labels': json.dumps(payload['labels']),
        'stockdata': json.dumps(payload['stockdata']),
        'strategydata': json.dumps(payload['strategydata']),
        'trade_points': json.dumps(payload['trade_points']),
        'buy_points': json.dumps(payload['buy_points']),
        'sell_points': json.dumps(payload['sell_points']),
        'name': payload['ticker'],
    }
    return render(
        request,
        'indicator_review.html',
        {
            'data': chart_data_payload,
            'ticker': payload['ticker'],
            'results': payload['rows'][:50],
            'all_tickers': payload['all_tickers'],
            'all_stock_rows': payload['all_stock_rows'],
            'indicator_names': payload['indicator_names'],
            'selected_indicator': payload['indicator_name'],
            'indicator_groups': payload['indicator_groups'],
            'selected_trades': payload['selected_trades'],
            'selected_indicator_summary': payload['selected_indicator_summary'],
        },
    )


def view_indicator_chart_data(request):
    ticker = request.GET.get('ticker') or ''
    indicator_name = request.GET.get('indicator') or 'multi_indicator_combo'
    payload = _build_indicator_review_payload(ticker, indicator_name)
    if payload.get('error'):
        return JsonResponse({'error': payload['error']}, status=404)
    return JsonResponse(payload)


def _format_strategy_params(trade_row):
    param_fields = ['param_1', 'param_2', 'param_3', 'param_4', 'param_5', 'param_6', 'param_7']
    params = []
    for index, field_name in enumerate(param_fields, start=1):
        value = trade_row.get(field_name)
        if value is None:
            continue
        params.append('p' + str(index) + '=' + str(value))
    return ', '.join(params) if params else 'No params'


def _sanitize_numeric_value(value, precision=4):
    if value is None:
        return None
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric_value):
        return None
    return round(numeric_value, precision)


def _sanitize_numeric_list(values, precision=4):
    return [_sanitize_numeric_value(value, precision=precision) for value in values]


def _build_indicator_review_payload(ticker, indicator_name, max_reasonable_return=10.0):
    rows = []
    for trade in strategy_backtested.objects.filter(
        name='indicator_2y',
        buy_price__isnull=False,
        sell_price__isnull=False,
    ).values('yahoo_id', 'indicator_name', 'buy_date', 'sell_date', 'buy_price', 'sell_price', 'param_1', 'param_2', 'param_3', 'param_4', 'param_5', 'param_6', 'param_7'):
        if not trade['buy_price'] or not trade['sell_price']:
            continue
        return_pct = ((trade['sell_price'] - trade['buy_price']) / trade['buy_price']) * 100
        if return_pct <= 0 or return_pct > (max_reasonable_return * 100):
            continue
        trade['return_pct'] = round(return_pct, 2)
        rows.append(trade)

    rows.sort(key=lambda item: item['return_pct'], reverse=True)
    if not rows:
        return {'error': 'No indicator backtest results found'}

    all_tickers = sorted(set(row['yahoo_id'] for row in rows))
    if ticker not in all_tickers:
        ticker = rows[0]['yahoo_id']

    ticker_rows = [row for row in rows if row['yahoo_id'] == ticker]
    indicator_names = sorted(set(row['indicator_name'] for row in ticker_rows))
    if indicator_name not in indicator_names:
        indicator_name = indicator_names[0] if indicator_names else ''

    indicator_groups = []
    for indicator in indicator_names:
        grouped_rows = [row for row in ticker_rows if row['indicator_name'] == indicator][:25]
        indicator_groups.append((indicator, grouped_rows))

    all_stock_rows = rows[:300]

    try:
        live_df = pd.DataFrame(yf.Ticker(str(ticker)).history(period='3y', auto_adjust=True))
        if live_df.empty:
            raise ValueError('No live price history')
        live_df = live_df.reset_index()
        date_col = 'Date' if 'Date' in live_df.columns else 'Datetime'
        live_df[date_col] = pd.to_datetime(live_df[date_col]).dt.date
        date_list = list(live_df[date_col])
        close_series = [float(price) for price in live_df['Close']]
    except Exception:
        histo = historical_price.objects.filter(yahoo_id=ticker).order_by('spot_date').values('spot_date', 'close_price')
        df = pd.DataFrame(histo)
        if df.empty:
            return {'error': 'No historical price found for ' + ticker}
        date_list = [pd.Timestamp(d).date() for d in df['spot_date']]
        close_series = [float(price) for price in df['close_price']]

    if not date_list or not close_series:
        return {'error': 'No historical price found for ' + ticker}

    labels = [str(d) for d in date_list]
    base_price = close_series[0]
    if not base_price or base_price <= 0:
        return {'error': 'No usable price history for ' + ticker}

    stockdata = _sanitize_numeric_list([(price / base_price) * 100 for price in close_series], precision=4)
    available_dates = sorted(date_list)
    available_date_set = set(available_dates)

    def _align_to_market_date(raw_date):
        trade_date = pd.Timestamp(raw_date).date()
        if trade_date in available_date_set:
            return trade_date
        previous_dates = [d for d in available_dates if d <= trade_date]
        if previous_dates:
            return previous_dates[-1]
        return available_dates[0]

    selected_trades = [row for row in ticker_rows if row['indicator_name'] == indicator_name]
    trade_points = []
    for trade in selected_trades:
        aligned_buy_date = _align_to_market_date(trade['buy_date'])
        aligned_sell_date = _align_to_market_date(trade['sell_date'])
        trade_points.append({
            'x': str(aligned_buy_date),
            'y': _sanitize_numeric_value((float(trade['buy_price']) / base_price) * 100, precision=4),
            'type': 'buy',
            'indicator': trade['indicator_name'],
            'date': str(aligned_buy_date),
            'price': _sanitize_numeric_value(float(trade['buy_price']), precision=6),
            'return_pct': '',
        })
        trade_points.append({
            'x': str(aligned_sell_date),
            'y': _sanitize_numeric_value((float(trade['sell_price']) / base_price) * 100, precision=4),
            'type': 'sell',
            'indicator': trade['indicator_name'],
            'date': str(aligned_sell_date),
            'price': _sanitize_numeric_value(float(trade['sell_price']), precision=6),
            'return_pct': _sanitize_numeric_value((((float(trade['sell_price']) - float(trade['buy_price'])) / float(trade['buy_price'])) * 100), precision=2),
        })

    strategy_curve = []
    buy_points = []
    sell_points = []
    if selected_trades:
        trade_by_buy = {_align_to_market_date(trade['buy_date']): trade for trade in selected_trades}
        trade_by_sell = {_align_to_market_date(trade['sell_date']): trade for trade in selected_trades}
        equity_base = 100.0
        holding = False
        entry_price = None

        for current_date, close_price in zip(date_list, close_series):
            if current_date in trade_by_buy and not holding:
                holding = True
                buy_trade = trade_by_buy[current_date]
                entry_price = float(buy_trade['buy_price'])
                buy_points.append({
                    'x': str(current_date),
                    'y': _sanitize_numeric_value((entry_price / base_price) * 100, precision=4),
                    'date': str(current_date),
                    'price': _sanitize_numeric_value(entry_price, precision=6),
                    'return_pct': '',
                    'indicator': buy_trade['indicator_name'],
                })

            if holding and entry_price:
                strategy_value = equity_base * (close_price / entry_price)
            else:
                strategy_value = equity_base

            strategy_curve.append(_sanitize_numeric_value(strategy_value, precision=4))

            if current_date in trade_by_sell and holding:
                sell_trade = trade_by_sell[current_date]
                sell_price = float(sell_trade['sell_price'])
                sell_points.append({
                    'x': str(current_date),
                    'y': _sanitize_numeric_value((sell_price / base_price) * 100, precision=4),
                    'date': str(current_date),
                    'price': _sanitize_numeric_value(sell_price, precision=6),
                    'return_pct': _sanitize_numeric_value(((sell_price - entry_price) / entry_price) * 100, precision=2),
                    'indicator': sell_trade['indicator_name'],
                })
                equity_base = equity_base * (float(sell_trade['sell_price']) / entry_price)
                holding = False
                entry_price = None

    selected_indicator_summary = _build_indicator_summary(selected_trades)
    return {
        'ticker': ticker,
        'indicator_name': indicator_name,
        'indicator_names': indicator_names,
        'all_tickers': all_tickers,
        'indicator_groups': indicator_groups,
        'all_stock_rows': all_stock_rows,
        'selected_trades': selected_trades,
        'selected_indicator_summary': selected_indicator_summary,
        'labels': labels,
        'stockdata': stockdata,
        'strategydata': strategy_curve if strategy_curve else stockdata,
        'trade_points': trade_points,
        'buy_points': buy_points,
        'sell_points': sell_points,
        'base_price': base_price,
        'rows': rows,
    }


def view_strategy_params_dashboard(request):
    dataset_names = sorted(strategy_backtested.objects.values_list('name', flat=True).distinct())
    if not dataset_names:
        return HttpResponse('No backtest data found')

    selected_dataset = request.GET.get('name') or 'indicator_2y'
    if selected_dataset not in dataset_names:
        selected_dataset = dataset_names[0]

    all_rows = list(
        strategy_backtested.objects.filter(name=selected_dataset).values(
            'name',
            'yahoo_id',
            'indicator_name',
            'param_1',
            'param_2',
            'param_3',
            'param_4',
            'param_5',
            'param_6',
            'param_7',
            'buy_date',
            'sell_date',
            'buy_price',
            'sell_price',
        )
    )
    if not all_rows:
        return HttpResponse('No rows found for dataset ' + selected_dataset)

    indicator_names = sorted(set(row['indicator_name'] for row in all_rows))
    selected_indicator = request.GET.get('indicator') or 'all'
    if selected_indicator != 'all' and selected_indicator not in indicator_names:
        selected_indicator = 'all'

    filtered_rows = all_rows
    if selected_indicator != 'all':
        filtered_rows = [row for row in all_rows if row['indicator_name'] == selected_indicator]

    grouped_stats = {}
    trade_rows = []
    for row in filtered_rows:
        params_label = _format_strategy_params(row)
        group_key = (row['indicator_name'], params_label)
        if group_key not in grouped_stats:
            grouped_stats[group_key] = {
                'indicator_name': row['indicator_name'],
                'params_label': params_label,
                'row_count': 0,
                'trade_count': 0,
                'win_count': 0,
                'returns': [],
                'tickers': set(),
            }

        grouped_stats[group_key]['row_count'] += 1
        grouped_stats[group_key]['tickers'].add(row['yahoo_id'])

        buy_price = row['buy_price']
        sell_price = row['sell_price']
        if not buy_price or not sell_price:
            continue

        return_pct = ((sell_price - buy_price) / buy_price) * 100
        grouped_stats[group_key]['trade_count'] += 1
        grouped_stats[group_key]['returns'].append(return_pct)
        if return_pct > 0:
            grouped_stats[group_key]['win_count'] += 1

        trade_copy = dict(row)
        trade_copy['params_label'] = params_label
        trade_copy['return_pct'] = round(return_pct, 2)
        trade_rows.append(trade_copy)

    strategy_summary = []
    for stat in grouped_stats.values():
        returns = stat['returns']
        trade_count = stat['trade_count']
        win_count = stat['win_count']
        strategy_summary.append({
            'indicator_name': stat['indicator_name'],
            'params_label': stat['params_label'],
            'row_count': stat['row_count'],
            'trade_count': trade_count,
            'ticker_count': len(stat['tickers']),
            'win_rate': round((win_count * 100.0 / trade_count), 2) if trade_count else 0.0,
            'avg_return': round(sum(returns) / trade_count, 2) if trade_count else 0.0,
            'best_return': round(max(returns), 2) if trade_count else 0.0,
            'worst_return': round(min(returns), 2) if trade_count else 0.0,
        })

    strategy_summary.sort(key=lambda item: (item['indicator_name'], -item['avg_return']))
    trade_rows.sort(key=lambda item: item['return_pct'], reverse=True)

    return render(
        request,
        'strategy_params_dashboard.html',
        {
            'dataset_names': dataset_names,
            'selected_dataset': selected_dataset,
            'indicator_names': indicator_names,
            'selected_indicator': selected_indicator,
            'strategy_summary': strategy_summary,
            'trade_rows': trade_rows[:500],
        },
    )


def view_next_year_portfolio(request):
    selected_dataset = request.GET.get('name') or 'indicator_2y'
    selected_indicator = request.GET.get('indicator') or 'multi_indicator_combo'
    try:
        max_positions = int(request.GET.get('positions', 12))
    except ValueError:
        max_positions = 12
    max_positions = max(5, min(max_positions, 25))

    try:
        min_trade_count = int(request.GET.get('min_trades', 5))
    except ValueError:
        min_trade_count = 5
    min_trade_count = max(1, min(min_trade_count, 20))

    try:
        history_years = int(request.GET.get('history_years', 3))
    except ValueError:
        history_years = 3
    history_years = max(1, min(history_years, 5))

    dataset_names = sorted(strategy_backtested.objects.values_list('name', flat=True).distinct())
    indicator_names = sorted(
        strategy_backtested.objects.filter(name=selected_dataset).values_list('indicator_name', flat=True).distinct()
    )
    if not indicator_names:
        indicator_names = ['multi_indicator_combo']
    if selected_indicator not in indicator_names:
        selected_indicator = indicator_names[0]

    all_rows = list(
        strategy_backtested.objects.filter(
            name=selected_dataset,
            indicator_name=selected_indicator,
            buy_price__isnull=False,
            sell_price__isnull=False,
        ).values(
            'yahoo_id',
            'buy_price',
            'sell_price',
            'buy_date',
            'sell_date',
            'param_1',
            'param_2',
            'param_3',
            'param_4',
            'param_5',
            'param_6',
            'param_7',
        )
    )
    if not all_rows:
        payload = {
            'selected_dataset': selected_dataset,
            'selected_indicator': selected_indicator,
            'max_positions': max_positions,
            'min_trade_count': min_trade_count,
            'history_years': history_years,
            'positions': [],
            'summary': {'candidate_count': 0, 'selected_count': 0},
            'dataset_names': dataset_names,
            'indicator_names': indicator_names,
            'portfolio_summary': _build_portfolio_summary([], selected_indicator, min_trade_count, 0),
        }
        if request.GET.get('format') == 'json':
            return JsonResponse(payload)
        return render(
            request,
            'portfolio_next_year.html',
            {
                **payload,
                'initial_portfolio_data': json.dumps(payload),
            },
        )

    ticker_stats = {}
    for row in all_rows:
        buy_price = row['buy_price']
        sell_price = row['sell_price']
        if not buy_price or not sell_price:
            continue
        return_pct = ((sell_price - buy_price) / buy_price) * 100
        if return_pct > 300 or return_pct < -80:
            continue

        ticker = row['yahoo_id']
        if ticker not in ticker_stats:
            ticker_stats[ticker] = {
                'ticker': ticker,
                'trade_count': 0,
                'win_count': 0,
                'returns': [],
                'params_label': _format_strategy_params(row),
            }
        ticker_stats[ticker]['trade_count'] += 1
        ticker_stats[ticker]['returns'].append(return_pct)
        if return_pct > 0:
            ticker_stats[ticker]['win_count'] += 1

    candidates = []
    for stat in ticker_stats.values():
        trade_count = stat['trade_count']
        if trade_count < min_trade_count:
            continue
        avg_return = sum(stat['returns']) / trade_count
        win_rate = (stat['win_count'] * 100.0) / trade_count
        score = (avg_return * 0.55) + (win_rate * 0.45)
        if score <= 0:
            continue
        candidates.append({
            'ticker': stat['ticker'],
            'trade_count': trade_count,
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 2),
            'best_return': round(max(stat['returns']), 2),
            'worst_return': round(min(stat['returns']), 2),
            'score': round(score, 2),
            'params_label': stat['params_label'],
            'history_years': history_years,
        })

    candidates.sort(key=lambda item: item['score'], reverse=True)
    selected_positions = candidates[:max_positions]
    score_total = sum(position['score'] for position in selected_positions)
    if score_total <= 0:
        equal_weight = round(100.0 / len(selected_positions), 2)
        for position in selected_positions:
            position['weight_pct'] = equal_weight
    else:
        running_weight = 0.0
        for index, position in enumerate(selected_positions):
            if index == len(selected_positions) - 1:
                position['weight_pct'] = round(100.0 - running_weight, 2)
            else:
                weight = round((position['score'] / score_total) * 100.0, 2)
                position['weight_pct'] = weight
                running_weight += weight

    ticker_ids = [position['ticker'] for position in selected_positions]
    security_lookup = {}
    if ticker_ids:
        for security_row in securitydescription.objects.filter(yahoo_id__in=ticker_ids).values(
            'yahoo_id', 'name', 'sector_level_1', 'industry_level_1', 'market_place', 'country', 'market_cap'
        ):
            security_lookup[security_row['yahoo_id']] = security_row

    for position in selected_positions:
        security_row = security_lookup.get(position['ticker'])
        if security_row:
            position['company_name'] = security_row['name']
            position['sector'] = security_row['sector_level_1']
            position['industry'] = security_row['industry_level_1']
            position['market_place'] = security_row['market_place']
            position['country'] = security_row['country']
            position['market_cap'] = security_row['market_cap']
            position['market_cap_label'] = _format_market_cap(security_row['market_cap'])
        else:
            position['company_name'] = position['ticker']
            position['sector'] = 'Unclassified'
            position['industry'] = 'Unclassified'
            position['market_place'] = None
            position['country'] = None
            position['market_cap'] = None
            position['market_cap_label'] = 'N/A'
        position['detail_reason'] = (
            f'{position["trade_count"]} trades • {position["win_rate"]}% win rate • '
            f'{position["avg_return"]}% average return'
        )

    payload = {
        'selected_dataset': selected_dataset,
        'selected_indicator': selected_indicator,
        'max_positions': max_positions,
        'min_trade_count': min_trade_count,
        'history_years': history_years,
        'positions': selected_positions,
        'summary': {
            'candidate_count': len(candidates),
            'selected_count': len(selected_positions),
        },
        'dataset_names': dataset_names,
        'indicator_names': indicator_names,
        'portfolio_summary': _build_portfolio_summary(
            selected_positions,
            selected_indicator,
            min_trade_count,
            len(candidates),
        ),
    }
    if request.GET.get('format') == 'json':
        return JsonResponse(payload)
    return render(
        request,
        'portfolio_next_year.html',
        {
            **payload,
            'initial_portfolio_data': json.dumps(payload),
        },
    )
