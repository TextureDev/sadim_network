import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2

from config import settings

def get_db_connection():
    conn = psycopg2.connect(
        host=settings.DB_HOST,       # "127.0.0.1" أو "localhost"
        database=settings.DB_NAME,   # اسم قاعدة البيانات
        user=settings.DB_USER,       # اسم المستخدم
        password=settings.DB_PASS,   # كلمة المرور
        port=settings.DB_PORT        # 5432 عادةً
    )
    return conn


def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    
#----------USERS TABLE----------#
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            user_agent TEXT,
            ip VARCHAR(50),
            name VARCHAR(30) NOT NULL,
            email VARCHAR(60) UNIQUE NOT NULL,
            password_hash VARCHAR(260) NOT NULL,
            role VARCHAR(20) DEFAULT 'user', -- admin / user
            profile_image TEXT,
            last_login TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active', -- active / suspended / deleted
            is_verified BOOLEAN DEFAULT FALSE, -- تحقق البريد
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


#----------services TABLE----------#
    cur.execute("""
       CREATE TABLE IF NOT EXISTS services (
         id SERIAL PRIMARY KEY,
         title VARCHAR(150) NOT NULL,
         description TEXT NOT NULL,
         price NUMERIC DEFAULT 0,
         download_url TEXT,
         image_url TEXT,
         delivery_time INT DEFAULT 1,
         category VARCHAR(50) DEFAULT 'tech',
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
       );

    """)

#----------EMAIL VERIFICATION TABLE----------#
    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        token VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_used BOOLEAN DEFAULT FALSE,
        expires_at TIMESTAMP NOT NULL
    );
     """)
   
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visitor_logs (
            id SERIAL PRIMARY KEY,
            ip VARCHAR(100),
            user_agent VARCHAR(300),
            path VARCHAR(300),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    #------ جدول لتسجيل نشاطات المستخدمين
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            email VARCHAR(100),
            username VARCHAR(50),
            ip VARCHAR(50),
            user_agent TEXT,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            desc_text TEXT NOT NULL, 
            pdf_path TEXT NOT NULL,
            download_count INTEGER DEFAULT 0,
            cover_path TEXT NOT NULL
        );
    """)
    #----------PROFILE TABLES----------#
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id         SERIAL PRIMARY KEY,
            key        VARCHAR(100) UNIQUE NOT NULL,
            value      TEXT,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile_stats (
            id    SERIAL PRIMARY KEY,
            label VARCHAR(100) NOT NULL,
            value VARCHAR(100) NOT NULL
        );
    """)
 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile_skills (
            id    SERIAL PRIMARY KEY,
            name  VARCHAR(100) NOT NULL,
            level INTEGER CHECK (level BETWEEN 0 AND 100)
        );
    """)
 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile_projects (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(200) NOT NULL,
            description TEXT,
            url         VARCHAR(500),
            tags        VARCHAR(300)
        );
    """)
 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile_certificates (
            id          SERIAL PRIMARY KEY,
            title       VARCHAR(200) NOT NULL,
            issuer      VARCHAR(200),
            date        VARCHAR(50),
            description TEXT
        );
    """)
 
    conn.commit()
    cur.close()
    conn.close()



if __name__ == '__main__':
    create_tables()
    print("Tables created successfully.")
    print("تم إنشاء الجداول بنجاح.")