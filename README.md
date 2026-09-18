# Tableau計算フィールド Markdown Exporter

Tableauワークブックパッケージ `.twbx` を解析し、ワークブック内の計算フィールドをデータソース別のMarkdownファイルとしてエクスポートするツールです。

計算式だけでなく、データソース情報、データ型、依存する計算フィールド、内部名を表示名へ置換した計算式も出力します。

---

## 主な機能

- `.twbx` から `.twb` を抽出
- `.twb` のXMLを解析
- データソースごとに計算フィールドを抽出
- 計算フィールドごとにMarkdownを生成
- データソース別のフォルダへMarkdownを出力
- 計算フィールド間の依存関係を抽出
- 計算フィールド参照を表示名へ解決
- `formula(raw)` と `formula(resolved)` の両方を出力
- 出力先を一時フォルダで生成してから正式フォルダと入れ替え
- ワークブックから削除された計算フィールドの古いMarkdownを自動削除
- 出力処理に失敗した場合のロールバック
- Windowsで使用できない文字をフォルダ名から除去
- PyInstallerによる単一実行ファイル化
- `.twbx` ファイルのドラッグ＆ドロップ実行
- `.exe` 実行時のメッセージボックス表示
- Windowsのファイルロックによる出力失敗を検出

---

## 調査結果

`.twbx` および `.twb` は、次の形式になっています。

- `.twbx` はZIP形式のアーカイブ
- `.twb` はUTF-8のXML
- 計算フィールドは各データソースの `column/calculation` 要素に格納される
- データソースには表示名の `caption` と内部名の `name` が存在する
- 計算フィールドの `caption` は一意とは限らない
- 計算フィールドの内部名はデータソースをまたいで重複する可能性がある

調査対象ワークブックでは、次の結果となりました。

- `calculation` ノード総数: 599
- `internal_name` ユニーク数: 114
- `caption` ユニーク数: 96

### 結論

計算フィールドは、次の組み合わせで識別します。

```text
データソース内部名 + 計算フィールド内部名
```

Pythonでは、次の型をキーとして使用しています。

```python
CalcFieldKey = tuple[str, str]
```

Markdownは計算フィールドの内部名単位で生成し、各ファイルのFront Matterにデータソースの表示名と内部名を記録します。

---

## 必要環境

### Pythonから実行する場合

- Python 3.10以降
- 標準ライブラリのみで動作

主に次の標準ライブラリを使用しています。

- `pathlib`
- `zipfile`
- `xml.etree.ElementTree`
- `dataclasses`
- `tempfile`
- `shutil`
- `ctypes`
- `json`
- `re`

### `.exe` を生成する場合

- PyInstaller

---

## Pythonからの実行方法

`src` フォルダへ対象の `.twbx` ファイルを配置します。

```text
src/
└─ マスタスケジュール・工程工期遵守率.twbx
```

その後、次のコマンドを実行します。

```bash
python main.py
```

`src` フォルダに複数の `.twbx` が存在する場合、最初に見つかったファイルが処理対象になります。

---

## `.exe` からの実行方法

対象の `.twbx` ファイルを、生成した実行ファイルへドラッグ＆ドロップします。

```text
マスタスケジュール・工程工期遵守率.twbx
    ↓ ドラッグ＆ドロップ
tableau_calcfield_exporter.exe
```

`.exe` を単独でダブルクリックした場合は、使用方法を示すメッセージボックスが表示されます。

---

## 出力先

### Pythonから実行した場合

プロジェクト配下の `out` フォルダに出力されます。

```text
out/
└─ マスタスケジュール・工程工期遵守率/
   └─ calc_fields/
```

### `.exe` へドラッグ＆ドロップした場合

ユーザーのドキュメントフォルダ配下へ出力されます。

```text
Documents/
└─ tableau_repo/
   └─ マスタスケジュール・工程工期遵守率/
      └─ calc_fields/
```

---

## 出力ディレクトリ構成

計算フィールドは、データソースごとのフォルダへ出力されます。

```text
calc_fields/
├─ 01_Parameters/
├─ 02_メイン/
├─ 03_[生産管理] VIE_CHU_SO_OP_ZENGO_ADD_ALL+ITAG/
└─ 04_リアルタイム(1_日)/
```

データソースフォルダ名は、次の形式で生成されます。

```text
連番_データソース表示名
```

例:

```text
01_Parameters
02_メイン
03_工程実績
```

連番は `.twb` のXMLにおけるデータソースの出現順です。

データソースの `caption` が空の場合は、内部名の `name` を使用します。

そのため、TableauのParametersデータソースは次のように出力されます。

```text
01_Parameters
```

### 同名データソースへの対応

表示名が同じデータソースが複数存在しても、先頭の連番によってフォルダ名が重複しないようにしています。

```text
02_メイン
05_メイン
```

データソースの正確な識別には、各MarkdownのFront Matterへ出力される `datasource_internal_name` を使用できます。

### Windowsで使用できない文字

データソースの表示名にWindowsで使用できない文字が含まれる場合は、アンダースコア `_` に置換します。

対象文字:

```text
\ / : * ? " < > |
```

例:

```text
リアルタイム(1:日)
```

出力:

```text
04_リアルタイム(1_日)
```

---

## 出力ファイル例

### ディレクトリ

```text
calc_fields/
└─ 02_メイン/
   └─ [1_指定日遵守色分け (コピー)_4573123956556349441].md
```

