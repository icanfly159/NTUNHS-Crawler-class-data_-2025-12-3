# NTUNHS 課程資料查詢系統（FastAPI + MongoDB Atlas）


簡單的個人說明：
* * * 前情提要 Crawler_class.py 和 Input_datato_mongodb.py 不用管這很重要所以說三遍 * * * 
* * * 前情提要 Crawler_class.py 和 Input_datato_mongodb.py 不用管這很重要所以說三遍 * * * 
* * * 前情提要 Crawler_class.py 和 Input_datato_mongodb.py 不用管這很重要所以說三遍 * * * 

Crawler_class.py:動態爬蟲所有課程了所以不到了 （有問題可以去看一下）
Input_datato_mongodb.py: 快速input 資料到mongodb 



已經測試過api 
push 到你們local 就可以測試流程

testing 流程：
1. 創見cluster 在mongodb cloud 裡面 我這裡創見名稱叫做 ‘’’NTUNHSdatabase’’’(創見你們的cluster名稱也ok)


2. 可以看config.env 裡面改你們創見的database 名稱和密碼

2. Input_datato_mongodb.py 跑這之前也需要改這裡面的mongodb 的url 改成你們的

3. 請先跑Input_datato_mongodb.py 放入 data 倒 mongodb cloud 

4. 輸入運作node.js server ```uvicorn app.main:app```

5. 測試api ```http://localhost:8000/docs```






* 下面都為ai生成但可以看一下


本專案提供以「學期課程 JSON 資料」為基礎的後端查詢服務，包含：

* 智慧搜尋教師
* 老師跨學期授課統計
* 指定學期課程查詢
* 歷年授課系所分析
* 最熱門 Top 3 課程（含年度平均與歷年平均）

後端採 **FastAPI** 實作，資料儲存在 **MongoDB Atlas**，並可讓其他服務（例如 **Node.js server / React 前端**）直接串接 API 使用。

---

# 📦 一、課程 JSON 資料結構說明

每個 JSON 檔代表一個學期，例如：

```
courses_1142.json → 1142 學期
courses_1051.json → 1051 學期
```

匯入 MongoDB 後，每個 JSON 對應到一個 collection：

```
courses_1142.json → courses_1142
courses_1051.json → courses_1051
```

## 1.1 JSON 欄位說明

| 欄位名稱             | 型態     | 說明            |
| ---------------- | ------ | ------------- |
| index            | int    | 排序編號（API 不使用） |
| sem_no           | string | 學期（如 1142）    |
| group_name       | string | 系所名稱          |
| grade            | int    | 年級            |
| class_no         | string | 班級代號          |
| course_no        | string | 課程代碼          |
| course_name      | string | 課程名稱          |
| teacher_name     | array  | 授課老師（可能一位或多人） |
| total_count      | int    | 修課人數          |
| credit           | int    | 學分            |
| course_type_name | string | 課程類型          |
| room_no          | string | 教室            |
| week_no          | int    | 星期幾上課         |
| section_no       | array  | 節次，例如 `[6,7]` |

## 1.2 JSON 範例

```json
{
  "index": 58,
  "sem_no": "1142",
  "group_name": "四年制護理系",
  "grade": 1,
  "class_no": "C0",
  "course_no": "0001",
  "course_name": "國文二",
  "teacher_name": ["何澍"],
  "total_count": 0,
  "credit": 2,
  "course_type_name": "通識必修(通識)",
  "room_no": "F408",
  "week_no": 3,
  "section_no": [1, 2]
}
```

---

# 🏗️ 二、系統架構流程說明

整個系統由以下組成：

* `config.env`：儲存 MongoDB 連線設定
* `infra/db.py`：負責與 MongoDB Atlas 建立連線
* `app/main.py`：FastAPI 主 API 入口
* `search_service.py`：教師智慧搜尋
* `stat_service.py`：老師授課統計邏輯

可與 **Node.js / React / 其它後端** 串接。

---

# 🔧 2.1 config.env（MongoDB 設定）

在專案根目錄建立 `config.env`：

```env
MONGO_URI=mongodb+srv://<USERNAME>:<PASSWORD>@<cluster>.mongodb.net/?retryWrites=true&w=majority&appName=YourAppName
DATABASE_NAME=NTUNHS_CLASS_DATA
```

