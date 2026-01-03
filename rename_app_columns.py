"""
app_nameカラムをapp_idにリネーム
"""
import os
import psycopg2
from urllib.parse import urlparse

def rename_columns():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URLが設定されていません")
        return
    
    # HerokuのDATABASE_URLはpostgres://で始まるが、psycopg2はpostgresql://が必要
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    conn = psycopg2.connect(database_url, sslmode='require')
    cursor = conn.cursor()
    
    try:
        # T_テナントアプリ設定のカラムをリネーム
        print("📝 T_テナントアプリ設定.app_name → app_id")
        cursor.execute('''
            ALTER TABLE "T_テナントアプリ設定" 
            RENAME COLUMN app_name TO app_id
        ''')
        
        # T_店舗アプリ設定のカラムをリネーム
        print("📝 T_店舗アプリ設定.app_name → app_id")
        cursor.execute('''
            ALTER TABLE "T_店舗アプリ設定" 
            RENAME COLUMN app_name TO app_id
        ''')
        
        conn.commit()
        print("✅ カラム名変更完了")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ エラー: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    rename_columns()
