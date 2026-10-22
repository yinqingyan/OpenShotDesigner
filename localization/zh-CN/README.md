# Open Shot Designer 简体中文本地化

本目录保存简体中文本地化的英文来源清单、审校表和实施记录。

## 当前基线

- 上游项目：`koosoli/OpenShotDesigner`
- 上游版本：`v1.4.2`
- 基线提交：`766a80df36a8c8cde3b14cbd482ce0e298adbd04`
- 工作分支：`codex/zh-cn-localization`
- 提取范围：`src/**/*.ts` 和 `src/**/*.tsx`，排除测试与 `src/generated`
- 提取方式：TypeScript AST
- 当前阶段：专业初译和逐条确认流程已建立，所有条目（含保留英文项）默认等待人工确认
- 界面状态：已接入 `zh-CN` 语言选项和 87 条顶部导航、项目页及 chrome 文案；完整业务界面的合成要等全部审校项确认

本次扫描结果：

| 项目 | 数量 |
| --- | ---: |
| 生产源码文件 | 524 |
| 候选源码命中 | 9,440 |
| 按英文原文归并后的候选 | 7,611 |
| 需要人工判断的候选文案 | 4,985 |
| 涉及 PDF/打印的候选文案 | 776 |
| 不翻译项 | 2,626 |
| 专业术语初译 | 386 |
| 界面与打印审校项 | 4,985 |
| 已初译、待确认 | 3,988 |
| 安全保留英文、待确认 | 997 |
| 本地审校队列 | 5,371 |

`4,985` 是提取规则筛选出的候选审校文案，并非完成翻译后的精确替换点。同一句原文
可能出现在不同语义中，正式实施时需要按上下文拆成独立、稳定的 i18n 键。长句先用
公开翻译服务生成通顺初稿，再按项目术语表校正；短标签、编程字符串、品牌和技术值
由本地规则处理。初译没有人工确认的条目一律不能进入合成。

## 文件

- `english-source-catalog.json`：完整机器可读清单，保留源码位置、上下文、变量、布局风险和保留原因。
- `english-ui-review.csv`：原始界面英文候选清单，由 AST 提取器生成。
- `zh-cn-terminology.json`：电影制作、摄影、灯光、电力、制片、场记和程序界面术语初译。
- `zh-cn-drafts.json`：4,985 个界面/打印候选的专业初译、处置、置信度和语境依据。
- `zh-CN-review.html`：自包含的逐条确认工具，支持编辑、确认、需修改和自动保存；全部确认后才允许导出确认清单。
- `OpenShotDesigner-zh-CN-review.xlsx`：供人工筛选和留痕的完整审校工作簿。

工作簿包含：

- `Summary`：版本、计数、执行顺序与基线结果。
- `Review Workflow`：初译、确认、门禁和合成步骤。
- `UI Strings 1-3`：英文原文、专业初译、核对后中文、置信度、状态和语境依据。
- `Terminology`：386 条专业术语初译与核对列。
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
python3 scripts/build_zh_cn_drafts.py
python3 scripts/build_zh_cn_terminology.py
python3 scripts/build_zh_cn_review_app.py
python3 scripts/build_localization_workbook.py
```

`scripts/translate_zh_cn_drafts.py` 只用于重新生成长句初稿；它会调用公开翻译服务，
需要网络，不应在人工修改完成后的清单上直接运行。

只生成小尺寸渲染检查文件：

```bash
python3 scripts/build_localization_workbook.py --preview
```

## 确认与合成流程

1. 打开 `zh-CN-review.html`，先确认 386 条专业术语，再逐条检查界面与打印文案。
2. 正确时点击“确认并下一项”；需要调整时修改译文并点击“需修改”，补充修改说明。
3. 品牌、枚举、协议、代码和技术值保持英文；这些条目也必须点击“确认保留并下一项”。
4. 浏览器会自动保存进度。全部“待确认”和“需修改”清零后，“进入合成”才会解锁。
5. 点击“进入合成”会导出 `zh-cn-confirmed.json`；只有这个确认清单可以作为代码合成输入。
6. 在合成阶段建立稳定 i18n 键，保持枚举、持久化值和 CSV/Resolve 表头不变，然后运行 lint、测试、构建和逐页截图回归。

## 翻译规则

1. `Shot` 使用“镜头”，`Scene` 使用“场次”，`Setup` 依语境使用“机位设置”。
2. `Take` 使用“条次”，`Good take` 使用“可用条次”，`Coverage` 使用“镜头覆盖”。
3. `Crew call` 使用“剧组集合时间”，`Cast call` 使用“演员集合时间”，`Call sheet` 使用“通告单”。
4. `Pickup` 在补拍语境使用“补拍镜头”，在运输语境使用“接送”。
5. 变量、快捷键、文件格式和 `ISO`、`FPS`、`ND`、`DMX`、`T-stop` 等专业符号保持稳定。
6. 英文继续作为默认语言和缺失键的回退语言；中文界面与中文通告单仍是两个独立设置。

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

本目录目前是“专业初译、等待逐条确认”的成果；它不是已确认或已完成的中文版本，
也没有进入代码合成。中文 PDF 仍需在确认完成后单独解决字体嵌入、断行和分页。
