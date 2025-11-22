# Kindle2Cosense
kindleのjson形式のexportデータをcosenseの形式に変換するスクリプト

# kindle.jsonのフォーマット
```json
[
  {
    "title": "これからのAI、正しい付き合い方と使い方　「共同知能」と共生するためのヒント",
    "authors": "イーサン・モリック, 久保田 敦子",
    "acquiredTime": 1745834774432,
    "readStatus": "UNKNOWN",
    "asin": "B0DPLVNYS3",
    "productImage": "https://m.media-amazon.com/images/I/31lMOgbgXsL.jpg"
  },
  {
　...
]
```

# cosense.jsonのフォーマット
{
  "name": "osamu-private",
  "displayName": "メモ",
  "exported": 1745724951,
  "users": [
    {
      "id": "5ae710505d885f0014e6312c",
      "name": "osamu",
      "displayName": "osamu",
      "email": "okano.osamu@gmail.com"
    }
  ],
  "pages": [
    {
      "title": "問題解決のステップ",
      "created": 1527519791,
      "updated": 1529315077,
      "id": "5b0c1a2d628ee00014949b21",
      "views": 15,
      "lines": [
        "問題解決のステップ",
        "  学習・知識化",
        "#リスト",
        ""
      ]
    },
```
    {

## 出力規則
cosense.jsonのフォーマットに従って出力すること
kindle.jsonの一項目をcosonseの一ページに変換すること

titleはそのままtitleにかつlines配列に追加
authorsはそのままlines配列に追加
acquiredTimeはそのままcreatedにそして人間が読める形式に変換してlines配列に追加
readStatusはそのままlines配列に追加
asinはそのままlines配列に追加
productImageは[]で囲ってlinesの配列に追加

input/kindle.jsonを読み込み、build/cosense.jsonに書き込むこと


## 機能追加
　
### 著者リンク追加
著者: イーサン・モリック, 久保田 敦子
authorsを分割して、著者名をリンクにする
つまり
イーサン・モリック, 久保田 敦子
ならば
[イーサン・モリック], [久保田 敦子]
にする

### 読了状態リンク追加
"readStatus": "UNKNOWN",
ならば
[UNKNOWN]
にする

### ASINリンク追加
"asin": "B0DPLVNYS3",
の場合
[reader https://read.amazon.co.jp/manga/B0DPLVNYS3]
[amazon https://www.amazon.co.jp/dp/B0DPLVNYS3]
にする

### グルーピング機能
"ダニッチの怪 3　ラヴクラフト傑作集 (ビームコミックス)"
からは
[ダニッチの怪],[ビームコミックス]
がグループにできそう

"らーめん再遊記（１２） (ビッグコミックス)"
からは
[らーめん再遊記],[ビッグコミックス]
がグループにできそう

"ちびまる子ちゃん 10 (りぼんマスコットコミックスDIGITAL)"
からは
[ちびまる子ちゃん],[りぼんマスコットコミックスDIGITAL]
がグループにできそう

"がらくた屋まん太 2巻"
からは
[がらくた屋まん太]
がグループにできそう

"まおゆう魔王勇者　「この我のものとなれ、勇者よ」「断る！」(9) (角川コミックス・エース)"
からは
[まおゆう魔王勇者],[角川コミックス・エース]
がグループにできそう