如需切換資料庫，只需修改這裡即可。

---

# 🔌 2.2 db.py（資料庫連線管理）

`infra/db.py` 是唯一負責連線 MongoDB 的地方：

```python
client = MongoClient(MONGO_URI)

def get_db():
    return client[DATABASE_NAME]
```

如果未來想改連自己本地端 MongoDB 或改成 Node.js 驅動，只要調整：

* `MONGO_URI`
* 或替換此檔案即可

主邏輯（search / stat）完全不受影響。

---

# 🚀 2.3 FastAPI 主系統：main.py

提供 API 給前端 / Node.js 使用：

```python
GET /teachers/search?q=關鍵字       → 智慧搜尋老師
GET /teachers/{teacher}/stats?sem=1142 → 老師統計資料
```

Node.js 或任何前端只要使用 HTTP 請求即可串接。

---

# 🧠 2.4 search_service.py（教師智慧搜尋）

功能：

* 模糊搜尋（輸入「賴」→ 找到 賴冠霖 / 賴冠林 / 林賴冠）
* 跨所有學期的 collection
* 回傳排序後的不重複老師

前端常用作 **自動完成（auto-complete）功能**。

---

# 📊 2.5 stat_service.py（老師授課統計）

輸入老師名稱與學期（如：1142），回傳 5 大資訊：

### ✔ 1. 每學期授課堂數

```json
{
  "1051": 3,
  "1052": 1,
  "1142": 2
}
```

### ✔ 2. 歷年授課系所

```json
["四年制護理系", "四年制資管系", "研究所"]
```

### ✔ 3. 指定學期完整課程資料（若無則顯示無課）

所有 JSON 欄位都會輸出（移除 `_id` 與 `index`）。

### ✔ 4. 計算該學期上課總時數

依據 `section_no` 的長度統計。

### ✔ 5. 歷年 Top 3 課程

包含：

* 該課所有學期的人數總和
* 每一年（如 105 年）之平均人數（若兩學期上課則先平均）
* 歷年平均（四捨五入）

範例：

```json
{
  "course_no": "0737",
  "course_name": "健康照護之另類輔助療法",
  "total_students": 120,
  "year_avg": {
    "105": 35,
    "107": 50
  },
  "overall_avg": 43
}
```

---

# 🔗 2.6 Node.js / React 串接方式

## Node.js 串 FastAPI：

```js
const r = await fetch(`http://localhost:8000/teachers/search?q=${q}`);
const data = await r.json();
```

若想改用 Node.js 直接查 MongoDB，只需要：

* 改寫 `search_service.py` 與 `stat_service.py` 至 JavaScript
* 並把 `MONGO_URI` 用在 Node.js 的 MongoDB Driver 即可

其餘架構皆保持相同。

---

# 🔄 2.7 系統流程圖

```text
          [React / 前端]
                 │
                 ▼
        [Node.js Server (可選)]
                 │   （HTTP 呼叫）
                 ▼
          [FastAPI Python]
   ┌─────────────────────────────┐
   │ /teachers/search             │
   │ /teachers/{t}/stats          │
   └───────────┬─────────────────┘
               │ get_db()
               ▼
        [MongoDB Atlas 資料庫]
   courses_1051 / courses_1142 / ...
```

---

# 🧪 三、API Input / Output 範例

## 3.1 搜尋老師

```
GET /teachers/search?q=賴
```

```json
{
  "query": "賴",
  "teachers": ["賴冠霖", "賴冠林", "林賴冠"]
}
```

---

## 3.2 老師統計查詢

```
GET /teachers/賴冠霖/stats?sem=1142
```

輸出包含：

* 每學期授課數
* 授課系所
* 1142 學期所有課程資料
* 本學期授課總時數
* 歷年 Top 3 課程（含年度平均）

```json
{
  "teacher": "賴冠霖",
  "courses_per_semester": {
    "1051": 3,
    "1052": 1,
    "1142": 2
  },
  "department_count": 3,
  "departments": ["四年制護理系", "研究所", "資管系"],
  "this_semester": {
    "sem_no": "1142",
    "course_count": 2,
    "courses": [...]
  },
  "top3_courses": [...]
}
```

---


