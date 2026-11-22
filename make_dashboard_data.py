"""Compute every number the Before vs After dashboard shows, from Dataset 1 and Dataset 2."""
import json
import sys

import pandas as pd

d1 = pd.read_excel(sys.argv[1])
d2 = pd.read_excel(sys.argv[2]) if sys.argv[2].endswith('.xlsx') else pd.read_csv(sys.argv[2])
out = sys.argv[3]

BRANDS = ["Nonna's Slice House", 'Bombay Street Bowls', 'Flame and Bun']
PLATFORMS = ['Delivery App 1', 'Delivery App 2', 'Phone/Text']


def r(x, n=2):
    return round(float(x), n)


def pct(s):
    return r(s.mean() * 100, 1)


def stats(df):
    df = df.copy()
    df['correct'] = df.order_accuracy == 'Correct'
    df['refund'] = df.refund_issued == 'Yes'
    df['refund_loss'] = df.order_subtotal_usd.where(df.refund, 0)
    df['profit_after_refunds'] = df.estimated_profit_usd - df.refund_loss
    pk = df[df.is_peak_hour == 'Yes']
    npk = df[df.is_peak_hour == 'No']
    days = df.order_date.nunique()
    hours = list(range(10, 22))
    hourly = df[df.hour_of_day.isin(hours)].groupby('hour_of_day')
    s = {
        'kpi': {
            'accuracy': pct(df.correct),
            'profit_per_order': r(df.estimated_profit_usd.mean()),
            'profit_after_refunds': r(df.profit_after_refunds.mean()),
            'peak_staffing_ratio': r(pk.staffing_ratio.mean()),
            'prep_variance': r(df.prep_time_variance_minutes.mean()),
            'rating': r(df.customer_rating.mean()),
            'refund_rate': pct(df.refund),
            'refund_loss': r(df.refund_loss.sum(), 0),
            'wrong_orders': int((~df.correct).sum()),
        },
        'brand_accuracy': [pct(df[df.brand_name == b].correct) for b in BRANDS],
        'brand_rating': [r(df[df.brand_name == b].customer_rating.mean()) for b in BRANDS],
        'peak_accuracy': [pct(npk.correct), pct(pk.correct)],
        'peak_variance': [r(npk.prep_time_variance_minutes.mean()), r(pk.prep_time_variance_minutes.mean())],
        'hour_labels': [f'{h}:00' for h in hours],
        'hour_ratio': [r(hourly.staffing_ratio.mean()[h]) for h in hours],
        'hour_staff': [int(hourly.staff_on_shift.first()[h]) for h in hours],
        'hour_orders': [int(hourly.order_id.count()[h]) for h in hours],
        'rating_by_accuracy': [r(df[df.correct].customer_rating.mean()),
                               r(df[~df.correct].customer_rating.mean()) if (~df.correct).any() else 0],
        'refund_platform': [pct(df[df.platform_name == p].refund) for p in PLATFORMS],
        'refund_loss_brand': [r(df[df.brand_name == b].refund_loss.sum(), 0) for b in BRANDS],
        'profit_after_refunds_platform': [r(df[df.platform_name == p].profit_after_refunds.mean()) for p in PLATFORMS],
        'profit_after_refunds_brand': [r(df[df.brand_name == b].profit_after_refunds.mean()) for b in BRANDS],
        'orders_per_day': r(len(df) / days),
    }
    mon = df.assign(month=pd.to_datetime(df.order_date).dt.strftime('%Y-%m')).groupby('month')
    s['monthly'] = {
        'months': sorted(mon.groups.keys()),
        'accuracy': [pct(g.correct) for _, g in mon],
        'profit_after_refunds': [r(g.profit_after_refunds.mean()) for _, g in mon],
        'peak_staffing_ratio': [r(g[g.is_peak_hour == 'Yes'].staffing_ratio.mean()) for _, g in mon],
        'prep_variance': [r(g.prep_time_variance_minutes.mean()) for _, g in mon],
        'rating': [r(g.customer_rating.mean()) for _, g in mon],
        'refund_rate': [pct(g.refund) for _, g in mon],
    }
    return s


data = {
    'brands': BRANDS,
    'platforms': PLATFORMS,
    'before': stats(d1),
    'after': stats(d2),
}
with open(out, 'w') as f:
    f.write('window.DASH = ' + json.dumps(data) + ';\n')
print(json.dumps(data['before']['kpi']))
print(json.dumps(data['after']['kpi']))
print(data['before']['hour_staff'], data['after']['hour_staff'])
