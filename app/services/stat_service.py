# stat_service.py (功能1 + 功能2 + 功能3 + 功能5)
# ---------------------------------------------------
from collections import defaultdict
from typing import Dict, Any, List

COURSE_COLLECTION_PREFIX = "courses_"


def compute_teacher_stats(db, teacher: str, this_sem: str = "1142") -> Dict[str, Any]:
    """
    功能 1：每學期授課堂數
    功能 2：歷年授課系所
    功能 3：指定學期授課資料
    功能 5：歷年 Top 3 課程（含每年平均值計算）
    """

    courses_per_sem = defaultdict(int)
    departments = set()
    sem_courses: List[Dict[str, Any]] = []

    # 用來累積每堂課跨學期資料
    course_year_map = defaultdict(lambda: defaultdict(list))
    # 結構變成：
    # course_year_map[(course_no, course_name)][year] = [total_count1, total_count2 ...]

    # 遍歷所有 courses_xxxx collection
    for coll_name in db.list_collection_names():
        if not coll_name.startswith(COURSE_COLLECTION_PREFIX):
            continue

        coll = db[coll_name]
        cursor = coll.find({"teacher_name": teacher})

        for doc in cursor:
            sem_no = doc.get("sem_no")  # e.g. "1051"
            group_name = doc.get("group_name")
            course_no = doc.get("course_no")
            course_name = doc.get("course_name")
            total_count = doc.get("total_count", 0) or 0

            # -------------------------
            # 功能 1：每學期教課堂數
            # -------------------------
            courses_per_sem[sem_no] += 1

            # -------------------------
            # 功能 2：系所
            # -------------------------
            if group_name:
                departments.add(group_name)

            # -------------------------
            # 功能 3：指定學期課程
            # -------------------------
            if sem_no == this_sem:
                clean_doc = {
                    k: v for k, v in doc.items() if k not in ["_id", "index"]
                }
                sem_courses.append(clean_doc)

            # -------------------------
            # 功能 5：累積課程的跨學期資料
            # -------------------------
            year = sem_no[:3]  # 例如 "1051" → "105"
            key = (course_no, course_name)
            course_year_map[key][year].append(total_count)

    # 排序（學期）
    sorted_result = dict(sorted(courses_per_sem.items()))

    # 功能 3：沒有課
    if len(sem_courses) == 0:
        sem_info = {
            "sem_no": this_sem,
            "course_count": 0,
            "courses": [],
            "note": "該學期無課程",
        }
    else:
        sem_info = {
            "sem_no": this_sem,
            "course_count": len(sem_courses),
            "courses": sem_courses,
        }

    # -------------------------
    # 功能 5：計算 Top3 課程
    # -------------------------
    course_stats_output = []

    for (course_no, course_name), year_map in course_year_map.items():

        # 計算每個「學年」平均值
        year_avg = {}
        for year, counts in year_map.items():
            year_avg[year] = sum(counts) / len(counts)  # 兩學期平均 or 一學期平均

        # 整體歷年平均
        overall_avg = sum(year_avg.values()) / len(year_avg)

        # 總人數（全部學期加總）
        total_students = sum(sum(c_list) for c_list in year_map.values())

        course_stats_output.append({
            "course_no": course_no,
            "course_name": course_name,
            "total_students": total_students,
            "year_avg": year_avg,          # 每個學年的平均
            "overall_avg": overall_avg,    # 歷年平均
        })

    # 按總人數排序，只取前三名
    top_courses = sorted(
        course_stats_output,
        key=lambda x: x["total_students"],
        reverse=True
    )[:3]

    return {
        "teacher": teacher,
        "courses_per_semester": sorted_result,
        "department_count": len(departments),
        "departments": sorted(departments),
        "this_semester": sem_info,
        "top3_courses": top_courses,
    }
