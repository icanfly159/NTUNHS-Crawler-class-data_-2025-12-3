from typing import Iterable, List, Tuple, Dict
import os
import json
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://system10.ntunhs.edu.tw/AcadInfoSystem/Modules/QueryCourse/QueryCourse.aspx"


# -----------------------------
# Small logging helper
# -----------------------------
def log(msg: str) -> None:
    print(f"[NTUNHS] {msg}")


# -----------------------------
# Utility: split semesters into chunks of size 2
# -----------------------------
def chunk_semesters(semesters: List[str], chunk_size: int = 2) -> List[List[str]]:
    """
    Split semester list into chunks of given size.
    e.g. ["1142","1141","1132","1131"] -> [["1142","1141"],["1132","1131"]]
         ["1142","1141","1132"]       -> [["1142","1141"],["1132"]]
    """
    chunks: List[List[str]] = []
    current: List[str] = []
    for s in semesters:
        current.append(s)
        if len(current) == chunk_size:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


# -----------------------------
# 1. Semester selection
# -----------------------------
def click_multi_semesters(driver, semesters: Iterable[str]) -> Tuple[List[str], List[str]]:
    """Click only the semesters listed in `semesters`."""
    requested = [s.strip() for s in semesters if s.strip()]
    log(f"Selecting semesters: {requested}")

    # 1. Click '學期多選' button
    multi_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "btnMultiSemNo"))
    )
    multi_btn.click()
    log("Clicked '學期多選' button.")

    # 2. Wait for at least one semester checkbox to appear
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@id='ContentPlaceHolder1_cblSemNo_0']")
        )
    )

    # Cache all checkbox + label pairs once
    checkboxes = driver.find_elements(
        By.XPATH, "//input[contains(@id, 'ContentPlaceHolder1_cblSemNo_')]"
    )

    pairs: List[Tuple[str, object]] = []  # (label_text, checkbox)
    for box in checkboxes:
        box_id = box.get_attribute("id")
        label_elem = driver.find_element(By.XPATH, f"//label[@for='{box_id}']")
        label_text = label_elem.text.strip().replace("\xa0", "")
        pairs.append((label_text, box))

    found_values: List[str] = []
    not_found_values: List[str] = []

    for sem in requested:
        for label_text, box in pairs:
            if label_text == sem:
                driver.execute_script("arguments[0].click();", box)
                found_values.append(sem)
                break
        else:
            not_found_values.append(sem)

    log(f"Semester selected: {found_values}")
    if not_found_values:
        log(f"Semester NOT found on page: {not_found_values}")

    return found_values, not_found_values


# -----------------------------
# 1.5 年級 (grade) + 查詢
# -----------------------------
def click_all_grades(driver) -> None:
    """
    Click all checkboxes inside 年級 table.
    (學期變動後年級項目會刷新，因此每次查詢都需要重新抓取)
    HTML example:
      <table id="ContentPlaceHolder1_cblGrade">
        <input ... value="1"> 1年級
        <input ... value="2"> 2年級
        ...
      </table>
    """
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.ID, "ContentPlaceHolder1_cblGrade")
        )
    )

    checkboxes = driver.find_elements(
        By.XPATH, "//table[@id='ContentPlaceHolder1_cblGrade']//input[@type='checkbox']"
    )

    for box in checkboxes:
        driver.execute_script("arguments[0].click();", box)

    log(f"Selected all 年級 checkboxes (count={len(checkboxes)}).")


def click_query_button(driver) -> None:
    """Click the 查詢 (Query) button."""
    query_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_btnQuery"))
    )
    driver.execute_script("arguments[0].click();", query_btn)
    log("Clicked '查詢' button. Waiting for results...")


def wait_for_results_table(driver, timeout: int = 500) -> None:
    """
    Wait until there is at least one result row in either:
      - NewGridView (ContentPlaceHolder1_NewGridView), or
      - OldGridView (ContentPlaceHolder1_OldGridView)
    """
    def _has_any_row(d):
        rows = d.find_elements(
            By.CSS_SELECTOR,
            "#ContentPlaceHolder1_NewGridView tr[group], "
            "#ContentPlaceHolder1_OldGridView tr[group]"
        )
        return len(rows) > 0

    WebDriverWait(driver, timeout).until(_has_any_row)
    log("Result table is ready (found at least one row in NewGridView or OldGridView).")


# -----------------------------
# 2. Helpers for scraping / parsing
# -----------------------------
def get_span_text_in_row(row, id_substring: str) -> str:
    """Find a span in this row whose id contains `id_substring` and return its text."""
    elem = row.find_element(By.CSS_SELECTOR, f"span[id*='{id_substring}']")
    return elem.text.strip()


