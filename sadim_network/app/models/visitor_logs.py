# visitor_logs

from app.db.sadim_db import get_db_connection


class visitor_logs:
    @staticmethod
    def log_visit(ip, user_agent, path):
        """تسجيل زيارة جديدة في قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
             "INSERT INTO visitor_logs (ip, user_agent, path) VALUES (%s, %s, %s)",
             (ip, user_agent, path)
         )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def get_all_visits():
        """جلب جميع الزيارات من قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT ip, user_agent, path, timestamp FROM visitor_logs ORDER BY timestamp DESC;")
        visits = cur.fetchall()
        cur.close()
        conn.close()
        return visits

    @staticmethod
    def get_visit_count():
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM visitor_logs")
        count = cur.fetchone()[0]

        cur.close()
        conn.close()
        return count
    
    @staticmethod
    def delete_all_visits():
        """حذف جميع الزيارات من قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM visitor_logs")
        conn.commit()
        cur.close()
        conn.close()
        return True # تم حذف جميع الزيارات بنجاح