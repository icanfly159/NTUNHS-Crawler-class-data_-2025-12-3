# 🏫 NTUNHS 課程資料爬蟲 (NTUNHS Course Data Crawler)

一個以 **Python + Selenium** 實作的自動化爬蟲工具，用來批次抓取  
**國北護 NTUNHS 校務系統的課程資料**，並將所有課程資訊整理為  
結構化的 **JSON 檔案**。

本專案能協助你：

- 📦 批次下載多個學期的課程資料  
- 🧩 自動勾選所有學制（四技、二技、碩士班、博士班…）  
- 🔍 自動查詢課程、解析表格  
- 📝 將資料整理成 MongoDB 友好的 JSON 格式  
- 📁 按「學期」分類生成 JSON 檔（如：`courses_1142.json`）

> 適合用於課表系統開發、課程分析、學期資料備份、資料研究等用途。

---


# 📑 1. NTUNHS 課程資料爬蟲 create.py 

### ✔ 自動化操作完整查詢流程
- 自動選擇多學期（使用者輸入）
- 自動勾選所有學制
- 自動點擊查詢
- 智慧等待（等待最長 90 秒），避免伺服器速度太慢造成錯誤(can change the time)








### ✔ 完整解析課程資料
this data Input in MongoDB
包含：
| 欄位 | 說明 |
|------|------|
| index | 流水號（整數） |
| sem_no | 學期代碼（例：1142） |
| group_name | 系所 / 班級名稱 |
| grade | 年級（整數） |
| class_no | 班別代碼 |
| course_no | 課號 |
| course_name | 課程名稱 |
| teacher_name | 老師姓名陣列 |
| total_count | 人數/容量資訊 |
| credit | 學分數 |
| course_type_name | 課程類型（必修/選修/通識等） |
| room_no | 教室 |
| week_no | 星期幾上課（1–7） |
| section_no | 節次清單，如 `[6,7]` |