### Front Matter

```yaml
---
datasource_caption: "メイン"
datasource_internal_name: "sqlproxy.17lkpp71k8sktb10c6utx0o8ar70"
caption: "1_工程工期色分け"
internal_name: "[1_指定日遵守色分け (コピー)_4573123956556349441]"
datatype: "string"
role: "measure"
type: "nominal"
depends_on:
  - caption: "工程工期遵守率"
    internal_name: "[工程工期遵守率(過去) (コピー)_3063010704483557436]"
---
```

Front Matterには次の情報を出力します。

| 項目 | 内容 |
|---|---|
| `datasource_caption` | データソースの表示名 |
| `datasource_internal_name` | データソースの内部名 |
| `caption` | 計算フィールドの表示名 |
| `internal_name` | 計算フィールドの内部名 |
| `datatype` | データ型 |
| `role` | ディメンションまたはメジャー |
| `type` | Tableau上のフィールド種別 |
| `depends_on` | 参照している計算フィールド |

依存する計算フィールドがない場合は、次のように出力します。

```yaml
depends_on: []
```

---

## 計算式の出力例

Markdownには、元の計算式と表示名へ解決した計算式の両方を出力します。

### formula(raw)

Tableauの内部名を維持した計算式です。

```sql
if [工程工期遵守率(過去) (コピー)_3063010704483557436] >= 0.8 then '80%以上'
elseif [工程工期遵守率(過去) (コピー)_3063010704483557436] >= 0.5 then '50%以上'
elseif [工程工期遵守率(過去) (コピー)_3063010704483557436] < 0.5 then '50%未満'
else null end
```

### formula(resolved)

参照する計算フィールドの内部名を、表示名へ置換した計算式です。

```sql
if [工程工期遵守率] >= 0.8 then '80%以上'
elseif [工程工期遵守率] >= 0.5 then '50%以上'
elseif [工程工期遵守率] < 0.5 then '50%未満'
else null end
```

---

## 古いMarkdownの自動削除

出力時は、既存の `calc_fields` フォルダへMarkdownを追加・上書きするのではなく、新しい一時フォルダへ全ファイルを生成します。

```text
calc_fields.tmp-xxxxxxxx
```

すべてのMarkdown生成に成功した後、次の順序でフォルダを入れ替えます。

```text
calc_fields
    ↓
calc_fields.backup

calc_fields.tmp-xxxxxxxx
    ↓
calc_fields
```

入れ替えに成功した後、バックアップフォルダを削除します。

```text
calc_fields.backup
    ↓
削除
```

この方式により、前回の出力時には存在していたものの、現在のワークブックから削除されている計算フィールドのMarkdownも自動的に削除されます。

例:

```text
前回のワークブック
├─ A.md
├─ B.md
└─ C.md

現在のワークブック
├─ A.md
└─ B.md
```

再出力後:

```text
calc_fields/
├─ A.md
└─ B.md
```

`C.md` は残りません。

---

## エラー処理

### 出力先が使用中の場合

Windowsでは、次のような状態で出力先フォルダの名前変更に失敗する場合があります。

- エクスプローラで `calc_fields` フォルダそのものを開いている
- VS Codeなどのエディタで削除予定のMarkdownを開いている
- 他のアプリケーションが出力先のファイルを使用している

この場合、次の趣旨のエラーメッセージを表示します。

```text
出力先フォルダまたは削除予定ファイルが使用中です。
エクスプローラ、VSCode等で
当該フォルダ・ファイルを閉じてから
再実行してください。
```

`.exe` から実行している場合は、エラー内容をメッセージボックスに表示します。

Pythonから実行している場合は、原因調査ができるようにスタックトレースを出力します。

### バックアップフォルダが残っている場合

前回の処理が正常終了せず、次のフォルダが残っている場合は処理を中止します。

```text
calc_fields.backup
```

バックアップフォルダの内容を確認し、必要に応じて復元または削除してから再実行してください。

---

## PyInstallerによる`.exe`化

次のコマンドで、単一の実行ファイルを生成できます。

```bat
pyinstaller ^
  --onefile ^
  --noconsole ^
  --name tableau_calcfield_exporter ^
  --icon assets/BA-90.ico ^
  main.py
```

生成された実行ファイルは、次の場所に作成されます。

```text
dist/
└─ tableau_calcfield_exporter.exe
```

---

## 実装済み項目

- [x] `.twbx` から `.twb` を抽出
- [x] `.twb` XMLの解析
- [x] 計算フィールドの抽出
- [x] データソース内部名とフィールド内部名による一意識別
- [x] 計算フィールド間の依存関係抽出
- [x] 計算フィールド参照の表示名への解決
- [x] `formula(raw)` の出力
- [x] `formula(resolved)` の出力
- [x] YAML Front Matterの出力
- [x] データソース別のフォルダ出力
- [x] データソースフォルダへの連番付与
- [x] 空のデータソース表示名への対応
- [x] Windows禁止文字の置換
- [x] 削除済み計算フィールドのMarkdown削除
- [x] 一時フォルダを使用した安全な出力
- [x] 出力フォルダのバックアップとロールバック
- [x] Windowsのファイルロック対策
- [x] `.exe` 化
- [x] Drag & Drop対応
- [x] `Documents/tableau_repo` への出力
- [x] `.exe` 実行時のメッセージボックス表示
- [x] Git管理向けディレクトリ構成の整備
