from unicodedata import category

import psycopg2
from db.sadim_db import get_db_connection
from datetime import datetime, timedelta
from psycopg2 import extras

class service:
    @staticmethod
    def add_service(image_url, name, category, description, title, price, delivery_time):
        """إضافة خدمة جديدة إلى قاعدة البيانات"""
        
            # إدخال البيانات مع التصنيف
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO services (image_url, name, category, description, title, price, delivery_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (image_url, title, category, description, title, price, delivery_time))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def get_all_services():
        """جلب جميع الخدمات من قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
        cur.execute("SELECT * FROM services;")
        services = cur.fetchall()
    
        cur.close()
        conn.close()
        return services
    
    @staticmethod
    def get_service(service_id):
        """جلب خدمة بواسطة معرفها"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, description, price, image_url, delivery_time FROM services WHERE id=%s", (service_id,))
        service = cur.fetchone()
        cur.close()
        conn.close()
        return service
 
    @staticmethod
    def delete_service(service_id):
        """حذف خدمة من قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM services WHERE id=%s;", (service_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    
    @staticmethod
    def update_service(service_id, image_url,  description, title, price, delivery_time, category):

        """تحديث بيانات خدمة في قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE services
            SET title=%s, description=%s, price=%s, image_url=%s, delivery_time=%s, category=%s
            WHERE id=%s
        """, (title, description, price, image_url, delivery_time, category, service_id)) # الخطوة 2: التحديث
        conn.commit()

        cur.close()
        conn.close()
        return True



    @staticmethod
    def search_services(keyword):
        """البحث عن خدمات بواسطة كلمة مفتاحية في الاسم أو الوصف"""
        conn = get_db_connection()
        cur = conn.cursor()
        search_pattern = f"%{keyword}%"
        cur.execute("""
            SELECT * FROM services
            WHERE name ILIKE %s OR description ILIKE %s;
        """, (search_pattern, search_pattern))
        services = cur.fetchall()
        cur.close()
        conn.close()
        return services
    @staticmethod
    def get_services_by_type(service_type):
        """جلب خدمات بواسطة النوع"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM services WHERE type=%s;", (service_type,))
        services = cur.fetchall()
        cur.close()
        conn.close()
        return services
    
    @staticmethod
    def count_services():
        """عد عدد الخدمات في قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM services;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    
    @staticmethod
    def get_all_books():
        """جلب جميع الكتب من قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

                # جلب الكتب
        cur.execute("""
            SELECT id, image_url, name, category, description, title, type, price, download_url, delivery_time
            FROM services
            WHERE category = 'books'
            ORDER BY created_at DESC
        """)
        books = cur.fetchall()
        cur.close()
        conn.close()
        return books
    
    @staticmethod
    def get_all_tech_tools():
        """جلب جميع الأدوات التقنية من قاعدة البيانات"""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

                # جلب الأدوات التقنية
        cur.execute("""
            SELECT id, image_url, name, category, description, title, type, price, download_url, delivery_time
            FROM services
            WHERE category = 'tech'
            ORDER BY created_at DESC
        """)
        tech_tools = cur.fetchall()
        cur.close()
        conn.close()
        return tech_tools
    
    @staticmethod
    def get_services_by_category(category):
        
     conn = get_db_connection()
     cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
     cur.execute("SELECT * FROM services ORDER BY created_at DESC")
     services = cur.fetchall()
     cur.close()
     conn.close()

     return services

    @staticmethod
    def get_book_by_id(book_id):
        """جلب كتاب بواسطة معرفه"""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, image_url, name, category, description, title, type, price, download_url, delivery_time FROM services WHERE id=%s AND category='books'", (book_id,))
        book = cur.fetchone()
        cur.close()
        conn.close()
        return book

    @staticmethod
    def get_tool_by_id(tool_id):
        """جلب أداة بواسطة معرفها"""
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, image_url, name, category, description, title, type, price, download_url, delivery_time FROM services WHERE id=%s AND category='tech'", (tool_id,))
        tool = cur.fetchone()
        cur.close()
        conn.close()
        return tool