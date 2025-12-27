# -*- coding: utf-8 -*-
"""
CSV出力と会計ソフト連携ユーティリティ
仕訳データを各種会計ソフト形式でエクスポート
"""

import csv
import io
from typing import List, Dict
from datetime import datetime


def export_to_generic_csv(journals: List[Dict]) -> str:
    """
    汎用CSV形式で仕訳をエクスポート
    
    Args:
        journals: 仕訳データのリスト
    
    Returns:
        CSV文字列
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # ヘッダー
    writer.writerow([
        '日付',
        '借方勘定科目',
        '借方補助科目',
        '借方金額',
        '貸方勘定科目',
        '貸方補助科目',
        '貸方金額',
        '摘要'
    ])
    
    # データ
    for journal in journals:
        writer.writerow([
            journal.get('日付', ''),
            journal.get('借方勘定科目', ''),
            journal.get('借方補助科目', ''),
            journal.get('借方金額', 0),
            journal.get('貸方勘定科目', ''),
            journal.get('貸方補助科目', ''),
            journal.get('貸方金額', 0),
            journal.get('摘要', '')
        ])
    
    return output.getvalue()


def export_to_yayoi_csv(journals: List[Dict]) -> str:
    """
    弥生会計形式でエクスポート
    
    Args:
        journals: 仕訳データのリスト
    
    Returns:
        CSV文字列（弥生会計形式）
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 弥生会計のヘッダー
    writer.writerow([
        '伝票No',
        '決算',
        '取引日付',
        '借方勘定科目',
        '借方補助科目',
        '借方部門',
        '借方税区分',
        '借方金額',
        '借方税額',
        '貸方勘定科目',
        '貸方補助科目',
        '貸方部門',
        '貸方税区分',
        '貸方金額',
        '貸方税額',
        '摘要',
        'No',
        '期日',
        'タイプ',
        '生成元',
        '仕訳メモ',
        'タグ',
        'MID'
    ])
    
    # データ
    for idx, journal in enumerate(journals, start=1):
        date_str = journal.get('日付', '')
        if isinstance(date_str, str) and date_str:
            # YYYY-MM-DD形式をYYYY/MM/DD形式に変換
            date_str = date_str.replace('-', '/')
        
        writer.writerow([
            idx,  # 伝票No
            '',  # 決算
            date_str,  # 取引日付
            journal.get('借方勘定科目', ''),
            journal.get('借方補助科目', ''),
            '',  # 借方部門
            '対象外',  # 借方税区分（デフォルト）
            journal.get('借方金額', 0),
            0,  # 借方税額
            journal.get('貸方勘定科目', ''),
            journal.get('貸方補助科目', ''),
            '',  # 貸方部門
            '対象外',  # 貸方税区分（デフォルト）
            journal.get('貸方金額', 0),
            0,  # 貸方税額
            journal.get('摘要', ''),
            '',  # No
            '',  # 期日
            '',  # タイプ
            '',  # 生成元
            '',  # 仕訳メモ
            '',  # タグ
            ''   # MID
        ])
    
    return output.getvalue()


def export_to_freee_csv(journals: List[Dict]) -> str:
    """
    freee会計形式でエクスポート
    
    Args:
        journals: 仕訳データのリスト
    
    Returns:
        CSV文字列（freee形式）
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # freeeのヘッダー
    writer.writerow([
        '収支区分',
        '管理番号',
        '発生日',
        '決済期日',
        '取引先',
        '勘定科目',
        '税区分',
        '金額',
        '税込金額',
        '備考',
        '品目',
        '部門',
        'メモタグ（複数指定可、カンマ区切り）',
        'セグメント1',
        'セグメント2',
        'セグメント3',
        '決済口座',
        '決済金額'
    ])
    
    # データ（借方・貸方を分けて出力）
    for journal in journals:
        date_str = journal.get('日付', '')
        description = journal.get('摘要', '')
        
        # 借方
        writer.writerow([
            '支出',  # 収支区分
            '',  # 管理番号
            date_str,  # 発生日
            '',  # 決済期日
            journal.get('借方補助科目', ''),  # 取引先
            journal.get('借方勘定科目', ''),  # 勘定科目
            '課税対象外',  # 税区分（デフォルト）
            journal.get('借方金額', 0),  # 金額
            journal.get('借方金額', 0),  # 税込金額
            description,  # 備考
            '',  # 品目
            '',  # 部門
            '',  # メモタグ
            '',  # セグメント1
            '',  # セグメント2
            '',  # セグメント3
            '',  # 決済口座
            ''   # 決済金額
        ])
        
        # 貸方
        writer.writerow([
            '収入',  # 収支区分
            '',  # 管理番号
            date_str,  # 発生日
            '',  # 決済期日
            journal.get('貸方補助科目', ''),  # 取引先
            journal.get('貸方勘定科目', ''),  # 勘定科目
            '課税対象外',  # 税区分（デフォルト）
            journal.get('貸方金額', 0),  # 金額
            journal.get('貸方金額', 0),  # 税込金額
            description,  # 備考
            '',  # 品目
            '',  # 部門
            '',  # メモタグ
            '',  # セグメント1
            '',  # セグメント2
            '',  # セグメント3
            '',  # 決済口座
            ''   # 決済金額
        ])
    
    return output.getvalue()


def export_to_mfcloud_csv(journals: List[Dict]) -> str:
    """
    マネーフォワードクラウド会計形式でエクスポート
    
    Args:
        journals: 仕訳データのリスト
    
    Returns:
        CSV文字列（MFクラウド形式）
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # MFクラウドのヘッダー
    writer.writerow([
        '取引No',
        '取引日',
        '借方勘定科目',
        '借方補助科目',
        '借方部門',
        '借方税区分',
        '借方金額(円)',
        '借方税額',
        '貸方勘定科目',
        '貸方補助科目',
        '貸方部門',
        '貸方税区分',
        '貸方金額(円)',
        '貸方税額',
        '摘要',
        '仕訳メモ',
        'タグ',
        'MID'
    ])
    
    # データ
    for idx, journal in enumerate(journals, start=1):
        date_str = journal.get('日付', '')
        
        writer.writerow([
            idx,  # 取引No
            date_str,  # 取引日
            journal.get('借方勘定科目', ''),
            journal.get('借方補助科目', ''),
            '',  # 借方部門
            '課税対象外',  # 借方税区分
            journal.get('借方金額', 0),
            0,  # 借方税額
            journal.get('貸方勘定科目', ''),
            journal.get('貸方補助科目', ''),
            '',  # 貸方部門
            '課税対象外',  # 貸方税区分
            journal.get('貸方金額', 0),
            0,  # 貸方税額
            journal.get('摘要', ''),
            '',  # 仕訳メモ
            '',  # タグ
            ''   # MID
        ])
    
    return output.getvalue()


