"""Dataset 2 (after, simulated): Jan 1 to Dec 31, 2026, the year right after Dataset 1 (Jan 1 to Dec 31, 2025).

Unchanged variables are generated the same way Dataset 1 behaves: each Dataset 2 order is drawn at random
from Dataset 1's orders (brand, platform, item, hour, prices, quoted prep time, base queue...), so averages
and ups and downs match Dataset 1, and placed on the same calendar day one year later.
Only the KPI input variables in the Improvement Rules Table are changed, each by a researched amount,
with random variation around the new average (never one multiplier for every row).
"""
import random, sys
import numpy as np
import pandas as pd

src, out_xlsx = sys.argv[1], sys.argv[2]
rng = random.Random(2026)
np_rng = np.random.default_rng(2026)
d1 = pd.read_excel(src)
d1['order_date'] = pd.to_datetime(d1.order_date)

# ---- improvement rules (see Improvement Rules Table)
WRONG_CUT = 0.40          # Acrelec Double Check: bagging mistakes -40%
REFUND_CUT = 0.50         # Acrelec Double Check: order refunds -50%
DELAY_CUT = 0.20          # Toast / Park Burger: ticket times -20%  -> prep delay -20%
QUEUE_CUT = 0.20          # same Toast result: 20% faster tickets -> 20% fewer orders waiting (same demand)
STAFF_MOVE = {11: 1, 13: 1, 20: 1, 10: -1, 17: -1, 21: -1}   # TimeForge: +12% peak labor efficiency -> +3 of 27 peak staff-hours (+11%)
RATING_UP = 0.20          # Acrelec Double Check: +0.2 to +0.3 rating points, low end used

n = len(d1)
pick = np_rng.integers(0, n, n)                        # draw orders like Dataset 1
d2 = d1.iloc[pick].reset_index(drop=True).copy()
d2['order_date'] = d2.order_date.apply(lambda d: d.replace(year=2026))
d2 = d2.sort_values(['order_date', 'hour_of_day']).reset_index(drop=True)
d2['order_id'] = ['ORD-%05d' % (2501 + i) for i in range(n)]
d2['day_of_week'] = d2.order_date.dt.day_name()

base = d2.copy()   # Dataset-1-style values before the solution, used to apply the rules

# ---- staffing: same daily schedule pattern as Dataset 1, hours moved into the rush
d2['staff_on_shift'] = [s + STAFF_MOVE.get(h, 0) for s, h in zip(base.staff_on_shift, base.hour_of_day)]

# ---- orders waiting: -20% on average, varied order to order (x0.70 to x0.90)
d2['orders_in_queue'] = [max(1, round(q * rng.uniform(1 - QUEUE_CUT - .10, 1 - QUEUE_CUT + .10))) for q in base.orders_in_queue]
d2['staffing_ratio'] = (d2.orders_in_queue / d2.staff_on_shift).round(2)

# ---- prep delay: -20% on average for late orders (x0.70 to x0.90); early orders unchanged
d2['prep_time_variance_minutes'] = [round(v * rng.uniform(1 - DELAY_CUT - .10, 1 - DELAY_CUT + .10), 1) if v > 0 else v
                                    for v in base.prep_time_variance_minutes]
d2['actual_prep_time_minutes'] = (d2.quoted_prep_time_minutes + d2.prep_time_variance_minutes).round(1)

# ---- accuracy: 40% of wrong orders become correct (random which ones)
wrong = d2.index[base.order_accuracy == 'Incorrect'].tolist()
d1_wrong_rate = (d1.order_accuracy == 'Incorrect').mean()
target_wrong = round(d1_wrong_rate * (1 - WRONG_CUT) * n)          # Dataset 1 wrong-order rate x 0.60
fixed = set(rng.sample(wrong, max(0, len(wrong) - target_wrong)))
d2['order_accuracy'] = ['Correct' if i in fixed else a for i, a in zip(d2.index, base.order_accuracy)]

# ---- refunds: only wrong orders are refunded (as in Dataset 1); total refunds -50%
base_refunds = (d1.refund_issued == 'Yes').sum()                    # Dataset 1 refunds
target_refunds = round(base_refunds * (1 - REFUND_CUT))
still_wrong = d2.index[d2.order_accuracy == 'Incorrect'].tolist()
refunded = set(rng.sample(still_wrong, target_refunds))
d2['refund_issued'] = ['Yes' if i in refunded else 'No' for i in d2.index]

# ---- rating: fixed orders get a rating drawn from Dataset 1's correct orders; then the whole
#      distribution is lifted so the average is Dataset 1's average + 0.20 (clipped to 1..5)
good = d1.customer_rating[d1.order_accuracy == 'Correct'].tolist()
r = [rng.choice(good) if i in fixed else v for i, v in zip(d2.index, base.customer_rating)]
target = d1.customer_rating.mean() + RATING_UP
# lift ratings in 0.1 steps on randomly chosen orders (never above 5) until the average reaches the target,
# so the lift is spread unevenly like real reviews, not added equally to every order
r = [round(float(x), 1) for x in r]
steps = round((target * n - sum(r)) / 0.1)
pool = [i for i in range(n) if r[i] < 5]
for _ in range(max(0, steps)):
    k = rng.choice(pool); r[k] = round(r[k] + 0.1, 1)
    if r[k] >= 5: pool.remove(k)
d2['customer_rating'] = r
shift = steps * 0.1 / n

d2['order_date'] = d2.order_date.dt.strftime('%Y-%m-%d')
d2 = d2[d1.columns]

# ---- sanity checks
assert (d2.orders_in_queue >= 1).all() and (d2.staff_on_shift >= 1).all()
assert ((d2.refund_issued == 'Yes') <= (d2.order_accuracy == 'Incorrect')).all()
assert d2.customer_rating.between(1, 5).all()
assert (abs(d2.actual_prep_time_minutes - d2.quoted_prep_time_minutes - d2.prep_time_variance_minutes) < 0.06).all()
assert (d2.actual_prep_time_minutes > 0).all(), d2.actual_prep_time_minutes.min()
assert d2.order_id.is_unique and len(d2.columns) == 23

with pd.ExcelWriter(out_xlsx, engine='openpyxl') as w:
    d2.to_excel(w, index=False, sheet_name='Dataset_2_2026')
print('rating shift applied:', round(shift, 3), 'fixed orders:', len(fixed), 'refunds', base_refunds, '->', target_refunds)
