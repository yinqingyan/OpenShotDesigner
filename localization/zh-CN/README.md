# Open Shot Designer 简体中文本地化

本目录保存简体中文本地化的英文来源清单、审校表和实施记录。

## 当前基线

- 上游项目：`koosoli/OpenShotDesigner`
- 上游版本：`v1.4.2`
- 基线提交：`766a80df36a8c8cde3b14cbd482ce0e298adbd04`
- 工作分支：`codex/zh-cn-localization`
- 提取范围：`src/**/*.ts` 和 `src/**/*.tsx`，排除测试与 `src/generated`
- 提取方式：TypeScript AST

本次扫描结果：

| 项目 | 数量 |
| --- | ---: |
| 生产源码文件 | 524 |
| 候选源码命中 | 9,440 |
| 按英文原文归并后的候选 | 7,611 |
| 需要人工判断的候选文案 | 4,985 |
| 涉及 PDF/打印的候选文案 | 776 |
| 不翻译项 | 2,626 |
| 领域术语建议 | 58 |

`4,985` 是提取规则筛选出的候选审校文案，并非完成翻译后的精确替换点。同一句原文
可能出现在不同语义中，正式实施时需要按上下文拆成独立、稳定的 i18n 键。

## 文件

- `english-source-catalog.json`：完整机器可读清单，保留源码位置、上下文、变量、布局风险和保留原因。
- `english-ui-review.csv`：便于版本控制审阅的界面英文清单。
- `OpenShotDesigner-zh-CN-review.xlsx`：供人工填写中文译文和审校状态的工作簿。

工作簿包含：

- `Summary`：版本、计数、执行顺序与基线结果。
- `UI Strings 1-3`：界面候选文案和中文输入列。
- `Terminology`：电影制作、摄影、制片和场记术语建议。
- `PDF Strings`：PDF、Canvas 和打印输出涉及的文案。
- `Do Not Translate 1-3`：品牌、协议、内部值、技术标识和示例内容。
- `Source Index`：源码命中位置，用于迁移时定位。

## 重新生成

先安装项目依赖：

```bash
npm ci
```

提取英文清单：

```bash
node scripts/build-localization-review.mjs
```

生成 Excel 审校表，需要 Python 3 和 `XlsxWriter`：

```bash
python3 -m pip install -r scripts/requirements-localization.txt
python3 scripts/build_localization_workbook.py
```

只生成小尺寸渲染检查文件：

```bash
python3 scripts/build_localization_workbook.py --preview
```

## 翻译与迁移规则

1. 先审校 `Terminology`，锁定高频术语，再批量处理页面文案。
2. 显示标签可以翻译；枚举值、持久化值、文件格式、CSV/Resolve 表头和第三方专名保持稳定。
3. 同一英文原文在不同页面表达不同含义时，使用不同稳定键。
4. 输入框、按钮、表格和固定宽度列优先使用简短译名，并按工作簿中的布局风险做截图回归。
5. 英文继续作为默认语言和缺失键的回退语言。
6. 中文界面与中文通告单是两个独立设置：界面跟随使用者，通告单语言属于项目数据。

## 已知阻塞

当前应用会把 PDF 不支持的 CJK 字符替换为 `?`，并使用未嵌入的 Helvetica/Courier
标准字体。因此中文 PDF 目前不可用。后续必须完成：

- 嵌入支持简体中文的合法字体文件；
- 保留 `sanitizePdfText` 对非 CJK 文本的稳定处理；
- 检查中文断行、分页、固定列宽和表格高度；
- 为 PDF 中文文本增加回归测试。

## 基线验证

- `npm run lint`：通过。
- `npm run build`：通过，仅有 Vite 大分块提示。
- `npm test`：238 / 239 个测试文件通过，2840 / 2841 个测试通过。
- 既有失败：`src/domain/__tests__/callSheetSun.test.ts:43`，柏林夏至与冬至的日落先后断言失败。此失败在本地化改动前已经存在，与本次文案提取无关。

本目录目前是审校阶段成果；它不表示界面或 PDF 已完成简体中文本地化。
