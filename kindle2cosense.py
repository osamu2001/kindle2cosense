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
        def extract_groups(original_title):
            import re
            extracted_group_names = []

            # Base pattern for volume indicators (e.g., "Vol. 1", "第2巻", "3", "Season 1")
            # This captures the core part of a volume string.
            _vol_indicator_inner_pattern = r'(?:(?:[vV]ol|第|Episode|EP|Season)\.?\s*)?[0-9０-９一二三四五六七八九十百千零〇IVXLCDMivxlcdm]+(?:(?:st|nd|rd|th)話|話|巻|号|編|版|シーズン)?'

            # Regex to check if a string *is exactly and only* a volume indicator.
            # Used with re.fullmatch(vol_indicator_regex, text, re.IGNORECASE)
            vol_indicator_regex = r'^' + _vol_indicator_inner_pattern + r'$'

            # Regex to remove a *trailing* volume indicator along with preceding whitespace.
            # Used with re.sub(simple_trailing_vol_regex, '', text).strip()
            simple_trailing_vol_regex = r'\s+' + _vol_indicator_inner_pattern + r'$'

            # Pattern to split a title by the first occurrence of volume information (preceded by a space).
            # Used with re.split(vol_pattern_for_split, text, maxsplit=1)
            # The result parts[0] is the text before the volume info.
            vol_pattern_for_split = r'\s+' + _vol_indicator_inner_pattern
            
            # Part 1: Extract from parentheses (likely labels/publishers or sub-series)
            paren_content_list = re.findall(r'\(([^)]+)\)', original_title)
            
            # Note: The original specific vol_indicator_regex definition that was previously here
            # has been effectively moved and generalized by the definitions above.
            
            for p_content in paren_content_list:
                p_content_stripped = p_content.strip()
                if not re.fullmatch(vol_indicator_regex, p_content_stripped, re.IGNORECASE):
                    # p_content_stripped is not a simple volume indicator.
                    # It could be "Series Name (Vol. 1)", "Series Name Vol. 1", "Publisher", etc.
                    # We need to try to extract a clean series/group name from it.

                    current_name_candidate = p_content_stripped

                    # Step 1: If p_content_stripped is like "Name (Vol)", extract "Name".
                    # Example: "ギャラリーフェイク (39)" -> "ギャラリーフェイク"
                    series_match_in_paren = re.match(r'^(.*?)\s*\(([^)]+)\)$', current_name_candidate)
                    if series_match_in_paren:
                        base_part = series_match_in_paren.group(1).strip()
                        paren_part_content = series_match_in_paren.group(2).strip()
                        if base_part and re.fullmatch(vol_indicator_regex, paren_part_content, re.IGNORECASE):
                            # It was "Name (Vol)", so use "Name" as the candidate for further processing.
                            current_name_candidate = base_part
                        # If not "Name (Vol)" (e.g., "Name (Publisher)"), current_name_candidate remains p_content_stripped,
                        # which is correct as "Name (Publisher)" might be a valid group name.

                    # Step 2: Remove trailing non-parenthesized volume info from current_name_candidate.
                    # Example: "Series Name Vol. 1" -> "Series Name"
                    # This reuses the regexes from Part 2.
                    
                    # Try splitting by general volume pattern
                    name_parts = re.split(vol_pattern_for_split, current_name_candidate, maxsplit=1)
                    core_name = name_parts[0].strip()

                    if not core_name or core_name == current_name_candidate: # If split didn't change or resulted in empty
                        # Fallback: try removing only strictly trailing volume information
                        core_name = re.sub(simple_trailing_vol_regex, '', current_name_candidate).strip()

                    # If stripping resulted in an empty string, and the original p_content_stripped
                    # (or its version after parenthesized vol removal) was not a volume, use that.
                    if not core_name and current_name_candidate and not re.fullmatch(vol_indicator_regex, current_name_candidate, re.IGNORECASE):
                        core_name = current_name_candidate
                    
                    # Add the processed core_name if it's valid and not a volume indicator itself
                    if core_name and not re.fullmatch(vol_indicator_regex, core_name, re.IGNORECASE):
                        extracted_group_names.append(core_name)
                # else: p_content_stripped was a volume indicator, so it's correctly skipped.

            # Part 2: Extract main series title
            # Remove ALL parenthesized content to get a base for the main title.
            title_without_any_parens = re.sub(r'\s*\([^)]*\)', '', original_title).strip()
            
            main_title_final = ""
            if title_without_any_parens:
                # Pattern to split title by volume information.
                # This tries to capture "Series Name" from "Series Name Vol. X Subtitle" or "Series Name X巻"
                parts = re.split(vol_pattern_for_split, title_without_any_parens, maxsplit=1)
                candidate_from_split = parts[0].strip()

                if candidate_from_split and candidate_from_split != title_without_any_parens:
                    main_title_final = candidate_from_split
                else:
                    # Fallback: try removing only strictly trailing volume information
                    main_title_final = re.sub(simple_trailing_vol_regex, '', title_without_any_parens).strip()
                
                # If title_without_any_parens was *only* a volume (e.g. "3巻"), main_title_final might be empty.
                # In that case, restore title_without_any_parens if it's not a volume indicator itself.
                if not main_title_final and title_without_any_parens:
                    if not re.fullmatch(vol_indicator_regex, title_without_any_parens, re.IGNORECASE):
                        main_title_final = title_without_any_parens
                
                # Refine main_title_final by removing common subtitles after a separator
                if main_title_final:
                    core_title_candidate = re.split(r'[:：　—―－]', main_title_final, maxsplit=1)[0].strip() # Added em-dash variants
                    # Only update if core_title_candidate is non-empty and significantly shorter or more "core"
                    if core_title_candidate and len(core_title_candidate) > 1 and core_title_candidate != main_title_final : # Min length 2 for core
                        # Check if the part removed was substantial (e.g. a long subtitle)
                        if len(main_title_final) - len(core_title_candidate) > 2 or '「' in main_title_final : # Heuristic for actual subtitle
                            main_title_final = core_title_candidate
                        

            if main_title_final:
                # Add as a primary candidate if it's not a volume indicator itself
                if not re.fullmatch(vol_indicator_regex, main_title_final, re.IGNORECASE):
                    # Insert at the beginning if it's a meaningful extraction,
                    # or if no other groups were found (it might be the title itself).
                    if main_title_final != original_title or not extracted_group_names:
                         extracted_group_names.insert(0, main_title_final)

            # Deduplicate while preserving order (Python 3.7+ dict trick)
            final_groups = list(dict.fromkeys(g for g in extracted_group_names if g)) # Ensure no empty strings
            return final_groups

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