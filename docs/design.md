# TariffCheck design

## Input: usage CSV
- Columns: `timestamp,kwh`
- One row every 30 minutes (48 rows per day)
- `timestamp` is local Brisbane time, format `YYYY-MM-DD HH:MM` (Queensland has no daylight saving)
- `kwh` is energy used in that 30 minutes, 0 or more

## Plan types
| Type | How it charges | Example |
|---|---|---|
| Flat | One price for every kWh | 24.48 c/kWh |
| Block (stepped) | First X kWh per day at one price, the rest at another | first 15 kWh/day at 22.44 c, then 25.30 c |
| Time-of-Use | Price depends on the time of day | peak 4pm–9pm 35.86 c, off-peak 11am–4pm 14.42 c, shoulder 9pm–11am 20.75 c |

Every plan also has a **daily supply charge** (c/day), paid whatever you use.

## Assumptions
- All prices include GST
- Block thresholds reset every day
- A Time-of-Use window can cross midnight (e.g. shoulder 9pm–11am)
- Time windows include the start and exclude the end: "Peak 4pm–9pm" means 16:00 ≤ time < 21:00 (the plan writes this as 4:00pm–8:59pm)
- Each CSV timestamp is the **start** of its 30-minute interval, so the 20:30 reading is peak and the 21:00 reading is shoulder
- Money uses `Decimal`, never `float`; round to cents only at the end
- Yearly estimate = (cost ÷ days in the data) × 365

## Real plans used (source: Energy Made Easy Quick compare, Springfield Lakes 4300, retrieved 9 Nov 2026)

Rates as listed, before any discounts. All prices include GST.

| Plan | Retailer | Plan ID | Type | Usage rates | Supply |
|---|---|---|---|---|---|
| Nectr Power Perks – August 2026 | Nectr | NTR1154691MRE1 | Flat | 24.48 c/kWh | 164.87 c/day |
| GLOHOME Residential (Flat Rate) – Energex | GloBird Energy | GLO1212438MRE1 | Block | 22.44 c/kWh for the first 15 kWh per day, then 25.30 c/kWh | 148.50 c/day |
| Nectr Power Perks TOU – August 2026 | Nectr | NTR1154695MRE1 | Time-of-Use (all week) | Peak 4pm–9pm 35.86 c; Off-peak 11am–4pm 14.42 c; Shoulder 9pm–11am 20.75 c | 140.17 c/day |

Screenshots of each plan's price page are in `docs/plans/`.