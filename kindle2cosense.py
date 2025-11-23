import json
import os
import re
from datetime import datetime
import uuid


class TitleParser:
    def __init__(self):
        self._vol_indicator_inner_pattern = r'(?:(?:[vV]ol|第|Episode|EP|Season)\.?\s*)?[0-9０-９一二三四五六七八九十百千零〇IVXLCDMivxlcdm]+(?:(?:st|nd|rd|th)話|話|巻|号|編|版|シーズン)?'
        self.vol_indicator_regex = r'^' + self._vol_indicator_inner_pattern + r'$'
        self.simple_trailing_vol_regex = r'\s+' + self._vol_indicator_inner_pattern + r'$'
        self.vol_pattern_for_split = r'\s+' + self._vol_indicator_inner_pattern

    def extract_groups(self, original_title):
        extracted_group_names = []
        
        # 1. Extract from parentheses
        paren_content_list = re.findall(r'[（\(]([^）)]+)[）\)]', original_title)
        for p_content in paren_content_list:
            group_name = self._process_paren_content(p_content)
            if group_name:
                extracted_group_names.append(group_name)
        
        # 2. Extract from main title (removing parentheses and volume info)
        main_title_group = self._extract_main_title_group(original_title, extracted_group_names)
        if main_title_group:
             extracted_group_names.insert(0, main_title_group)
             
        # Remove duplicates while preserving order
        final_groups = list(dict.fromkeys(g for g in extracted_group_names if g))
        return final_groups

    def _process_paren_content(self, p_content):
        p_content_stripped = p_content.strip()
        if re.fullmatch(self.vol_indicator_regex, p_content_stripped, re.IGNORECASE):
            return None

        current_name_candidate = p_content_stripped
        
        # Check for series inside parens like "Series (Publisher)"
        series_match_in_paren = re.match(r'^(.*?)\s*[（\(]([^）)]+)[）\)]$', current_name_candidate)
        if series_match_in_paren:
            base_part = series_match_in_paren.group(1).strip()
            paren_part_content = series_match_in_paren.group(2).strip()
            if base_part and re.fullmatch(self.vol_indicator_regex, paren_part_content, re.IGNORECASE):
                current_name_candidate = base_part

        # Split by volume pattern
        name_parts = re.split(self.vol_pattern_for_split, current_name_candidate, maxsplit=1)
        core_name = name_parts[0].strip()
        
        if not core_name or core_name == current_name_candidate:
            core_name = re.sub(self.simple_trailing_vol_regex, '', current_name_candidate).strip()
        
        if not core_name and current_name_candidate and not re.fullmatch(self.vol_indicator_regex, current_name_candidate, re.IGNORECASE):
            core_name = current_name_candidate
            
        if core_name and not re.fullmatch(self.vol_indicator_regex, core_name, re.IGNORECASE):
            return core_name
        return None

    def _extract_main_title_group(self, original_title, existing_groups):
        title_without_any_parens = re.sub(r'\s*[（\(][^）)]*[）\)]', '', original_title).strip()
        main_title_final = ""
        
        if title_without_any_parens:
            parts = re.split(self.vol_pattern_for_split, title_without_any_parens, maxsplit=1)
            candidate_from_split = parts[0].strip()
            
            if candidate_from_split and candidate_from_split != title_without_any_parens:
                main_title_final = candidate_from_split
            else:
                main_title_final = re.sub(self.simple_trailing_vol_regex, '', title_without_any_parens).strip()
            
            if not main_title_final and title_without_any_parens:
                if not re.fullmatch(self.vol_indicator_regex, title_without_any_parens, re.IGNORECASE):
                    main_title_final = title_without_any_parens
            
            if main_title_final:
                core_title_candidate = re.split(r'[:：　—―－]', main_title_final, maxsplit=1)[0].strip()
                if core_title_candidate and len(core_title_candidate) > 1 and core_title_candidate != main_title_final :
                    if len(main_title_final) - len(core_title_candidate) > 2 or '「' in main_title_final :
                        main_title_final = core_title_candidate
        
        if main_title_final:
            if not re.fullmatch(self.vol_indicator_regex, main_title_final, re.IGNORECASE):
                if main_title_final != original_title or not existing_groups:
                     return main_title_final
        return None

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
    
    # 購入年を格納するセット
    acquired_years = set()
    
    title_parser = TitleParser()

    for book in kindle_data:
        if 'title' not in book:
            print(f"警告: titleがない本をスキップします: {book}")
            continue
            
        # タイムスタンプ変換 (ミリ秒 → 秒)
        acquired_time_sec = book.get('acquiredTime', 0) // 1000
        acquired_dt = datetime.fromtimestamp(acquired_time_sec) if book.get('acquiredTime') else datetime.now()
        jp_time_str = acquired_dt.strftime('%Y年%m月%d日 %H:%M')
        
        year_link = None
        purchase_lines = []
        if book.get('acquiredTime'):
            year_str = acquired_dt.strftime('%Y')
            year_link = f"[{year_str}年]"
            acquired_years.add(year_str)
            purchase_lines = [
                "[* 購入]",
                f" {jp_time_str}",
                f" {year_link}",
                ""
            ]
        else:
            purchase_lines = [
                "[* 購入]",
                " 不明",
                ""
            ]

        # 著者リンク処理
        authors = book.get('authors', '不明')
        if authors:
            author_list = [a.strip() for a in authors.split(',')]
            author_lines = ["[* 著者]"] + [f" [{a}]" for a in author_list] + [""]
        else:
            author_lines = ["[* 著者]", " [不明]", ""]

        # グルーピングリンク追加処理
        group_names = title_parser.extract_groups(book['title'])
        group_lines = []
        if group_names:
            # タイトルと同じリンクは除外する
            filtered_groups = [g for g in group_names if g != book['title']]
            if filtered_groups:
                group_lines = ["[* シリーズ]"] + [f" [{g}]" for g in filtered_groups] + [""]
        
        # ページデータ作成
        asin = book.get('asin', '')
        amazon_url = f"https://www.amazon.co.jp/dp/{asin}"
        product_image = book.get('productImage')

        if product_image:
            amazon_link = f"[{product_image} {amazon_url}]"
        else:
            amazon_link = f"[amazon {amazon_url}]"

        page = {
            "id": str(uuid.uuid4()),
            "title": book['title'],
            "created": acquired_time_sec,
            "updated": acquired_time_sec,
            "views": 15,
            "lines": [
                book.get('title', '無題'),
                *author_lines,
                *purchase_lines,
                *group_lines,
                "[* 読む]",
                f" [クラウド https://read.amazon.co.jp?asin={asin}]",
                amazon_link,
                "",
            ]
        }
        
        cosense_data['pages'].append(page)
    
    # 購入年まとめページを作成
    if acquired_years:
        sorted_years = sorted(list(acquired_years), reverse=True)
        year_links_lines = [f" [{year}年]" for year in sorted_years]
        
        year_summary_page = {
            "id": str(uuid.uuid4()),
            "title": "購入年",
            "created": int(datetime.now().timestamp()),
            "updated": int(datetime.now().timestamp()),
            "views": 1,
            "lines": [
                "購入年",
                *year_links_lines
            ]
        }
        cosense_data['pages'].append(year_summary_page)

    # JSON出力
    output_path = os.path.join(output_dir, 'cosense.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cosense_data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    
    return output_path

if __name__ == '__main__':
    input_file = 'input/kindle.json'
    output_dir = 'build'
    
    output_file = convert_kindle_to_cosense(input_file, output_dir)
    print(f"変換完了: {output_file}")
