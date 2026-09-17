# Tableau計算フィールド Markdown Exporter

## 調査結果

- `.twbx` は ZIP
- `.twb` は UTF-8 XML
- calculation ノード総数: 599
- internal_name ユニーク数: 114
- caption ユニーク数: 96

### 結論

- caption は一意ではない
- internal_name を主キーとする
- Markdown は internal_name 単位で生成する

---

## 現在の機能

- `.twbx` から `.twb` を抽出
- `.twb` XML を解析
- 計算フィールドを抽出
- 計算フィールドごとに Markdown を出力
- 計算フィールド間の依存関係を抽出
- 計算フィールド参照を表示名へ解決
- `formula(raw)` と `formula(resolved)` の両方を出力

---

## 入力

```text
src/
└─ マスタスケジュール・工程工期遵守率.twbx
```

---

## 出力

```text
out/
└─ マスタスケジュール・工程工期遵守率/
   └─ calc_fields/
      ├─ [Calculation_0893963499188226].md
      ├─ [Calculation_930837773830561795].md
      └─ ...
```

---

## 出力ファイル例

```yaml
---
caption: 1_工程工期色分け
internal_name: [1_指定日遵守色分け (コピー)_4573123956556349441]
datatype: string
role: measure
type: nominal

depends_on:
  - caption: 工程工期遵守率
    internal_name: [工程工期遵守率(過去) (コピー)_3063010704483557436]
---
```

```markdown
# 1_工程工期色分け

## formula(raw)

```sql
if [工程工期遵守率(過去) (コピー)_3063010704483557436] >= 0.8 then '80%以上'
elseif [工程工期遵守率(過去) (コピー)_3063010704483557436] >= 0.5 then '50%以上'
elseif [工程工期遵守率(過去) (コピー)_3063010704483557436] < 0.5 then '50%未満'
else null end
```

## formula(resolved)

```sql
if [工程工期遵守率] >= 0.8 then '80%以上'
elseif [工程工期遵守率] >= 0.5 then '50%以上'
elseif [工程工期遵守率] < 0.5 then '50%未満'
else null end
```
```

---

## 今後の予定

- ✅`.exe` 化
- ✅Drag & Drop 対応
- ✅`Documents/tableau_repository` への出力
- Git 管理向けディレクトリ構成の整備

# .exe化コマンド

```bash
pyinstaller ^
  --onefile ^
  --noconsole ^
  --name tableau_calcfield_exporter ^
  --icon assets/ba-90.ico ^
  main.py
```
