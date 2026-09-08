"""
ذكاء | EduAI — بذر بيانات العرض التجريبي (آمن/قابل لإعادة التشغيل)
يُنشئ عند أول تشغيل: حساب طالب مستند + اختبار ثنائي اللغة + فريق مذاكرة.
يُعطَّل بـ: EDUI_SEED_DEMO=0
"""
import json
import os
import uuid
from pathlib import Path

from backend.database import (
    init_db,
    register_user,
    get_db_connection,
    save_document,
    save_document_quiz,
    create_team,
    list_user_teams,
    count_documents,
)
from backend.services.document_service import DocumentService
from backend.config import UPLOAD_DIR

DEMO_DIR = Path(__file__).resolve().parent / "demo"
DEMO_PDF = DEMO_DIR / "sample_lecture.pdf"
DEMO_QUIZ = DEMO_DIR / "quiz_demo.json"
DEMO_EMAIL = "student@univ.edu"
DEMO_PASSWORD = "student123"
DEMO_DOC_ID = "demo_ai_edu"
DEMO_NAME = "طالب المنصة الأكاديمية"


def _has_student() -> bool:
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)).fetchone()
        return bool(row)
    finally:
        conn.close()


def _student_id() -> str:
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)).fetchone()
        return row["id"]
    finally:
        conn.close()


def run() -> None:
    if os.getenv("EDUI_SEED_DEMO", "1").lower() in ("0", "false", "no"):
        return
    init_db()

    if not _has_student():
        print("[seed] إنشاء الحساب التجريبي: student@univ.edu / student123")
        register_user(DEMO_NAME, DEMO_EMAIL, DEMO_PASSWORD, role="student")

    uid = _student_id()
    if count_documents(user_id=uid) == 0 and DEMO_PDF.exists():
        print("[seed] ربط المستند التجريبي sample_lecture.pdf")
        doc_id = DEMO_DOC_ID
        save_path = os.path.join(UPLOAD_DIR, f"{doc_id}_sample_lecture.pdf")
        _copy(DEMO_PDF, save_path)
        pages_data = DocumentService.extract_text_and_pages(save_path)
        chunks = DocumentService.chunk_document(pages_data)
        full_text = "\n\n".join(p["text"] for p in pages_data)
        words_count = len(full_text.split())
        save_document(
            doc_id=doc_id,
            filename="sample_lecture.pdf",
            file_path=save_path,
            pages_count=len(pages_data),
            words_count=words_count,
            full_text=full_text,
            chunks=chunks,
            user_id=uid,
        )
        if DEMO_QUIZ.exists():
            quiz = json.loads(DEMO_QUIZ.read_text(encoding="utf-8"))
            save_document_quiz(doc_id, quiz)
            print("[seed] ربط الاختبار التجريبي (3 أسئلة)")


def _copy(src: Path, dst: str) -> None:
    import shutil

    shutil.copyfile(src, dst)


def seed_teams_if_empty() -> None:
    if os.getenv("EDUI_SEED_DEMO", "1").lower() in ("0", "false", "no"):
        return
    if not _has_student():
        return
    uid = _student_id()
    try:
        teams = list_user_teams(uid)
        if not teams:
            print("[seed] إنشاء فريق المذاكرة التجريبي")
            create_team(owner_id=uid, name="فريق مذاكرة مقرر الذكاء الاصطناعي")
    except Exception as exc:
        print(f"[seed] تحذير (الفريق): {exc}")


if __name__ == "__main__":
    run()
    seed_teams_if_empty()
    print("[seed] اكتمل بذر البيانات التجريبية بنجاح")