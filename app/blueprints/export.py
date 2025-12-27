# -*- coding: utf-8 -*-
"""
エクスポートBlueprint
仕訳データのCSV出力と会計ソフト連携
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from datetime import datetime

from ..utils import get_db, _sql
from ..utils.decorators import require_roles
from ..utils.export import export_journals, get_supported_formats

bp = Blueprint('export', __name__, url_prefix='/export')


@bp.route('/')
@require_roles(['system_admin', 'tenant_admin', 'admin', 'employee'])
def index():
    """エクスポート画面"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('テナントが選択されていません', 'error')
        return redirect(url_for('auth.index'))
    
    # サポートしている形式を取得
    formats = get_supported_formats()
    
    # 仕訳の統計情報を取得
    conn = get_db()
    cur = conn.cursor()
    
    # 確認済み仕訳数
    sql = _sql(conn, '''
        SELECT COUNT(*) FROM "T_仕訳"
        WHERE tenant_id = %s AND 確認済みフラグ = 1
    ''')
    cur.execute(sql, (tenant_id,))
    confirmed_count = cur.fetchone()[0]
    
    # 未確認仕訳数
    sql = _sql(conn, '''
        SELECT COUNT(*) FROM "T_仕訳"
        WHERE tenant_id = %s AND 確認済みフラグ = 0
    ''')
    cur.execute(sql, (tenant_id,))
    unconfirmed_count = cur.fetchone()[0]
    
    # 日付範囲を取得
    sql = _sql(conn, '''
        SELECT MIN(日付), MAX(日付) FROM "T_仕訳"
        WHERE tenant_id = %s
    ''')
    cur.execute(sql, (tenant_id,))
    date_range = cur.fetchone()
    
    conn.close()
    
    return render_template(
        'export_index.html',
        formats=formats,
        confirmed_count=confirmed_count,
        unconfirmed_count=unconfirmed_count,
        min_date=date_range[0] if date_range else None,
        max_date=date_range[1] if date_range else None
    )


@bp.route('/download', methods=['POST'])
@require_roles(['system_admin', 'tenant_admin', 'admin', 'employee'])
def download():
    """CSV出力実行"""
    tenant_id = session.get('tenant_id')
    
    try:
        # パラメータ取得
        format_id = request.form.get('format')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        confirmed_only = request.form.get('confirmed_only') == '1'
        
        if not format_id:
            flash('出力形式を選択してください', 'error')
            return redirect(url_for('export.index'))
        
        # 仕訳データを取得
        conn = get_db()
        cur = conn.cursor()
        
        sql_parts = ['SELECT * FROM "T_仕訳" WHERE tenant_id = %s']
        params = [tenant_id]
        
        # 日付範囲フィルタ
        if start_date:
            sql_parts.append('AND 日付 >= %s')
            params.append(start_date)
        
        if end_date:
            sql_parts.append('AND 日付 <= %s')
            params.append(end_date)
        
        # 確認済みフィルタ
        if confirmed_only:
            sql_parts.append('AND 確認済みフラグ = 1')
        
        sql_parts.append('ORDER BY 日付 ASC, id ASC')
        
        sql = _sql(conn, ' '.join(sql_parts))
        cur.execute(sql, tuple(params))
        
        rows = cur.fetchall()
        conn.close()
        
        if not rows:
            flash('エクスポートする仕訳がありません', 'warning')
            return redirect(url_for('export.index'))
        
        # 辞書形式に変換
        journals = []
        for row in rows:
            if isinstance(row, tuple):
                journals.append({
                    'id': row[0],
                    'tenant_id': row[1],
                    '証憑ID': row[2],
                    '企業情報ID': row[3],
                    '日付': row[4],
                    '借方勘定科目': row[5],
                    '借方金額': row[6],
                    '借方補助科目': row[7],
                    '貸方勘定科目': row[8],
                    '貸方金額': row[9],
                    '貸方補助科目': row[10],
                    '摘要': row[11],
                    '自動生成フラグ': row[12],
                    '確認済みフラグ': row[13],
                })
            else:
                journals.append(dict(row))
        
        # CSV生成
        csv_content = export_journals(journals, format_id)
        
        # ファイル名生成
        format_names = {f['id']: f['name'] for f in get_supported_formats()}
        format_name = format_names.get(format_id, 'export')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'journal_{format_name}_{timestamp}.csv'
        
        # レスポンス生成
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'  # BOM付きUTF-8
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        flash(f'エクスポートエラー: {str(e)}', 'error')
        return redirect(url_for('export.index'))


@bp.route('/preview', methods=['POST'])
@require_roles(['system_admin', 'tenant_admin', 'admin', 'employee'])
def preview():
    """エクスポートプレビュー"""
    tenant_id = session.get('tenant_id')
    
    try:
        # パラメータ取得
        format_id = request.form.get('format')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        confirmed_only = request.form.get('confirmed_only') == '1'
        
        if not format_id:
            flash('出力形式を選択してください', 'error')
            return redirect(url_for('export.index'))
        
        # 仕訳データを取得（最大10件）
        conn = get_db()
        cur = conn.cursor()
        
        sql_parts = ['SELECT * FROM "T_仕訳" WHERE tenant_id = %s']
        params = [tenant_id]
        
        if start_date:
            sql_parts.append('AND 日付 >= %s')
            params.append(start_date)
        
        if end_date:
            sql_parts.append('AND 日付 <= %s')
            params.append(end_date)
        
        if confirmed_only:
            sql_parts.append('AND 確認済みフラグ = 1')
        
        sql_parts.append('ORDER BY 日付 ASC, id ASC LIMIT 10')
        
        sql = _sql(conn, ' '.join(sql_parts))
        cur.execute(sql, tuple(params))
        
        rows = cur.fetchall()
        conn.close()
        
        if not rows:
            flash('プレビューする仕訳がありません', 'warning')
            return redirect(url_for('export.index'))
        
        # 辞書形式に変換
        journals = []
        for row in rows:
            if isinstance(row, tuple):
                journals.append({
                    'id': row[0],
                    'tenant_id': row[1],
                    '証憑ID': row[2],
                    '企業情報ID': row[3],
                    '日付': row[4],
                    '借方勘定科目': row[5],
                    '借方金額': row[6],
                    '借方補助科目': row[7],
                    '貸方勘定科目': row[8],
                    '貸方金額': row[9],
                    '貸方補助科目': row[10],
                    '摘要': row[11],
                    '自動生成フラグ': row[12],
                    '確認済みフラグ': row[13],
                })
            else:
                journals.append(dict(row))
        
        # CSV生成
        csv_content = export_journals(journals, format_id)
        
        # プレビュー用に行分割
        csv_lines = csv_content.strip().split('\n')
        
        # サポートしている形式を取得
        formats = get_supported_formats()
        format_name = next((f['name'] for f in formats if f['id'] == format_id), format_id)
        
        return render_template(
            'export_preview.html',
            format_id=format_id,
            format_name=format_name,
            csv_lines=csv_lines,
            journal_count=len(journals),
            start_date=start_date,
            end_date=end_date,
            confirmed_only=confirmed_only
        )
        
    except Exception as e:
        flash(f'プレビューエラー: {str(e)}', 'error')
        return redirect(url_for('export.index'))
