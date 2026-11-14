# 北海道札幌函館旅行攻略：自動資料更新包

請將本資料夾內的內容上傳到 `cah25/hokkaido-trip-guide` 儲存庫根目錄，保留 `.github/workflows/update-data.yml`、`scripts/update_data.py`、`data/status.json` 與 `index.html`。

## 需要的 GitHub 設定

1. 儲存庫必須是 Public，GitHub Pages 來源使用 `main` 分支的 `/ (root)`。
2. 到 **Settings → Actions → General**，確認允許 Actions 執行；Workflow permissions 選擇 **Read and write permissions**。
3. 上傳後到 **Actions → Update Hokkaido weather and transport data → Run workflow** 手動執行一次。
4. 之後排程約每 10 分鐘執行一次；GitHub Actions 可能因平台排程而延遲幾分鐘。

JMA 的警報與預報會直接由公開 JSON 更新。交通來源若只有動態頁面或官方拒絕自動讀取，`status.json` 會標示來源狀態與抓取時間，不會猜測道路或列車是否正常。
