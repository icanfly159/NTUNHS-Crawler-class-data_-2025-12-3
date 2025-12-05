# search_service.py
# -----------------------------------------
# 智慧搜尋老師名稱（跨所有學期 collection）
# -----------------------------------------

from typing import List
import re

# 可接受的 collection prefix
COURSE_COLLECTION_PREFIX = "courses_"


def search_teachers(db, keyword: str) -> List[str]:
    """
    智慧搜尋老師名稱：
    - 跨所有 courses_xxxx collection 搜尋 teacher_name
    - 支援模糊搜尋、中文搜尋
    - 回傳不重複、排序後的老師列表
    """

    if not keyword or keyword.strip() == "":
        return []

    keyword = keyword.strip()
    regex = re.compile(keyword, re.IGNORECASE)  # 模糊搜尋

    teacher_set = set()

    # 遍歷所有 collection
    for coll_name in db.list_collection_names():
        # 只搜尋以 courses_ 開頭的 collection
        if not coll_name.startswith(COURSE_COLLECTION_PREFIX):
            continue

        coll = db[coll_name]

        # 查詢 teacher_name array 中含 keyword 的項目
        cursor = coll.find({"teacher_name": regex}, {"teacher_name": 1})

        for doc in cursor:
            teachers = doc.get("teacher_name", [])
            for t in teachers:
                if keyword in t:  # 再次強化本地端比對，避免多餘結果
                    teacher_set.add(t)

    # 回傳排序後的老師列表
    return sorted(teacher_set)
