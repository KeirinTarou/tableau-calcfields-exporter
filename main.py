from pathlib import Path
import sys
from dataclasses import dataclass, field
import zipfile
import xml.etree.ElementTree as ET
import re
import ctypes
import json

SRC_DIR = Path(__file__).parent / "src"
OUT_DIR = Path(__file__).parent / "out"

@dataclass
class CalcField:
    datasource_caption: str
    datasource_internal_name: str

    caption: str
    internal_name: str
    formula: str
    datatype: str | None
    role: str | None
    field_type: str | None

    depends_on: list[str] = field(default_factory=list)

CalcFieldKey = tuple[str, str]

def is_frozen() -> bool:
    """ PyInstallerで生成された実行ファイルか判定"""

    return bool(getattr(sys, "frozen", False))

def show_message(
    message: str, title: str = "Tableau Markdown Exporter") -> None:
    """ Windowsのメッセージボックスを表示する"""

    ctypes.windll.user32.MessageBoxW(
        None, 
        message, 
        title, 
        0x40, 
    )

def get_output_dir(twbx_path: Path) -> Path:
    """ 出力先パスを解決する"""

    if len(sys.argv) >= 2:
        root_dir = (
            Path.home()
            / "Documents"
            / "tableau_repo"
        )
    else:
        root_dir = OUT_DIR

    return (
        root_dir
        / twbx_path.stem
        / "calc_fields"
    )

def get_twbx_path() -> Path:
    """ 対象の.twbxファイルを取得する

    :return: .twbxファイルのPathオブジェクト
    :rtype: Path
    """

    if len(sys.argv) >= 2:
        return Path(sys.argv[1])

    twbx_files = list(SRC_DIR.glob("*.twbx"))

    if not twbx_files:
        raise FileNotFoundError(
            ".twbxファイルが見つからない。（(　ﾟдﾟ)､ﾍﾟｯ < クソが）"
        )

    return twbx_files[0]

def load_twb_xml(twbx_path: Path) -> str:
    """ .twbxファイルからtwbのXMLを取り出す

    :param twbx_path: .twbxファイルのPathオブジェクト
    :type twbx_path: Path
    :return: .twbxに同梱されている.twbのXMLテキスト
    :rtype: str
    """

    with zipfile.ZipFile(twbx_path) as z:
        twb_name = \
            next(
                info.filename
                for info in z.infolist()
                if info.filename.lower().endswith(".twb")
            )

        return z.read(twb_name).decode("utf-8")

def parse_twb_xml(xml_text: str) -> ET.Element:
    """ ワークブックのXMLをパースする
    
    :param xml_text: XMLの文字列
    :type xml_text: str
    :return: XML要素ツリーオブジェクト
    :rtype: ET.Element
    """

    return ET.fromstring(xml_text)

def collect_calc_fields(
        root: ET.Element) -> dict[CalcFieldKey, CalcField]:
    """ ワークブック内の計算フィールドを収集
    
    :param root: XMLのルート要素
    :type root: ET.Element
    :return: データソース内部名とフィールド内部名をキーとするCalcFieldのdict
    :rtype: dict[CalcFieldKey, CalcField]
    """

    calc_fields: dict[CalcFieldKey, CalcField] = {}

    for datasource in root.findall(
            "./datasources/datasource"):

        datasource_caption = \
            datasource.get("caption") or ""

        datasource_internal_name = \
            datasource.get("name") or ""

        for col in datasource.findall("column"):
            calc = col.find("calculation")

            if calc is None:
                continue

            internal_name = col.get("name")

            if internal_name is None:
                continue

            key = (
                datasource_internal_name, 
                internal_name, 
            )

            if key in calc_fields:
                continue

            calc_fields[key] = \
                CalcField(
                    datasource_caption=datasource_caption, 
                    datasource_internal_name=datasource_internal_name, 
                    caption=col.get("caption") or "", 
                    internal_name=internal_name, 
                    formula=calc.get("formula") or "", 
                    datatype=col.get("datatype"), 
                    role=col.get("role"), 
                    field_type=col.get("type"), 
                )

    return calc_fields

