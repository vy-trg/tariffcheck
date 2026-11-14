# TariffCheck test plan

**What is tested:** the live app (https://tariffcheck.streamlit.app/) and the `tariffcheck` package.
**When:** 14 Nov 2026, version on `main` after PR "Streamlit app".
**Where:** macOS, Chrome and Safari, desktop width and phone width (390 px).

## 1. Automated tests (run on every push by GitHub Actions)

| Area | File | What it proves |
|---|---|---|
| Plan maths | `tests/test_tariffs.py`, `tests/test_tou.py` | Flat, block and time-of-use bills match hand-worked examples to the cent, including windows that cross midnight |
| Bad plans | same files | Negative rates, overlapping or missing time windows are refused |
| Loading files | `tests/test_loader.py` | 11 kinds of broken CSV each give a clear message with the line number |
| Comparison | `tests/test_compare.py` | Cheapest plan, ties, savings and yearly estimate |
| Usage summary | `tests/test_usage.py` | Days, daily average, hourly profile, peak share |
| App | `tests/test_app.py` | App starts on sample data, and unticking every plan shows a message, not a crash |

Coverage: 100% of lines and branches in `tariffcheck/`. CI fails below 90%.

## 2. Manual tests

| # | Steps | Expected | Result |
|---|---|---|---|
| M1 | Open the app with no file | Sample data loads, 3 plans, GloBird cheapest at $1,752.14/yr | Pass |
| M2 | Upload `data/sample_usage.csv` | Same numbers as M1, toast "Loaded 1,440 readings" | Pass |
| M3 | Untick all plans | Friendly "No plans picked yet" message | Pass |
| M4 | Untick one plan | Cards and chart update, ribbon still on the cheapest | Pass |
| M5 | Upload an empty file | "the file is empty" | Pass |
| M6 | Upload a file with kWh `-1` | Error names the file and line 2 | Pass |
| M7 | Upload a file with `Timestamp,kWh` header | Loads normally | **Fail**, see bug 1 |
| M8 | Upload a file with one day of readings | Says "1 day" | **Fail**, see bug 2 |
| M9 | Upload a file with one day of readings | Warns that the yearly figure is a rough guess | **Fail**, see bug 3 |
| M10 | Download sample file, then upload it | Same result as M1 | _check_ |
| M11 | Phone width (390 px) | Columns stack, nothing cut off | _check_ |
| M12 | Turn on "Reduce motion" in macOS | Cards appear with no animation | _check_ |
| M13 | Check every plan price against Energy Made Easy | All rates and supply charges match `docs/design.md` | Pass |

## 3. Bugs found

| # | Bug | Severity | Status |
|---|---|---|---|
| 1 | Header `Timestamp,kWh` is rejected as "missing column(s)" even though the columns are there | High: blocks real users | Fixed, with test |
| 2 | "1 days of readings" | Low: wording | Fixed |
| 3 | A file with a few days is scaled up to a full year with no warning | Medium: misleading number | Fixed: warning under 28 days |

## 4. Not tested / out of scope

- Real retailer bills: the app is not compared against an actual bill.
- Files over ~1 year: should work but are slow to price in pure Python.
- Solar export, demand charges, discounts and concessions are not modelled.