def export_to_pca_csv(journals: List[Dict]) -> str:
    """
    PCA会計形式でエクスポート
    
    Args:
        journals: 仕訳データのリスト
    
    Returns:
        CSV文字列（PCA会計形式）
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # PCA会計のヘッダー
    writer.writerow([
        '伝票日付',
        '伝票番号',
        '借方科目コード',
        '借方科目名',
        '借方補助コード',
        '借方補助名',
        '借方部門コード',
        '借方部門名',
        '借方税区分',
        '借方金額',
        '借方消費税額',
        '貸方科目コード',
        '貸方科目名',
        '貸方補助コード',
        '貸方補助名',
        '貸方部門コード',
        '貸方部門名',
        '貸方税区分',
        '貸方金額',
        '貸方消費税額',
        '摘要'
    ])
    
    # データ
    for idx, journal in enumerate(journals, start=1):
        date_str = journal.get('日付', '')
        
        writer.writerow([
            date_str,  # 伝票日付
            idx,  # 伝票番号
            '',  # 借方科目コード
            journal.get('借方勘定科目', ''),
            '',  # 借方補助コード
            journal.get('借方補助科目', ''),
            '',  # 借方部門コード
            '',  # 借方部門名
            '0',  # 借方税区分（0=課税対象外）
            journal.get('借方金額', 0),
            0,  # 借方消費税額
            '',  # 貸方科目コード
            journal.get('貸方勘定科目', ''),
            '',  # 貸方補助コード
            journal.get('貸方補助科目', ''),
            '',  # 貸方部門コード
            '',  # 貸方部門名
            '0',  # 貸方税区分（0=課税対象外）
            journal.get('貸方金額', 0),
            0,  # 貸方消費税額
            journal.get('摘要', '')
        ])
    
    return output.getvalue()


def get_supported_formats() -> List[Dict[str, str]]:
    """
    サポートしているエクスポート形式のリストを取得
    
    Returns:
        形式情報のリスト
    """
    return [
        {
            'id': 'generic',
            'name': '汎用CSV',
            'description': 'シンプルな仕訳CSV形式'
        },
        {
            'id': 'yayoi',
            'name': '弥生会計',
            'description': '弥生会計インポート形式'
        },
        {
            'id': 'freee',
            'name': 'freee会計',
            'description': 'freee会計インポート形式'
        },
        {
            'id': 'mfcloud',
            'name': 'マネーフォワードクラウド会計',
            'description': 'MFクラウド会計インポート形式'
        },
        {
            'id': 'pca',
            'name': 'PCA会計',
            'description': 'PCA会計インポート形式'
        }
    ]


def export_journals(journals: List[Dict], format_id: str) -> str:
    """
    指定された形式で仕訳をエクスポート
    
    Args:
        journals: 仕訳データのリスト
        format_id: エクスポート形式ID
    
    Returns:
        CSV文字列
    
    Raises:
        ValueError: サポートされていない形式IDの場合
    """
    exporters = {
        'generic': export_to_generic_csv,
        'yayoi': export_to_yayoi_csv,
        'freee': export_to_freee_csv,
        'mfcloud': export_to_mfcloud_csv,
        'pca': export_to_pca_csv
    }
    
    exporter = exporters.get(format_id)
    if not exporter:
        raise ValueError(f'サポートされていない形式: {format_id}')
    
    return exporter(journals)
