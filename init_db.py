#!/usr/bin/env python3
"""
データベース初期化スクリプト
Heroku上でデータベーステーブルを作成します
"""

import os
import sys

# アプリケーションのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def init_database():
    """データベーステーブルを初期化"""
    with app.app_context():
        try:
            # すべてのテーブルを作成
            db.create_all()
            print("✅ データベーステーブルの作成に成功しました")
            
            # 作成されたテーブルを確認
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n作成されたテーブル一覧 ({len(tables)}個):")
            for table in tables:
                print(f"  - {table}")
            
            return True
            
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("データベース初期化を開始します...")
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', '未設定')[:50]}...")
    
    success = init_database()
    
    if success:
        print("\n✅ データベース初期化が完了しました")
        sys.exit(0)
    else:
        print("\n❌ データベース初期化に失敗しました")
        sys.exit(1)