def parse_int_safe(text: str, default: int = 0) -> int:
    text = (text or "").strip()
    match = re.search(r"\d+", text)
    return int(match.group()) if match else default


def parse_section_no(sec_text: str) -> List[int]:
    """
    Convert time strings like:
      '6~7節'      -> [6, 7]
      '1~4節'      -> [1, 2, 3, 4]
      '6節'        -> [6]
      '1,2,3,4節'  -> [1, 2, 3, 4]
      '1, 3, 5節'  -> [1, 3, 5]
      '1-4節'      -> [1, 2, 3, 4]
    """
    if not sec_text:
        return []

    s = sec_text.replace("節", "").replace(" ", "")
    if not s:
        return []

    result: List[int] = []

    parts = re.split(r"[，,]", s)
    for part in parts:
        part = part.strip()
        if not part:
            continue

        if "~" in part or "-" in part:
            tokens = re.split(r"[~-]", part)
            if len(tokens) == 2:
                start = parse_int_safe(tokens[0])
                end = parse_int_safe(tokens[1])
                if start and end and end >= start:
                    result.extend(range(start, end + 1))
                elif start:
                    result.append(start)
        else:
            n = parse_int_safe(part)
            if n:
                result.append(n)

    # unique, keep order
    seen = set()
    out: List[int] = []
    for n in result:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def parse_teacher_names_from_row(row) -> List[str]:
    """
    Prefer hidden 'hidTeachNames' if present.
    If empty, fallback to visible teacher spans.
    Return list of teacher names.
    """
    try:
        names_text = get_span_text_in_row(row, "hidTeachNames")
    except Exception:
        names_text = ""

    names: List[str] = []
    if names_text:
        tmp = names_text.replace("、", ",").replace("，", ",")
        for part in tmp.split(","):
            name = part.strip()
            if name:
                names.append(name)

    if not names:
        spans = row.find_elements(
            By.CSS_SELECTOR,
            "div[id*='Teaher'] span, div[id*='TeachNameLinks'] span"
        )
        for sp in spans:
            n = sp.text.strip()
            if n:
                names.append(n)

    return names


