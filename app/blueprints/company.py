# -*- coding: utf-8 -*-
"""
企業情報管理Blueprint
国税庁APIを使用した企業情報の検索・登録・管理
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime

from ..utils import get_db, _sql
from ..utils.decorators import require_roles
from ..utils.nta_api import NTAInvoiceAPI, extract_invoice_number_from_text

bp = Blueprint('company', __name__, url_prefix='/company')


@bp.route('/')
@require_roles(['system_admin', 'tenant_admin', 'admin', 'employee'])
def index():
    """企業情報一覧"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('テナントが選択されていません', 'error')
        return redirect(url_for('auth.index'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # 企業情報一覧を取得
    sql = _sql(conn, '''
        SELECT 
            id,
            会社名,
            会社名カナ,
            郵便番号,
            住所,
            電話番号,
            インボイス登録番号,
            インボイス登録有無,
            created_at
        FROM "T_企業情報"
        WHERE tenant_id = %s
        ORDER BY created_at DESC
    ''')
    cur.execute(sql, (tenant_id,))
    
    companies = cur.fetchall()
    conn.close()
    
    return render_template('company_list.html', companies=companies)


@bp.route('/search', methods=['GET', 'POST'])
@require_roles(['system_admin', 'tenant_admin', 'admin', 'employee'])
def search():
    """企業情報検索"""
    if request.method == 'GET':
        return render_template('company_search.html')
    
    # POST: 検索実行
    search_type = request.form.get('search_type')
    search_value = request.form.get('search_value')
    
    if not search_value:
        flash('検索キーワードを入力してください', 'error')
        return redirect(request.url)
    
    try:
        api = NTAInvoiceAPI()
        results = []
        
        if search_type == 'invoice_number':
            # インボイス登録番号で検索
            result = api.search_by_invoice_number(search_value)
            if result:
                results = [result]
        
        elif search_type == 'corporate_number':
            # 法人番号で検索
            result = api.search_by_corporate_number(search_value)
            if result:
                results = [result]
        
        elif search_type == 'company_name':
            # 会社名で検索
            results = api.search_by_name(search_value)
        
        if not results:
            flash('該当する企業が見つかりませんでした', 'warning')
        
        return render_template('company_search.html', results=results, search_value=search_value)
        
    except Exception as e:
        flash(f'検索エラー: {str(e)}', 'error')
        return redirect(request.url)


@bp.route('/register', methods=['POST'])
@require_roles(['system_admin', 'tenant_admin', 'admin'])
def register():
    """企業情報を登録"""
    tenant_id = session.get('tenant_id')
    
    if not tenant_id:
        flash('テナントが選択されていません', 'error')
        return redirect(url_for('company.index'))
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # 既存チェック（インボイス登録番号）
        invoice_number = request.form.get('invoice_number')
        if invoice_number:
            sql = _sql(conn, 'SELECT id FROM "T_企業情報" WHERE インボイス登録番号 = %s')
            cur.execute(sql, (invoice_number,))
            existing = cur.fetchone()
            
            if existing:
                flash('この企業は既に登録されています', 'warning')
                return redirect(url_for('company.index'))
        
        # 登録
        sql = _sql(conn, '''
            INSERT INTO "T_企業情報" (
                tenant_id,
                法人番号,
                インボイス登録番号,
                会社名,
                会社名カナ,
                郵便番号,
                住所,
                電話番号,
                インボイス登録有無,
                インボイス登録日
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''')
        
        cur.execute(sql, (
            tenant_id,
            request.form.get('corporate_number'),
            invoice_number,
            request.form.get('company_name'),
            request.form.get('company_name_kana'),
            request.form.get('postal_code'),
            request.form.get('address'),
            request.form.get('phone'),
            1 if invoice_number else 0,
            request.form.get('registration_date')
        ))
        
        if hasattr(conn, 'commit'):
            conn.commit()
        
        conn.close()
        
        flash('企業情報を登録しました', 'success')
        return redirect(url_for('company.index'))
        
    except Exception as e:
        flash(f'登録エラー: {str(e)}', 'error')
        return redirect(url_for('company.search'))


@bp.route('/<int:company_id>')
@require_roles(['system_admin', 'tenant_admin', 'admin', 'employee'])
def detail(company_id):
    """企業情報詳細"""
    tenant_id = session.get('tenant_id')
    
    conn = get_db()
    cur = conn.cursor()
    
    sql = _sql(conn, '''
        SELECT * FROM "T_企業情報"
        WHERE id = %s AND tenant_id = %s
    ''')
    cur.execute(sql, (company_id, tenant_id))
    
    company = cur.fetchone()
    conn.close()
    
    if not company:
        flash('企業情報が見つかりません', 'error')
        return redirect(url_for('company.index'))
    
    return render_template('company_detail.html', company=company)


@bp.route('/<int:company_id>/edit', methods=['GET', 'POST'])
@require_roles(['system_admin', 'tenant_admin', 'admin'])
def edit(company_id):
    """企業情報編集"""
    tenant_id = session.get('tenant_id')
    
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'GET':
        sql = _sql(conn, '''
            SELECT * FROM "T_企業情報"
            WHERE id = %s AND tenant_id = %s
        ''')
        cur.execute(sql, (company_id, tenant_id))
        company = cur.fetchone()
        conn.close()
        
        if not company:
            flash('企業情報が見つかりません', 'error')
            return redirect(url_for('company.index'))
        
        return render_template('company_edit.html', company=company)
    
    # POST: 更新処理
    try:
        sql = _sql(conn, '''
            UPDATE "T_企業情報"
            SET 
                会社名 = %s,
                会社名カナ = %s,
                郵便番号 = %s,
                住所 = %s,
                電話番号 = %s,
                事業概要 = %s,
                最終更新日 = CURRENT_TIMESTAMP
            WHERE id = %s AND tenant_id = %s
        ''')
        
        cur.execute(sql, (
            request.form.get('company_name'),
            request.form.get('company_name_kana'),
            request.form.get('postal_code'),
            request.form.get('address'),
            request.form.get('phone'),
            request.form.get('business_description'),
            company_id,
            tenant_id
        ))
        
        if hasattr(conn, 'commit'):
            conn.commit()
        
        conn.close()
        
        flash('企業情報を更新しました', 'success')
        return redirect(url_for('company.detail', company_id=company_id))
        
    except Exception as e:
        flash(f'更新エラー: {str(e)}', 'error')
        return redirect(request.url)


@bp.route('/<int:company_id>/delete', methods=['POST'])
@require_roles(['system_admin', 'tenant_admin', 'admin'])
def delete(company_id):
    """企業情報削除"""
    tenant_id = session.get('tenant_id')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        sql = _sql(conn, 'DELETE FROM "T_企業情報" WHERE id = %s AND tenant_id = %s')
        cur.execute(sql, (company_id, tenant_id))
        
        if hasattr(conn, 'commit'):
            conn.commit()
        
        conn.close()
        
        flash('企業情報を削除しました', 'success')
        
    except Exception as e:
        flash(f'削除エラー: {str(e)}', 'error')
    
    return redirect(url_for('company.index'))


@bp.route('/api/search_by_phone', methods=['POST'])
@require_roles(['system_admin', 'tenant_admin', 'admin', 'employee'])
def api_search_by_phone():
    """電話番号で企業検索（API）"""
    phone = request.json.get('phone')
    
    if not phone:
        return jsonify({'error': '電話番号が指定されていません'}), 400
    
    tenant_id = session.get('tenant_id')
    
    # まずデータベースから検索
    conn = get_db()
    cur = conn.cursor()
    
    sql = _sql(conn, '''
        SELECT * FROM "T_企業情報"
        WHERE tenant_id = %s AND 電話番号 LIKE %s
        LIMIT 1
    ''')
    cur.execute(sql, (tenant_id, f'%{phone}%'))
    
    company = cur.fetchone()
    conn.close()
    
    if company:
        return jsonify({
            'found': True,
            'company': {
                'id': company[0] if isinstance(company, tuple) else company['id'],
                'name': company[4] if isinstance(company, tuple) else company['会社名'],
                'address': company[7] if isinstance(company, tuple) else company['住所'],
            }
        })
    
    return jsonify({'found': False})
