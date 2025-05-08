import json
import os
from datetime import datetime
import uuid

def convert_kindle_to_cosense(input_path, output_dir):
    # 出力ディレクトリがなければ作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # kindle.jsonを読み込み
    with open(input_path, 'r', encoding='utf-8') as f:
        kindle_data = json.load(f)
    
    # 変換後のデータ構造
    cosense_data = {
        "user": {
            "name": "Kindle User",
            "email": "user@example.com"
        },
        "pages": []
    }
    
    for book in kindle_data:
        if 'title' not in book:
            print(f"警告: titleがない本をスキップします: {book}")
            continue
            
        # タイムスタンプ変換 (ミリ秒 → 秒)
        acquired_time_sec = book.get('acquiredTime', 0) // 1000
        acquired_dt = datetime.fromtimestamp(acquired_time_sec) if book.get('acquiredTime') else datetime.now()
        jp_time_str = acquired_dt.strftime('%Y年%m月%d日 %H:%M')
        
        # 著者リンク処理
        authors = book.get('authors', '不明')
        author_links = [f"[{a.strip()}]" for a in authors.split(',')] if authors else ["[不明]"]

        # グルーピングリンク追加処理
        def extract_groups(title):
            import re
            groups = []
            # 括弧内の出版社名やシリーズ名を抽出
            paren_groups = re.findall(r'\(([^)]+)\)', title)
            groups.extend(paren_groups)
            # 括弧を除いたタイトル部分
            title_no_paren = re.sub(r'\s*\([^)]*\)', '', title)
            # 巻数や号数のパターンを除去して主要タイトルを抽出
            main_title = re.sub(r'[\s　]*[（(]?\d+[巻巻]?[）)]?$', '', title_no_paren).strip()
            if main_title:
                groups.insert(0, main_title)
            # 巻数や号数だけのグループは除外する
            groups = [g for g in groups if not re.fullmatch(r'\d+', g)]
            return groups

        group_names = extract_groups(book['title'])
        if group_names:
            # タイトルと同じリンクは除外する
            filtered_groups = [g for g in group_names if g != book['title']]
            group_links = [f"[{g}]" for g in filtered_groups] if filtered_groups else []
        else:
            # シリーズ名が抽出できなかった場合はリンクを追加しない（タイトル全体のリンクは追加しない）
            group_links = []

        # ページデータ作成
        page = {
            "id": str(uuid.uuid4()),
            "title": book['title'],
            "created": acquired_time_sec,
            "updated": acquired_time_sec,
            "views": 15,
            "lines": [
                book.get('title', '無題'),
                *author_links,
                f"購入日: {jp_time_str}" if 'acquiredTime' in book else "購入日: 不明",
                f"[{book.get('readStatus', 'UNKNOWN')}]",
                f"[reader https://read.amazon.co.jp/manga/{book.get('asin', '')}]",
                f"[amazon https://www.amazon.co.jp/dp/{book.get('asin', '')}]",
                *group_links,
                *([f"[{book['productImage']}]"] if 'productImage' in book else [])
            ]
        }
        
        cosense_data['pages'].append(page)
    
    # JSON出力
    output_path = os.path.join(output_dir, 'cosense.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cosense_data, f, ensure_ascii=False, indent=2)
    
    return output_path

if __name__ == '__main__':
    input_file = 'input/kindle.json'
    output_dir = 'build'
    
    output_file = convert_kindle_to_cosense(input_file, output_dir)
    print(f"変換完了: {output_file}")
