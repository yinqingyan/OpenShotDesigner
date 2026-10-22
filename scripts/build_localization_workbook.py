#!/usr/bin/env python3
"""Build the human-review workbook from the TypeScript AST catalog."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import xlsxwriter


ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "localization" / "zh-CN" / "english-source-catalog.json"
DRAFTS = ROOT / "localization" / "zh-CN" / "zh-cn-drafts.json"
TERMS = ROOT / "localization" / "zh-CN" / "zh-cn-terminology.json"
OUTPUT = ROOT / "localization" / "zh-CN" / "OpenShotDesigner-zh-CN-review.xlsx"
PREVIEW_DIR = Path("/private/tmp/openshot-localization-previews")
PREVIEW_OUTPUT = PREVIEW_DIR / "OpenShotDesigner-zh-CN-preview.xlsx"

FONT = "PingFang SC"
NAVY = "#243044"
BLUE = "#2F5D7C"
GREEN = "#4E6A43"
PURPLE = "#6B4E71"
BROWN = "#7A5C45"
INK = "#111827"
MUTED = "#4B5563"
BORDER = "#D1D5DB"
INPUT = "#FFF3CD"
HIGH_RISK = "#FEE2E2"


def chunks(values: list[list[object]], size: int) -> list[list[list[object]]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def clean(value: object) -> object:
    if not isinstance(value, str):
        return value
    value = "".join(char for char in value if char in "\n\t" or ord(char) >= 32)
    return value[:32767]


def write_cell(worksheet, row: int, col: int, value: object, cell_format=None) -> None:
    value = clean(value)
    if isinstance(value, bool):
        worksheet.write_boolean(row, col, value, cell_format)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        worksheet.write_number(row, col, value, cell_format)
    else:
        worksheet.write_string(row, col, "" if value is None else str(value), cell_format)


def add_review_sheet(
    workbook,
    name: str,
    title: str,
    description: str,
    headers: list[str],
    rows: list[list[object]],
    widths: list[int],
    tab_color: str,
    translation_col: int | None = None,
    reviewed_translation_col: int | None = None,
    status_col: int | None = None,
    risk_col: int | None = None,
    table_prefix: str = "Table",
    preview: bool = False,
) -> object:
    worksheet = workbook.add_worksheet(name)
    worksheet.set_tab_color(tab_color)
    worksheet.hide_gridlines(2)
    worksheet.set_column(0, 0, 3)
    for index, width in enumerate(widths, start=1):
        worksheet.set_column(index, index, width)

    title_format = workbook.add_format(
        {"font_name": FONT, "font_size": 16, "bold": True, "font_color": INK}
    )
    description_format = workbook.add_format(
        {"font_name": FONT, "font_size": 10, "italic": True, "font_color": MUTED}
    )
    header_format = workbook.add_format(
        {
            "font_name": FONT,
            "font_size": 10,
            "bold": True,
            "font_color": INK,
            "bg_color": "#E5E7EB",
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
            "border": 1,
            "border_color": "#CBD5E1",
        }
    )
    body_format = workbook.add_format(
        {
            "font_name": FONT,
            "font_size": 10,
            "font_color": INK,
            "valign": "vcenter",
            "text_wrap": True,
            "border": 1,
            "border_color": "#E5E7EB",
        }
    )
    centered_format = workbook.add_format(
        {
            "font_name": FONT,
            "font_size": 10,
            "font_color": INK,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
            "border": 1,
            "border_color": "#E5E7EB",
        }
    )
    input_format = workbook.add_format(
        {
            "font_name": FONT,
            "font_size": 10,
            "font_color": INK,
            "bg_color": INPUT,
            "valign": "vcenter",
            "text_wrap": True,
            "border": 1,
            "border_color": "#F6D365",
        }
    )

    last_col = len(headers)
    worksheet.merge_range(0, 1, 0, last_col, title, title_format)
    worksheet.merge_range(1, 1, 1, last_col, description, description_format)
    worksheet.set_row(0, 26)
    worksheet.set_row(1, 24)

    header_row = 3
    worksheet.set_row(header_row, 28)
    for col, header in enumerate(headers, start=1):
        worksheet.write_string(header_row, col, header, header_format)

    for row_index, values in enumerate(rows, start=4):
        for col_index, value in enumerate(values, start=1):
            selected_format = centered_format if col_index - 1 in {0, 7, 8, 11} else body_format
            if translation_col is not None and col_index - 1 == translation_col:
                selected_format = input_format
            if reviewed_translation_col is not None and col_index - 1 == reviewed_translation_col:
                selected_format = input_format
            if status_col is not None and col_index - 1 == status_col:
                selected_format = centered_format
            if risk_col is not None and col_index - 1 == risk_col:
                selected_format = centered_format
            write_cell(worksheet, row_index, col_index, value, selected_format)

    data_last_row = max(header_row, header_row + len(rows))
    if rows:
        worksheet.autofilter(header_row, 1, data_last_row, last_col)
    worksheet.freeze_panes(4, 4)
    worksheet.set_landscape()
    worksheet.set_margins(0.25, 0.25, 0.45, 0.45)
    worksheet.repeat_rows(header_row)

    if status_col is not None and rows:
        status_letter = chr(ord("A") + status_col + 1)
        worksheet.data_validation(
            4,
            status_col + 1,
            data_last_row,
            status_col + 1,
            {"validate": "list", "source": ["待确认", "需修改", "已确认"]},
        )
        worksheet.conditional_format(
            4,
            status_col + 1,
            data_last_row,
            status_col + 1,
            {
                "type": "cell",
                "criteria": "==",
                "value": '"已确认"',
                "format": workbook.add_format(
                    {"bg_color": "#DCFCE7", "font_color": "#166534", "bold": True}
                ),
            },
        )
        worksheet.conditional_format(
            4,
            status_col + 1,
            data_last_row,
            status_col + 1,
            {
                "type": "cell",
                "criteria": "==",
                "value": '"需修改"',
                "format": workbook.add_format(
                    {"bg_color": "#FEF3C7", "font_color": "#92400E", "bold": True}
                ),
            },
        )
        del status_letter

    if risk_col is not None and rows:
        worksheet.conditional_format(
            4,
            risk_col + 1,
            data_last_row,
            risk_col + 1,
            {
                "type": "cell",
                "criteria": "==",
                "value": '"高"',
                "format": workbook.add_format(
                    {"bg_color": HIGH_RISK, "font_color": "#991B1B", "bold": True}
                ),
            },
        )
    return worksheet


def add_summary(workbook, metadata: dict, preview: bool) -> None:
    worksheet = workbook.add_worksheet("Summary")
    worksheet.set_tab_color(NAVY)
    worksheet.hide_gridlines(2)
    worksheet.set_column("A:A", 22)
    worksheet.set_column("B:B", 20)
    worksheet.set_column("C:C", 3)
    worksheet.set_column("D:D", 20)
    worksheet.set_column("E:E", 20)
    worksheet.set_column("F:F", 3)
    worksheet.set_column("G:G", 18)
    worksheet.set_column("H:H", 18)
    worksheet.set_column("I:I", 3)
    worksheet.set_column("J:J", 18)
    worksheet.set_column("K:K", 20)

    title_format = workbook.add_format(
        {"font_name": FONT, "font_size": 18, "bold": True, "font_color": INK}
    )
    subtitle_format = workbook.add_format(
        {"font_name": FONT, "font_size": 10, "italic": True, "font_color": MUTED}
    )
    label_format = workbook.add_format(
        {
            "font_name": FONT,
            "font_size": 10,
            "bold": True,
            "font_color": "#374151",
            "bg_color": "#E5E7EB",
            "valign": "vcenter",
            "border": 1,
            "border_color": BORDER,
        }
    )
    value_format = workbook.add_format(
        {
            "font_name": FONT,
            "font_size": 10,
            "font_color": INK,
            "bg_color": "#F9FAFB",
            "valign": "vcenter",
            "text_wrap": True,
            "border": 1,
            "border_color": BORDER,
        }
    )
    section_format = workbook.add_format(
        {"font_name": FONT, "font_size": 12, "bold": True, "font_color": INK}
    )
    body_format = workbook.add_format(
        {
            "font_name": FONT,
            "font_size": 10,
            "font_color": "#374151",
            "valign": "top",
            "text_wrap": True,
        }
    )
    note_format = workbook.add_format(
        {
            "font_name": FONT,
            "font_size": 10,
            "font_color": "#92400E",
            "bg_color": "#FEF3C7",
            "valign": "vcenter",
            "text_wrap": True,
            "border": 1,
            "border_color": "#F6D365",
        }
    )

    worksheet.merge_range("B2:K2", "Open Shot Designer — 简体中文本地化审校", title_format)
    worksheet.merge_range(
        "B3:K3",
        "专业初译、逐条确认、全部确认后进入合成的本地化审校表",
        subtitle_format,
    )
    worksheet.print_area("B1:L24")
    worksheet.fit_to_pages(1, 1)
    worksheet.set_row(1, 30)
    worksheet.set_row(2, 22)

    counts = metadata["counts"]
    blocks = [
        (
            "B5:C8",
            [
                ("项目版本", f"v{metadata['version']}"),
                ("源码提交", metadata["commit"][:12]),
                ("本地化分支", metadata["branch"]),
                ("提取方式", "TypeScript AST"),
            ],
        ),
        (
            "E5:F8",
            [
                ("候选字符串", counts["uniqueCandidates"]),
                ("可翻译唯一文案", counts["translatableUnique"]),
                ("PDF/打印文案", counts["pdfUnique"]),
                ("术语建议", counts["terminology"]),
            ],
        ),
        (
            "H5:I8",
            [
                ("源码命中", counts["candidateOccurrences"]),
                ("来源文件", counts["sourceFiles"]),
                ("不翻译项", counts["doNotTranslateUnique"]),
                ("人工保留规则", counts.get("manualDoNotTranslate", 0)),
            ],
        ),
        (
            "K5:L8",
            [
                ("英文文本", "已导出"),
                ("专业初译", "已生成，待逐条确认"),
                ("确认工具", "zh-CN-review.html"),
                ("合成门槛", "全部条目已确认"),
            ],
        ),
    ]
    for block, rows in blocks:
        first_cell, _last_cell = block.split(":")
        col = xlsxwriter.utility.xl_cell_to_rowcol(first_cell)[1]
        start_row = 4
        for offset, (label, value) in enumerate(rows):
            worksheet.write_string(start_row + offset, col, label, label_format)
            worksheet.write(start_row + offset, col + 1, value, value_format)
            worksheet.set_row(start_row + offset, 26)

    worksheet.write_string("B11", "执行顺序", section_format)
    sequence = [
        "1. 打开 zh-CN-review.html，逐条核对专业初译；也可在 Excel 中逐项填写。",
        "2. 每条点击“确认并下一项”或“需修改”；保留英文项必须“确认保留英文”。",
        "3. 全部待确认项处理完后，工具才解锁“进入合成”，并导出已确认清单。",
        "4. 术语、品牌、变量、快捷键和 PDF 技术备注必须在确认时一并核对。",
        "5. 合成完成后运行 lint、测试、构建，并逐页面截图回归。",
    ]
    for offset, text in enumerate(sequence, start=12):
        worksheet.merge_range(offset - 1, 1, offset - 1, 11, text, body_format)
        worksheet.set_row(offset - 1, 28)

    worksheet.write_string("B18", "基线记录", section_format)
    baseline = [
        "lint：通过（TypeScript、ESLint、编码检查）。",
        "tests：238 / 239 个测试文件通过；2840 / 2841 个测试通过。既有失败位于 callSheetSun.test.ts。",
        "build：通过；Vite 仅提示大分块。",
    ]
    for offset, text in enumerate(baseline, start=19):
        worksheet.merge_range(offset - 1, 1, offset - 1, 11, text, body_format)
        worksheet.set_row(offset - 1, 28)

    warning = (
        "门禁规则：专业初译不等于完成。只有所有条目为“已确认”，才能进入代码合成；"
        "当前不执行合成，避免未经人工核对的译文进入应用。"
    )
    worksheet.merge_range("B24:L24", warning, note_format)
    worksheet.set_row(23, 38)
    if preview:
        worksheet.write_string("N2", "PREVIEW", workbook.add_format({"bold": True, "font_color": "#B91C1C"}))

def build(preview: bool) -> Path:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    draft_data = json.loads(DRAFTS.read_text(encoding="utf-8"))
    term_data = json.loads(TERMS.read_text(encoding="utf-8"))
    drafts = {entry["id"]: entry for entry in draft_data["entries"]}
    metadata = data["metadata"]
    entries = data["entries"]
    terms = term_data["entries"]
    metadata = dict(metadata)
    metadata["counts"] = dict(metadata["counts"])
    metadata["counts"]["terminology"] = len(terms)
    ui_entries = [entry for entry in entries if entry["translatable"]]
    pdf_entries = [entry for entry in ui_entries if entry["pdf"]]
    do_not_entries = [entry for entry in entries if not entry["translatable"]]
    source_occurrences = [occurrence for entry in ui_entries for occurrence in entry["occurrences"]]

    if preview:
        ui_entries = ui_entries[:20]
        pdf_entries = pdf_entries[:12]
        do_not_entries = do_not_entries[:12]
        source_occurrences = []
        output = PREVIEW_OUTPUT
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    else:
        output = OUTPUT

    workbook = xlsxwriter.Workbook(output, {"use_future_functions": False})
    add_summary(workbook, metadata, preview)
    workflow_rows = [
        ["1", "查看专业初译", "先看英文原文、专业初译、置信度和面板语境说明。", "理解该行在应用中的实际含义。"],
        ["2", "按条确认", "打开 zh-CN-review.html；正确则点“确认并下一项”，需要修改则点“需修改”。", "状态离开“待确认”。"],
        ["3", "修改译文", "在审校工具或 Excel 的“核对后简体中文”列填写最终版本。", "译文完整，术语和变量数量一致。"],
        ["4", "确认保留英文", "品牌、枚举、协议、变量和技术值必须点“确认保留英文”。", "所有保留项明确经过人工确认。"],
        ["5", "验收到合成门槛", "待确认和需修改都为 0 后，工具解锁“进入合成”。", "导出 zh-cn-confirmed.json。"],
        ["6", "进入代码合成", "使用已确认清单建立正式 i18n 键并逐页迁移。", "此步骤在当前阶段不自动执行。"],
    ]
    add_review_sheet(
        workbook,
        "Review Workflow",
        "中文确认流程与合成门禁",
        "流程固定为：专业初译 → 逐条确认/修改 → 全部确认 → 导出确认清单 → 代码合成。",
        ["步骤", "操作", "具体做法", "完成条件"],
        workflow_rows,
        [8, 22, 72, 48],
        "#334155",
        table_prefix="ReviewWorkflow",
        preview=preview,
    )

    ui_rows = [
        [
            entry["id"],
            entry["source"],
            drafts[entry["id"]]["translation"],
            "",
            drafts[entry["id"]]["confidence"],
            drafts[entry["id"]]["status"],
            drafts[entry["id"]]["context_note"],
            drafts[entry["id"]]["disposition"],
            entry["key"],
            entry["module"],
            entry["textType"],
            entry["sourceRefs"],
            entry["placeholders"],
            "Yes" if entry["pdf"] else "No",
            entry["layoutRisk"],
            entry["note"] or drafts[entry["id"]]["reason"],
            "",
        ]
        for entry in ui_entries
    ]
    ui_chunks = chunks(ui_rows, 2000)
    for index, rows in enumerate(ui_chunks, start=1):
        suffix = f" {index}" if len(ui_chunks) > 1 else ""
        add_review_sheet(
            workbook,
            f"UI Strings{suffix}",
            f"Open Shot Designer 界面英文本地化清单{suffix}",
            f"专业初译已填入；共 {len(ui_chunks)} 个审校分表。你逐条核对后填写“核对后简体中文”并把状态改为“已确认”。",
            [
                "编号",
                "英文原文",
                "专业初译",
                "核对后简体中文",
                "初译置信度",
                "状态",
                "专业依据/上下文说明",
                "处置",
                "临时键",
                "模块",
                "文本类型",
                "来源位置",
                "变量",
                "PDF/打印",
                "布局风险",
                "审校备注",
                "修改说明",
            ],
            rows,
            [13, 50, 46, 46, 11, 11, 62, 12, 18, 22, 18, 42, 20, 11, 10, 44, 42],
            BLUE,
            translation_col=2,
            reviewed_translation_col=3,
            status_col=5,
            risk_col=14,
            table_prefix=f"UIStrings{index}",
            preview=preview,
        )

    term_rows = [
        [
            index,
            term["source"],
            term["translation"],
            "",
            term["module"].removeprefix("术语/"),
            term["confidence"],
            term["status"],
            term["context_note"],
        ]
        for index, term in enumerate(terms, start=1)
    ]
    add_review_sheet(
        workbook,
        "Terminology",
        "电影制作与摄影术语建议",
        "这些译名用于保持界面一致；专业初译仍需逐条核对后才能被合成阶段使用。",
        ["序号", "英文术语", "专业初译", "核对后简体中文", "使用范围", "置信度", "状态", "说明"],
        term_rows,
        [8, 30, 30, 30, 22, 10, 11, 62],
        GREEN,
        translation_col=2,
        reviewed_translation_col=3,
        status_col=6,
        table_prefix="Terminology",
        preview=preview,
    )

    pdf_rows = [
        [
            entry["id"],
            entry["source"],
            drafts[entry["id"]]["translation"],
            "",
            drafts[entry["id"]]["confidence"],
            drafts[entry["id"]]["status"],
            drafts[entry["id"]]["context_note"],
            drafts[entry["id"]]["disposition"],
            entry["module"],
            entry["sourceRefs"],
            entry["placeholders"],
            entry["layoutRisk"],
            "Yes",
            entry["note"] or "需验证嵌入式中文字体、断行与分页。",
            "",
        ]
        for entry in pdf_entries
    ]
    add_review_sheet(
        workbook,
        "PDF Strings",
        "PDF 与打印文案",
        "这些文案进入 canvas/report/PDF 输出；中文 PDF 必须先替换仅支持 WinAnsi 的标准字体。逐条确认后才能进入合成。",
        [
            "编号",
            "英文原文",
            "专业初译",
            "核对后简体中文",
            "初译置信度",
            "状态",
            "专业依据/上下文说明",
            "处置",
            "模块",
            "来源位置",
            "变量",
            "布局风险",
            "PDF/打印",
            "技术备注",
            "修改说明",
        ],
        pdf_rows,
        [13, 52, 46, 46, 11, 11, 62, 12, 22, 44, 20, 10, 11, 54, 42],
        PURPLE,
        translation_col=2,
        reviewed_translation_col=3,
        status_col=5,
        risk_col=11,
        table_prefix="PDFStrings",
        preview=preview,
    )

    do_not_rows = [
        [
            index,
            entry["source"],
            entry.get("reason", ""),
            entry.get("module", ""),
            entry.get("sourceRefs", ""),
            entry.get("note", ""),
        ]
        for index, entry in enumerate(do_not_entries, start=1)
    ]
    do_not_chunks = chunks(do_not_rows, 1000)
    for index, rows in enumerate(do_not_chunks, start=1):
        suffix = f" {index}" if len(do_not_chunks) > 1 else ""
        add_review_sheet(
            workbook,
            f"Do Not Translate{suffix}",
            f"不翻译项与保留项{suffix}",
            "品牌、协议、文件格式、内部值和示例内容保持稳定；短标签可按上下文另建显示译文。",
            ["序号", "英文原文", "原因", "模块/规则", "来源位置", "说明"],
            rows,
            [8, 44, 28, 24, 48, 58],
            BROWN,
            table_prefix=f"DoNotTranslate{index}",
            preview=preview,
        )

    if source_occurrences:
        source_rows = [
            [
                index,
                item["key"],
                item["source"],
                item["file"],
                item["line"],
                item["column"],
                item["module"],
                item["textType"],
                item["context"],
                item["placeholders"],
                "Yes" if item["pdf"] else "No",
                item["layoutRisk"],
            ]
            for index, item in enumerate(source_occurrences, start=1)
        ]
        add_review_sheet(
            workbook,
            "Source Index",
            "源码命中索引",
            "用于定位迁移点；正式实施时把字符串替换为稳定键，并保持枚举值和持久化值稳定。",
            ["序号", "临时键", "英文原文", "文件", "行", "列", "模块", "文本类型", "上下文", "变量", "PDF/打印", "布局风险"],
            source_rows,
            [8, 18, 50, 54, 8, 8, 22, 18, 24, 22, 11, 10],
            "#6B7280",
            table_prefix="SourceIndex",
            preview=preview,
        )

    workbook.close()
    return output


if __name__ == "__main__":
    preview_mode = "--preview" in sys.argv
    result = build(preview_mode)
    print(result)
