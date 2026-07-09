# 台美日韓產業關聯儀表板

以台灣投資人角度，挑選美國道瓊/那斯達克/S&P500/費城半導體、韓國KOSPI、日本日經225、
台灣加權/上櫃指數成分股中「同產業」的代表公司，跨市場並排比較，用於觀察類似
「美股記憶體下跌 → 隔天台股/韓股記憶體股同步走弱」的產業連動效應。

線上網址（部署後）：`https://<你的帳號>.github.io/<repo名稱>/`

## 目前涵蓋範圍

- **22 個產業組、125 檔公司**（人工挑選之跨市場代表公司，非完整指數成分股清單）
- 每組公司數 3–8 檔，橫跨美/台/日/韓中的 2–4 個市場
- 完整清單見 `data/groups.json`

分組策略：由於 8 個指數合計成分股上千檔，全部涵蓋會使產業分類品質失控，
因此改採「精選跨市場產業組」，聚焦對台股有實質連動意義的產業
（半導體代工、記憶體、IC設計、封測、面板、PCB、航運、鋼鐵、軍工、AI伺服器、
生技疫苗等），可逐步擴充。

## 架構

```
data/
  groups.json     ← 公司分組主檔（人工維護，含股票代號、產業分類、產品說明、來源連結）
  latest.json     ← 股價快照（由 GitHub Actions 自動產生，不需手動編輯）
scripts/
  fetch_prices.py ← stdlib-only 抓價腳本，讀 groups.json 逐一查 Yahoo Finance
index.html        ← 儀表板（純 HTML/CSS/JS，無框架、無需編譯）
.github/workflows/
  update.yml      ← 每週日自動抓價 + 部署 GitHub Pages
```

延續你先前專案（tw-margin-table、tw-market-dashboard）的作法：
stdlib-only Python（無需 pip install 第三方套件）+ GitHub Actions + GitHub Pages。

## 資料來源與代號格式

股價一律透過 Yahoo Finance 公開的 chart API 抓取（`query1.finance.yahoo.com`），
代號後綴對應各市場：

| 市場 | 後綴 | 範例 |
|---|---|---|
| 美國 | 無 | `NVDA` |
| 台灣上市 | `.TW` | `2330.TW`（台積電） |
| 台灣上櫃 | `.TWO` | `6547.TWO`（高端疫苗） |
| 日本 | `.T` | `285A.T`（Kioxia） |
| 韓國 | `.KS` | `005930.KS`（三星電子） |

## 更新頻率

**每天**（UTC 23:00 = 台北時間隔天早上 07:00）自動執行。

選擇台北時間早上七點的原因：前一晚的美股收盤（台北時間凌晨四、五點）
已經確定，台/日/韓則呈現各自前一交易日的收盤價，一次抓齊四個市場最新
可得的資料。cron 設定在 `.github/workflows/update.yml`（`0 23 * * *`）。

## 部署步驟（GitHub Desktop 流程，比照你先前專案）

1. 在 GitHub 建立新的 public repo（例如 `tw-industry-chain`）。
2. 用 GitHub Desktop 把這個資料夾整個加入該 repo 並 push 到 `main` 分支。
3. 到 repo 的 **Settings → Pages**，「Build and deployment」的 Source 選擇
   **GitHub Actions**（不是「Deploy from a branch」）。
4. 到 **Actions** 頁籤，手動觸發一次 `Daily price update`
   （右側 "Run workflow" 按鈕）完成首次抓價與部署，之後就會每天自動跑。
5. 完成後網站會在 `https://<帳號>.github.io/<repo名稱>/` 上線。

> 注意：本機開發環境若有網路白名單限制，可能連不到
> `query1.finance.yahoo.com`；這在 GitHub Actions 的執行環境中不受影響，
> 正式跑的時候會直接抓到資料。

## 之後可以擴充的方向

- 目前每組公司數量刻意精簡（3–8檔），若要納入更多同產業公司，直接編輯
  `data/groups.json` 新增即可，`fetch_prices.py` 會自動抓新代號的價格。
- `data/groups.json` 裡的 `product` 欄位目前是人工簡短中文描述，
  如果想改成更完整的公司簡介，可以在 `fetch_prices.py` 之外另外呼叫
  Yahoo Finance 的 `quoteSummary` 端點抓 `longBusinessSummary` 再翻譯。
- 目前 `index.html` 用純 JS 讀 `data/*.json`，之後想加歷史股價走勢圖，
  可以讓 `fetch_prices.py` 額外把每週資料附加寫入一個歷史檔（例如
  `data/history.json`），再用 Chart.js 畫出來。

## 免責聲明

分組為人工判斷之產業關聯，非官方 GICS 或交易所分類；股價資料存在延遲，
僅供產業連動關係的研究參考，不構成投資建議。
