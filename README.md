# Ghost Kitchen: Before vs After Dashboard

MRP project dashboard by Sanjay Gaviriboina, Nithin Reddy Gurram, Haripriya Dommeti and Nithinkumar Kanugula.

Dashboard 1 (current state, Synthetic Dataset 1) side by side with Dashboard 2 (future state, Synthetic Dataset 2), showing the simulated impact of the Ghost Kitchen Command Center.

## What is on the page

* **KPI comparison:** the 6 KPIs before and after, with the change
* **Chapter 1:** order accuracy by brand
* **Chapter 2:** accuracy and prep delay at peak vs non-peak hours
* **Chapter 3:** orders waiting per staff member by hour, and staff scheduled by hour
* **Chapter 4:** customer rating by brand
* **Chapter 5:** refund rate and money lost to refunds
* **Chapter 6:** profit per order after refunds by channel
* **Method:** exactly which variables changed in Dataset 2, by how much, and the source for each
* **Downloads:** Dataset 1 and Dataset 2 as Excel files

Every chart has a "Show data table" link with the exact numbers.

## How Dataset 2 was built

Dataset 2 is Dataset 1 with only the variables the app would improve changed (see `scripts/make_dataset2.py`):

| Change | Source |
|---|---|
| 40% of wrong orders become correct | Acrelec smart-scale pilot: bagging mistakes down 40% |
| Total refunds down 50% | Acrelec and NEXA: refunds down 50% |
| Prep delay and orders waiting down 20% | Toast case study (Park Burger): ticket times down 20% |
| +1 staff at 11:00, 13:00, 20:00 and -1 at 10:00, 17:00, 21:00 (same total hours) | TimeForge: demand-based scheduling, 12% better peak labor efficiency |
| Ratings recomputed with Dataset 1's rules | Result +0.15 stars (Acrelec reports +0.2 to +0.3) |

Order volume, brand and channel mix, prices, commissions and food cost are unchanged.

## Publish on GitHub Pages (free)

1. Sign in at https://github.com.
2. Click **+** > **New repository**. Name it exactly **ghost-kitchen-dashboard**, choose **Public**, then click **Create repository**.
3. Click the **uploading an existing file** link.
4. Unzip `ghost-kitchen-dashboard.zip`, open the folder, select **everything inside it** (index.html, css, js, vendor, data, scripts, README.md, .nojekyll) and drag it into the upload box.
5. Click **Commit changes**.
6. Go to **Settings** > **Pages**. Set Source to **Deploy from a branch**, Branch to **main**, folder **/ (root)**, then click **Save**.
7. After 1 to 3 minutes your link is: `https://YOUR-USERNAME.github.io/ghost-kitchen-dashboard/`

The "Open the app prototype" button links to `../ghost-kitchen-app/`, so it works when the app is published in a repo named **ghost-kitchen-app** on the same account.

## Rebuild the numbers (optional)

```
python scripts/make_dataset2.py data/Ghost_Kitchen_Synthetic_Dataset_1.xlsx dataset2.csv data/Ghost_Kitchen_Synthetic_Dataset_2.xlsx
python scripts/make_dashboard_data.py data/Ghost_Kitchen_Synthetic_Dataset_1.xlsx dataset2.csv js/data.js
```
Requires Python with pandas and openpyxl.