# -----------------------------
# 3. Scrape table and save JSON
# -----------------------------
def scrape_results_and_save_json(driver) -> None:
    """
    After clicking 查詢 and loading results, scrape all rows from either:
       - ContentPlaceHolder1_NewGridView, or
       - ContentPlaceHolder1_OldGridView
    and save:
       data/courses_<sem_no>.json
    """
    # 等任何一個表格出現
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#ContentPlaceHolder1_NewGridView, #ContentPlaceHolder1_OldGridView")
        )
    )

    # 優先使用 NewGridView，若沒有就用 OldGridView
    table = None
    table_id = None
    try:
        table = driver.find_element(By.ID, "ContentPlaceHolder1_NewGridView")
        table_id = "ContentPlaceHolder1_NewGridView"
        log("Using NewGridView for scraping.")
    except Exception:
        table = driver.find_element(By.ID, "ContentPlaceHolder1_OldGridView")
        table_id = "ContentPlaceHolder1_OldGridView"
        log("Using OldGridView for scraping.")

    rows = table.find_elements(By.CSS_SELECTOR, "tr[group]")
    log(f"Found {len(rows)} <tr group='...'> rows in {table_id}, parsing...")

    data_by_sem: Dict[str, List[dict]] = {}
    parsed_count = 0
    skipped_count = 0

    for row in rows:
        try:
            index_str = get_span_text_in_row(row, "lblIndex")
        except Exception:
            skipped_count += 1
            continue

        index_val = parse_int_safe(index_str, default=0)

        # --- sem_no: New & Old 都是 lblSEMNo ---
        sem_no = get_span_text_in_row(row, "lblSEMNo")

        # --- group_name: New 用 lblGroupName，Old 用 lblDeptName ---
        try:
            group_name = get_span_text_in_row(row, "lblGroupName")
        except Exception:
            try:
                group_name = get_span_text_in_row(row, "lblDeptName")
            except Exception:
                group_name = ""

        # --- grade: New 用 lblGrade，Old 用 hidCOURSEGRADE ---
        try:
            grade_val = parse_int_safe(get_span_text_in_row(row, "lblGrade"), default=0)
        except Exception:
            try:
                grade_val = parse_int_safe(get_span_text_in_row(row, "hidCOURSEGRADE"), default=0)
            except Exception:
                grade_val = 0

        # --- class_no: New 用 lblClass，Old 通常用 hidden hidCOURSECLASS 或 ClassName title ---
        class_no = ""
        try:
            class_no = get_span_text_in_row(row, "lblClass")
        except Exception:
            # OldGridView: hidden COURSELASS
            try:
                class_no = get_span_text_in_row(row, "hidCOURSECLASS")
            except Exception:
                # fallback: ClassName 的 title (e.g. 665A10)
                try:
                    class_span = row.find_element(By.CSS_SELECTOR, "span[id*='lblClassName']")
                    class_no = (class_span.get_attribute("title") or "").strip()
                except Exception:
                    class_no = ""

        # --- course_no: New 有 lblCourseNo，Old 沒有時用 CourseName 的 title 或 FULLCOURSECLASS ---
        try:
            course_no = get_span_text_in_row(row, "lblCourseNo")
        except Exception:
            # OldGridView: lblCourseName 的 title 是課號 (例如 6651Z052)
            try:
                cspan = row.find_element(By.CSS_SELECTOR, "span[id*='lblCourseName']")
                course_no = (cspan.get_attribute("title") or "").strip()
            except Exception:
                # 再退一步用 hidCOURSEFLNO (完整代碼)
                try:
                    course_no = get_span_text_in_row(row, "hidCOURSEFLNO")
                except Exception:
                    course_no = ""

        # --- course_name: New & Old 都有 lblCourseName ---
        course_name = get_span_text_in_row(row, "lblCourseName")

        # --- teacher_names: 你原本的函式已經支援 hidTeachNames / link spans ---
        teacher_names = parse_teacher_names_from_row(row)

        # --- total_count / credit: 兩邊都有 lblTotalCNT / lblCredit ---
        total_cnt_val = parse_int_safe(get_span_text_in_row(row, "lblTotalCNT"), default=0)
        credit_val = parse_int_safe(get_span_text_in_row(row, "lblCredit"), default=0)

        # --- course_type_name / room_no / week_no: 兩邊 ID 名稱同樣 ---
        course_type_name = get_span_text_in_row(row, "lblCourseTypeName")
        room_no = get_span_text_in_row(row, "lblRoomNo")
        week_no_val = parse_int_safe(get_span_text_in_row(row, "lblWeekNo"), default=0)

        # --- section_no: 一樣用 lblSecNo + 你原本的 parse_section_no ---
        sec_text = get_span_text_in_row(row, "lblSecNo")
        section_no_list = parse_section_no(sec_text)

        doc = {
            "index": index_val,
            "sem_no": sem_no,
            "group_name": group_name,
            "grade": grade_val,
            "class_no": class_no,
            "course_no": course_no,
            "course_name": course_name,
            "teacher_name": teacher_names,
            "total_count": total_cnt_val,
            "credit": credit_val,
            "course_type_name": course_type_name,
            "room_no": room_no,
            "week_no": week_no_val,
            "section_no": section_no_list,
        }

        data_by_sem.setdefault(sem_no, []).append(doc)
        parsed_count += 1

    log(f"Parsed rows: {parsed_count}, skipped rows without index: {skipped_count}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    for sem, docs in data_by_sem.items():
        json_path = os.path.join(data_dir, f"courses_{sem}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)
        log(f"Saved {len(docs)} records to {json_path}")



# -----------------------------
# 4. Main flow – run query per 2 semesters
# -----------------------------
def main() -> None:
    raw = input("Enter semesters separated by commas (e.g. 1142,1141,1132,1131):\n> ")
    target_semesters = [s.strip() for s in raw.split(",") if s.strip()]

    if not target_semesters:
        print("No semesters entered. Exiting.")
        return

    # chunk into groups of 2: e.g. [1142,1141,1132,1131] -> [[1142,1141],[1132,1131]]
    chunks = chunk_semesters(target_semesters, chunk_size=2)
    log(f"Semester chunks (2 per search): {chunks}")

    log(f"Launching Chrome")
    driver = webdriver.Chrome()  # assumes chromedriver is in PATH / managed
    driver.maximize_window()

    try:
        for idx, sem_chunk in enumerate(chunks, start=1):
            log(f"=== Query #{idx}: semesters {sem_chunk} ===")

            # reload page each time to clear previous selections
            driver.get(URL)

            # 1) Select semesters (this chunk)
            click_multi_semesters(driver, sem_chunk)

            # 2) Select all 年級
            click_all_grades(driver)

            # 3) Click 查詢
            click_query_button(driver)

            # 4) Wait for results
            wait_for_results_table(driver, timeout=500)

            # 5) Scrape + save JSON (per sem_no)
            scrape_results_and_save_json(driver)

        log("All chunks done. JSON files are in ./data")

    except Exception as e:
        log(f"Error during Selenium interaction: {e}")

    input("Press Enter to close browser...")
    driver.quit()


if __name__ == "__main__":
    main()