def resolve_dependencies(
        calc_fields: dict[CalcFieldKey, CalcField]) -> None:
    """ []で囲まれた内部名をcaptionに変換する
    
    """

    # []で囲まれた文字列にマッチ
    pattern = r"\[[^\]]+\]"

    for calc_field in calc_fields.values():
        refs = \
            re.findall(pattern, calc_field.formula)

        calc_field.depends_on = list(
            dict.fromkeys(
                ref
                for ref in refs
                if (calc_field.datasource_internal_name, ref) in calc_fields
            )
        )

def resolve_formula(
        calc_field: CalcField, 
        calc_fields: dict[CalcFieldKey, CalcField]) -> str:
    """ 計算フィールド参照を表示名に解決した計算式を返す"""

    formula = calc_field.formula

    for dep in calc_field.depends_on:
        dep_key = (calc_field.datasource_internal_name, dep)
        formula = \
            formula.replace(
                dep, 
                f"[{calc_fields[dep_key].caption}]"
            )

    return formula

def export_markdown(
        calc_field: CalcField, 
        calc_fields: dict[CalcFieldKey, CalcField]) -> str:
    """ CalcFieldオブジェクトから出力用マークダウンテキストを作成
    
    :param calc_field: 計算フィールドオブジェクト
    :type calc_field: CalcField
    :param calc_fields: 計算フィールドオブジェクトのディクショナリ
    :type calc_fields: dict[str, CalcField]
    :return: マークダウン用テキスト
    :rtype: str
    """

    if calc_field.depends_on:
        depends_on_lines = ["depends_on:"]

        for dep in calc_field.depends_on:
            dep_key = (calc_field.datasource_internal_name, dep)
            dep_field = calc_fields[dep_key]

            depends_on_lines.extend([
                (
                    "  - caption: "
                    f"{to_yaml_scalar(dep_field.caption)}"
                ), 
                (
                    "    internal_name: "
                    f"{to_yaml_scalar(dep_field.internal_name)}"
                ), 
            ])
        
        depends_on_text = "\n".join(depends_on_lines)
    else:
        depends_on_text = "depends_on: []"

    return \
f"""---
datasource_caption: {to_yaml_scalar(calc_field.datasource_caption)}
datasource_internal_name: {to_yaml_scalar(calc_field.datasource_internal_name)}
caption: {to_yaml_scalar(calc_field.caption)}
internal_name: {to_yaml_scalar(calc_field.internal_name)}
datatype: {to_yaml_scalar(calc_field.datatype)}
role: {to_yaml_scalar(calc_field.role)}
type: {to_yaml_scalar(calc_field.field_type)}
{depends_on_text}
---

# {calc_field.caption}

## formula(raw)
```sql
{calc_field.formula}
```

## formula(resolved)
```sql
{resolve_formula(calc_field, calc_fields)}
```
"""

def to_yaml_scalar(value: str | None) -> str:
    """ 値をYAMLのスカラーとして安全に出力する"""

    if value is None:
        return "null"

    return json.dumps(
        value, 
        ensure_ascii=False, 
    )

def write_markdown(
        calc_field: CalcField, 
        calc_fields: dict[CalcFieldKey, CalcField], 
        out_dir: Path) -> Path:
    out_dir.mkdir(
        parents=True, 
        exist_ok=True, 
    )

    out_path = \
        out_dir / f"{calc_field.internal_name}.md"

    out_path.write_text(
        export_markdown(calc_field, calc_fields), 
        encoding="utf-8", 
    )

    return out_path

def main():
    if is_frozen() and len(sys.argv) < 2:
        show_message(
            "使い方: \n"
            "    .twbxファイルをこの実行ファイルに"
            "ドラッグ＆ドロップしてください。", 
            "安易に`.exe`をダブルクリックしてはいけない。（(　ﾟдﾟ)､ﾍﾟｯ < クソが。）"
        )
        return

    twbx_path = get_twbx_path()
    xml_text = load_twb_xml(twbx_path)
    root = parse_twb_xml(xml_text)
    calc_fields = collect_calc_fields(root)

    resolve_dependencies(calc_fields)

    out_dir = get_output_dir(twbx_path)

    for calc_field in calc_fields.values():
        write_markdown(
            calc_field, 
            calc_fields, 
            out_dir)

    if is_frozen():
        show_message(
            f"出力が完了しました。: \n{out_dir}", 
            "( ´_ゝ`) < 終了♪"
        )

if __name__ == "__main__":
    main()
