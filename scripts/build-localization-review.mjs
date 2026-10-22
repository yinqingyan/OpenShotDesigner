import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(scriptDir, '..');
const sourceDir = path.join(rootDir, 'src');
const outputDir = path.join(rootDir, 'localization', 'zh-CN');
const previewDir = path.join('/private/tmp', 'openshot-localization-previews');

const projectVersion = JSON.parse(await fs.readFile(path.join(rootDir, 'package.json'), 'utf8')).version;
const projectCommit = await fs
  .readFile(path.join(rootDir, '.git', 'HEAD'), 'utf8')
  .then(async (head) => {
    const ref = head.match(/^ref:\s*(.+)\s*$/)?.[1];
    return ref ? fs.readFile(path.join(rootDir, '.git', ref), 'utf8') : head;
  })
  .then((value) => value.trim())
  .catch(() => 'unknown');

const walk = async (directory) => {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(fullPath)));
    else files.push(fullPath);
  }
  return files;
};

const normalise = (text) =>
  text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const shortHash = (value) => createHash('sha1').update(value).digest('hex').slice(0, 12);

const lineOf = (sourceFile, node) => {
  const position = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
  return { line: position.line + 1, column: position.character + 1 };
};

const getCallName = (node) => {
  if (!ts.isCallExpression(node)) return '';
  if (ts.isIdentifier(node.expression)) return node.expression.text;
  if (ts.isPropertyAccessExpression(node.expression)) return node.expression.name.text;
  return '';
};

const getPropertyName = (node) =>
  ts.isPropertyAssignment(node) && (ts.isIdentifier(node.name) || ts.isStringLiteral(node.name))
    ? node.name.text
    : '';

const getJsxAttributeName = (node) => (ts.isJsxAttribute(node) && ts.isIdentifier(node.name) ? node.name.text : '');

const isTypeContext = (node) => {
  for (let current = node.parent; current; current = current.parent) {
    if (
      ts.isTypeNode(current) ||
      ts.isImportDeclaration(current) ||
      ts.isExportDeclaration(current) ||
      ts.isImportSpecifier(current) ||
      ts.isExportSpecifier(current)
    ) {
      return true;
    }
  }
  return false;
};

const isObjectKey = (node) => {
  const parent = node.parent;
  return (
    (ts.isPropertyAssignment(parent) && parent.name === node) ||
    (ts.isMethodDeclaration(parent) && parent.name === node) ||
    (ts.isPropertyDeclaration(parent) && parent.name === node)
  );
};

const isInternalError = (node) => {
  for (let current = node.parent; current; current = current.parent) {
    if (ts.isThrowStatement(current)) return true;
    if (ts.isNewExpression(current) && current.expression.getText().endsWith('Error')) return true;
    if (ts.isCallExpression(current) && ['console.error', 'console.warn'].includes(getCallName(current))) {
      return true;
    }
  }
  return false;
};

const userFacingContext = (node) => {
  if (ts.isJsxText(node)) return 'JSX 文本';

  const parent = node.parent;
  if (parent && ts.isJsxAttribute(parent)) {
    const name = getJsxAttributeName(parent);
    if (name) return `JSX 属性：${name}`;
  }
  if (parent && ts.isPropertyAssignment(parent)) {
    const name = getPropertyName(parent);
    if (['label', 'title', 'description', 'placeholder', 'message', 'help', 'emptyText', 'ariaLabel'].includes(name)) {
      return `对象属性：${name}`;
    }
  }
  if (parent && ts.isCallExpression(parent)) {
    const callName = getCallName(parent);
    if (
      [
        't',
        'documentText',
        'setNotice',
        'notify',
        'confirm',
        'prompt',
        'formatMessage',
        'setMessage',
        'setImportMessage',
        'setSaveNote',
        'setLiveError',
      ].includes(callName)
    ) {
      return `调用参数：${callName}`;
    }
  }

  for (let current = parent, depth = 0; current && depth < 4; current = current.parent, depth += 1) {
    if (ts.isJsxExpression(current)) return 'JSX 表达式';
    if (ts.isStatement(current) || ts.isSourceFile(current)) break;
  }
  return '';
};

const looksLikeTechnicalValue = (text) => {
  const value = text.trim();
  if (!value) return true;
  if (/^(?:https?:\/\/|mailto:|data:|blob:)/i.test(value)) return true;
  if (/^[./#/@][\w./#@-]+$/.test(value)) return true;
  if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)) return true;
  if (/^#[0-9a-f]{3,8}$/i.test(value)) return true;
  if (/^(?:application|image|audio|video|text)\/[\w.+-]+$/i.test(value)) return true;
  if (/^(?:[^\s]+\.(?:csv|tsv|json|txt|fountain|fdx|spmd|pdf|docx|celtx|html?|osd|zip|gdtf|mvr|png|jpe?g|webp))(?:[,;].*)?$/i.test(value)) {
    return true;
  }
  if (
    /(?:\.csv|\.json|request\.json|text\/csv|application\/json|application\/pdf|application\/zip|\.fountain|\.fdx)/i.test(
      value,
    ) &&
    /,|text\/|application\//.test(value)
  ) {
    return true;
  }
  if (/\b(?:const|let|var|function|return|await|async|new Promise|querySelector|querySelectorAll)\b/.test(value)) {
    return true;
  }
  if (/=>|;|\$\{[^}]*\?|\$\([^)]*\)/.test(value)) return true;
  if (/^[\w-]+:\s*[^:]+$/.test(value) && !/^[\w-]+\s+[A-Z]/.test(value)) return true;
  if (/^[A-Za-z_$][\w$]*=/.test(value)) return true;
  if (/^(?::scope|\[[^\]]+\]|#[\w-]+(?:\s|>)|\.(?:sel|query))/i.test(value)) return true;
  if (/^(?:"|'|`).*(?:"|'|`)$/.test(value) && /replace|join|slice|toUpperCase|toLowerCase/.test(value)) return true;
  if (/(?:monospace|sans-serif|serif)$/i.test(value)) return true;
  if (/^\.?[\w-]+\{[^}]+\}$/.test(value)) return true;
  if (/^[.!][\w-]*(?:\s|:|$)/.test(value) && value.length > 4) return true;
  if (/^--[\w-]+/.test(value)) return true;
  if (/^(?:\+|-)\.?\d/.test(value)) return true;
  if (/^\d+(?:\.\d+)?(?:px|pt|rem|em|vh|vw|ms|s|%|mm|cm|m|kg|g|lux|fc|k|w|v|a|hz|fps)?$/i.test(value)) {
    return true;
  }
  if (/^[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\(?\)?$/.test(value) && !userFacingContext({ parent: null })) {
    return true;
  }
  if (/[\\/][\w.-]+/.test(value) && /\.(?:[a-z0-9]{2,8})(?:[?#].*)?$/i.test(value)) {
    return true;
  }
  if (
    /(?:^|\s)(?:w|h|min-w|max-w|p[trblxy]?|m[trblxy]?|bg|text|border|rounded|flex|grid|gap|space)-/i.test(
      value,
    )
  ) {
    return true;
  }
  if (/^(?:true|false|null|undefined|NaN|Infinity)$/i.test(value)) return true;
  if (/^(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$/i.test(value)) return true;
  if (/^[A-Za-z][A-Za-z0-9]*::[A-Za-z0-9_:<>[\], ]+$/.test(value)) return true;
  return false;
};

const looksLikeNaturalLanguage = (text) => {
  if (text.length < 2 || text.length > 800) return false;
  if (!/[A-Za-z]/.test(text)) return false;
  if (looksLikeTechnicalValue(text)) return false;
  const words = text.match(/[A-Za-z][A-Za-z'’-]*/g) ?? [];
  if (words.length >= 2) return true;
  return /^[A-Z][A-Za-z'’-]{1,24}$/.test(text) || /^[A-Z0-9/&.+# -]{2,24}$/.test(text);
};

const formatModule = (relativeFile) => {
  const component = relativeFile.match(/^src\/components\/([^/]+)\//)?.[1];
  if (component) return `components/${component}`;
  const domain = relativeFile.match(/^src\/domain\/([^/]+)\//)?.[1];
  if (domain) return `domain/${domain}`;
  const utility = relativeFile.match(/^src\/utils\/([^/]+)\//)?.[1];
  if (utility) return `utils/${utility}`;
  const section = relativeFile.match(/^src\/([^/]+)\//)?.[1];
  return section ?? 'src';
};

const isPdfOrPrintSource = (relativeFile) =>
  relativeFile.includes('/pdf/') ||
  relativeFile.includes('/reports/') ||
  /Pdf\.(?:ts|tsx)$/.test(relativeFile) ||
  relativeFile.endsWith('/documentText.ts');

const isSampleSource = (relativeFile) =>
  /(?:sampleContent|sampleScout|sampleStoryboards)\.(?:ts|tsx)$/.test(relativeFile);

const denseTableModule = (relativeFile) =>
  /components\/(?:shotlist|equipment|schedule|budget|continuity|toolbar|contacts|reports)\//.test(relativeFile);

const layoutRiskFor = (text, relativeFile) => {
  const compact = text.replace(/\s+/g, ' ');
  const upperCase = /[A-Z]{4,}/.test(compact) && compact.length <= 32;
  if ((denseTableModule(relativeFile) && compact.length >= 18) || compact.length >= 48 || upperCase) {
    return '高';
  }
  if (compact.length >= 25 || /^[A-Z][A-Z0-9 /&.+#-]{3,}$/.test(compact)) return '中';
  return '低';
};

const placeholdersFor = (text) =>
  [...text.matchAll(/\$\{([^}]+)\}|{([A-Za-z][\w.[\]-]*)}/g)].map((match) => match[1] ?? match[2]).join(', ');

const spreadsheetSafe = (value) =>
  typeof value === 'string' && /^[=+\-@]/.test(value) ? `'${value}` : value;

const sourceFiles = (await walk(sourceDir))
  .filter((file) => /\.(?:ts|tsx)$/.test(file))
  .filter((file) => !file.endsWith('.d.ts'))
  .filter((file) => !file.includes('/__tests__/'))
  .filter((file) => !file.includes('/src/generated/'))
  .sort();

const occurrences = [];

for (const file of sourceFiles) {
  const relativeFile = path.relative(rootDir, file).split(path.sep).join('/');
  const sourceText = await fs.readFile(file, 'utf8');
  const sourceFile = ts.createSourceFile(
    file,
    sourceText,
    ts.ScriptTarget.Latest,
    true,
    file.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );

  const record = (node, rawText, syntaxKind) => {
    if (!rawText || isTypeContext(node) || isObjectKey(node)) return;
    const text = normalise(rawText);
    if (!looksLikeNaturalLanguage(text)) return;

    const context = userFacingContext(node);
    const propertyName =
      (ts.isPropertyAssignment(node.parent) && getPropertyName(node.parent)) ||
      (ts.isJsxAttribute(node.parent) && getJsxAttributeName(node.parent)) ||
      '';
    const callName = ts.isCallExpression(node.parent) ? getCallName(node.parent) : '';
    const position = lineOf(sourceFile, node);
    const sample = isSampleSource(relativeFile) || relativeFile === 'src/constants/presets.ts';
    const internalError = isInternalError(node);
    const naturalWords = text.match(/[A-Za-z][A-Za-z'’-]*/g)?.length ?? 0;
    const pdf = isPdfOrPrintSource(relativeFile);
    const uiModule =
      relativeFile.startsWith('src/components/') ||
      relativeFile.startsWith('src/i18n/') ||
      relativeFile === 'src/App.tsx' ||
      relativeFile === 'src/main.tsx' ||
      relativeFile.startsWith('src/context/');
    const configurationModule =
      relativeFile.startsWith('src/constants/') && relativeFile !== 'src/constants/presets.ts';
    const userMessageModule =
      pdf ||
      /^src\/domain\/(?:commands|people|readiness|reports|scheduling|usage|validation|workspace)\//.test(relativeFile);
    const sentenceLike = naturalWords >= 3 && text.length >= 16;
    const withoutPlaceholders = text.replace(/\$\{[\s\S]*?\}/g, ' ').replace(/[^\p{L}\p{N}\s'’-]/gu, ' ');
    const remainingWords = withoutPlaceholders.match(/[A-Za-z][A-Za-z'’-]*/g)?.length ?? 0;
    const templateIsMessage =
      syntaxKind !== 'template' ||
      context ||
      pdf ||
      (!/^[-.,:;·—+\s]/.test(text) &&
        remainingWords >= 1 &&
        !/\$\{[^}]*\}/.test(text.replaceAll(/\$\{[^}]*\}/g, '')));
    const translatable =
      !sample &&
      !internalError &&
      templateIsMessage &&
      (Boolean(context) ||
        (uiModule && naturalWords >= 2) ||
        (configurationModule && naturalWords >= 2 && naturalWords <= 8) ||
        (pdf && naturalWords >= 2) ||
        (userMessageModule && sentenceLike));
    const textType = pdf
      ? 'PDF/打印'
      : context.startsWith('JSX')
        ? '界面文案'
        : propertyName
          ? '对象标签'
          : '待分类';
    const layoutRisk = layoutRiskFor(text, relativeFile);
    let reason = '';
    if (!translatable) {
      if (sample) reason = '示例/剧本内容';
      else if (internalError) reason = '内部错误或日志';
      else if (!context && naturalWords < 2) reason = '技术标识或非完整文案';
      else reason = '不在可翻译界面文案范围内';
    }

    occurrences.push({
      source: text,
      key: `osd.${shortHash(text)}`,
      file: relativeFile,
      line: position.line,
      column: position.column,
      module: formatModule(relativeFile),
      textType,
      context: context || propertyName || callName || syntaxKind,
      syntaxKind,
      placeholders: placeholdersFor(text),
      pdf,
      translatable,
      layoutRisk,
      reason,
      note:
        pdf && layoutRisk === '高'
          ? 'PDF 需使用嵌入式中文字体，并检查断行、分页和固定列宽。'
          : layoutRisk === '高'
            ? '密集布局或大写/字距假设，迁移后需截图回归。'
            : '',
    });
  };

  const visit = (node) => {
    if (ts.isTemplateExpression(node)) {
      record(node, node.getText(sourceFile).slice(1, -1), 'template');
      return;
    }
    if (ts.isJsxText(node)) {
      record(node, node.getText(sourceFile), 'JSX text');
    } else if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
      record(node, node.text, ts.isJsxText(node.parent) ? 'JSX string' : 'string literal');
    }
    ts.forEachChild(node, visit);
  };

  visit(sourceFile);
}

const grouped = new Map();
for (const occurrence of occurrences) {
  const existing = grouped.get(occurrence.source);
  if (!existing) {
    grouped.set(occurrence.source, {
      source: occurrence.source,
      key: occurrence.key,
      occurrences: [occurrence],
    });
    continue;
  }
  existing.occurrences.push(occurrence);
}

const entries = [...grouped.values()]
  .map((group) => {
    const ordered = [...group.occurrences].sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line);
    const translatable = ordered.some((item) => item.translatable);
    const pdf = ordered.some((item) => item.pdf);
    const riskOrder = { 高: 3, 中: 2, 低: 1 };
    const layoutRisk = ordered.reduce(
      (highest, item) => (riskOrder[item.layoutRisk] > riskOrder[highest] ? item.layoutRisk : highest),
      '低',
    );
    return {
      id: `OSD-${shortHash(group.source).toUpperCase().slice(0, 8)}`,
      source: group.source,
      key: group.key,
      module: [...new Set(ordered.map((item) => item.module))].sort().join(', '),
      textType: [...new Set(ordered.map((item) => item.textType))].sort().join(', '),
      sourceRefs: ordered
        .slice(0, 8)
        .map((item) => `${item.file}:${item.line}`)
        .join('\n'),
      occurrenceCount: ordered.length,
      placeholders: [...new Set(ordered.map((item) => item.placeholders).filter(Boolean))].join(', '),
      pdf,
      translatable,
      layoutRisk,
      reason: ordered.find((item) => !item.translatable)?.reason ?? '',
      note: ordered.find((item) => item.note)?.note ?? '',
      occurrences: ordered,
    };
  })
  .sort((a, b) => Number(b.translatable) - Number(a.translatable) || a.source.localeCompare(b.source));

const uiEntries = entries.filter((entry) => entry.translatable);
const pdfEntries = uiEntries.filter((entry) => entry.pdf);
const doNotTranslateEntries = entries.filter((entry) => !entry.translatable);

const terminology = [
  ['Shot', '镜头', '摄影', '高', '基础摄影单位；与 Scene 区分。'],
  ['Scene', '场次', '编剧/场记', '高', '剧本中的叙事单位。'],
  ['Setup', '机位设置', '现场', '中', '需结合页面区分“灯光设置”与“机位设置”。'],
  ['Coverage', '镜头覆盖', '导演/场记', '中', '指用一组镜头完整覆盖场景。'],
  ['Lining', '镜位划线', '剧本拆解', '中', '剧本旁标示镜头覆盖范围的竖线。'],
  ['Lined script', '镜位标注剧本', '剧本拆解', '中', '比“划线剧本”更容易理解。'],
  ['Shot list', '镜头表', '导演组', '高', '固定表头中优先保持简短。'],
  ['Floor plan', '拍摄平面图', '导演组', '高', '与建筑 floor plan 区分。'],
  ['Blocking', '走位调度', '导演组', '中', '既指演员走位，也指现场调度。'],
  ['Storyboard', '故事板', '导演组', '高', '行业通用译名。'],
  ['Viewfinder', '取景器', '摄影', '高', '应用内模拟/实时取景界面。'],
  ['Focal length', '焦距', '摄影', '高', '不译为“焦段长度”。'],
  ['Aperture', '光圈', '摄影', '高', '数值单位常保留 f/。'],
  ['T-stop', 'T 档', '摄影', '中', '镜头通光等级；保留 T。'],
  ['Shutter angle', '快门角度', '摄影', '高', '常与快门速度并列显示。'],
  ['Sensor', '传感器', '摄影', '高', '相机传感器。'],
  ['Exposure', '曝光', '摄影', '高', '避免与 Exposure 报表混淆。'],
  ['White point', '白点', '摄影/调色', '中', '如页面实际表示白平衡，可在最终文案改为“白平衡”。'],
  ['Equipment manifest', '器材清单', '制片', '高', '固定表头优先使用“器材清单”。'],
  ['Call sheet', '通告单', '副导演组', '高', '中国大陆片场常用译名。'],
  ['Crew call', '剧组集合时间', '通告单', '高', '与 Cast call 分开。'],
  ['Wrap', '收工', '现场', '高', 'Planned wrap 为“计划收工”。'],
  ['Pickup', '补拍镜头', '现场', '中', '运输上下文中的 Pick-up 应译为“接送”。'],
  ['Stripboard', '拍摄计划板', '副导演组', '中', '保留其可视化色条概念。'],
  ['One-liner', '一行式拍摄计划', '副导演组', '中', '行业术语，可附英文。'],
  ['Day out of days', '演员按日工作安排', '副导演组', '中', '报表标题可保留 DOOD 缩写。'],
  ['Continuity', '场记', '场记组', '高', '页面语境指场记工作与连续性记录。'],
  ['Take', '条次', '场记', '高', 'Take 1 译“第 1 条”或保留栏名“条次”。'],
  ['Good take', '可用条次', '场记', '高', '与 NG 条次相对。'],
  ['Crew', '剧组', '制片', '高', '人员总称。'],
  ['Cast', '演员', '制片', '高', '演员组。'],
  ['Background', '背景演员', '制片', '中', '也可依地区使用“群演”。'],
  ['Gaffer', '灯光师', '灯光组', '高', '更准确为灯光组长；界面空间有限时用灯光师。'],
  ['Key grip', '灯光器材组长', '器械组', '中', '需按地区制作习惯复核。'],
  ['Sound mixer', '录音师', '声音组', '高', '现场录音负责人。'],
  ['1st AD', '第一副导演', '副导演组', '高', '保留职务层级。'],
  ['DP', '摄影指导', '摄影组', '高', '首次出现可采用“摄影指导（DP）”。'],
  ['Budget', '预算', '制片', '高', '基础财务术语。'],
  ['Rate', '费率', '制片', '高', '按天/周/整项计价时用“费率”。'],
  ['Day needs', '每日需求', '制片', '中', '页面中是每日人员与器材需求。'],
  ['Above the line', '线上成本', '预算', '高', '行业财务术语。'],
  ['Below the line', '线下成本', '预算', '高', '行业财务术语。'],
  ['VAT', '增值税', '预算', '高', '可保留 VAT 缩写。'],
  ['Locations', '拍摄地点', '制片', '高', '导航项可简化为“地点”。'],
  ['Task board', '任务看板', '制片', '高', '看板功能。'],
  ['Mood board', '情绪板', '美术/导演组', '高', '行业常用译名。'],
  ['Logistics', '运输与包装', '制片', '中', '根据页面实际内容复核是否仅指箱包物流。'],
  ['Rigging', '灯光吊挂', '灯光/器材', '中', '涵盖桁架、电机、悬挂负载。'],
  ['Power', '电力', '灯光/技术', '高', '技术规划页。'],
  ['Truss', '桁架', '灯光/器材', '高', '固定设备术语。'],
  ['Headroom', '负载余量', '电力', '中', '电力页面用“余量”，预算页面不可复用。'],
  ['Script supervisor', '场记', '场记组', '高', '职务名称。'],
  ['Slugline', '场景标题行', '编剧', '高', '剧本格式术语。'],
  ['Scene heading', '场景标题', '编剧', '高', '与 Slugline 可视上下文区分。'],
  ['Parenthetical', '表演提示', '编剧', '高', '对白中的括号提示。'],
  ['Sides', '拍摄单页', '演员/副导演', '中', '按演员或拍摄日拆出的剧本页。'],
  ['Breakdown', '剧本拆解', '制片', '高', '元素分析。'],
  ['Exhibit G', 'Exhibit G 表', '演员工时', '低', 'SAG-AFTRA 官方表单，优先保留原名。'],
].map(([source, suggestion, area, confidence, note]) => ({
  source,
  suggestion,
  area,
  confidence,
  status: '待审校',
  note,
}));

const manualDoNotTranslate = [
  ['Open Shot Designer', '品牌/产品名', '应用名称保持英文。'],
  ['DaVinci Resolve', '品牌/产品名', '第三方产品名。'],
  ['Final Draft', '品牌/产品名', '第三方产品名。'],
  ['OpenStreetMap', '品牌/产品名', '第三方平台名。'],
  ['Google Drive', '品牌/产品名', '第三方平台名。'],
  ['Nextcloud', '品牌/产品名', '第三方平台名。'],
  ['WebDAV', '协议/平台名', '协议名保持英文。'],
  ['Fountain', '格式/产品名', '剧本格式名保持英文。'],
  ['DMX', '行业缩写', '灯光控制协议缩写。'],
  ['ISO', '摄影参数', '参数缩写保持英文。'],
  ['FPS', '摄影参数', '帧率缩写保持英文。'],
  ['ND', '摄影参数', '中性密度滤镜缩写保持英文。'],
  ['INT.', '剧本格式标记', '保留国际剧本惯例；可在界面解释中说明。'],
  ['EXT.', '剧本格式标记', '保留国际剧本惯例。'],
  ['DAY', '剧本格式标记', '若属于场景标题行则保留；独立显示标签可另行翻译。'],
  ['NIGHT', '剧本格式标记', '若属于场景标题行则保留；独立显示标签可另行翻译。'],
  ['P/U', '行业缩写', '通告单中的接送缩写。'],
  ['DOOD', '行业缩写', 'Day out of days 的缩写。'],
  ['NG', '片场缩写', '不可用条次标记。'],
  ['A001C002', '技术标识', '素材文件名/编号示例。'],
];

const doNotRows = [
  ...doNotTranslateEntries.map((entry) => ({
    id: entry.id,
    source: entry.source,
    reason: entry.reason || '技术值或非界面文案',
    module: entry.module,
    refs: entry.sourceRefs,
    note: entry.note,
  })),
  ...manualDoNotTranslate
    .filter(([source]) => !doNotTranslateEntries.some((entry) => entry.source === source))
    .map(([source, reason, note], index) => ({
      id: `RULE-${String(index + 1).padStart(2, '0')}`,
      source,
      reason,
      module: '人工规则',
      refs: '',
      note,
    })),
];

const catalog = {
  metadata: {
    project: 'koosoli/OpenShotDesigner',
    version: projectVersion,
    commit: projectCommit,
    generatedAt: new Date().toISOString(),
    branch: 'codex/zh-cn-localization',
    extraction: 'TypeScript AST scan of src/**/*.ts and src/**/*.tsx, excluding tests and generated data',
    counts: {
      sourceFiles: sourceFiles.length,
      candidateOccurrences: occurrences.length,
      uniqueCandidates: entries.length,
      translatableUnique: uiEntries.length,
      pdfUnique: pdfEntries.length,
      doNotTranslateUnique: doNotTranslateEntries.length,
      manualDoNotTranslate: manualDoNotTranslate.length,
      terminology: terminology.length,
    },
  },
  terminology,
  entries,
  doNotTranslateRules: manualDoNotTranslate.map(([source, reason, note]) => ({ source, reason, note })),
};

const csvEscape = (value) => {
  const text = value == null ? '' : String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
};
const csv = [
  ['id', 'english_source', 'temporary_key', 'module', 'text_type', 'source_refs', 'pdf', 'translatable', 'zh_cn', 'status', 'layout_risk', 'note'],
  ...uiEntries.map((entry) => [
    entry.id,
    entry.source,
    entry.key,
    entry.module,
    entry.textType,
    entry.sourceRefs.replaceAll('\n', ' | '),
    entry.pdf ? 'Yes' : 'No',
    'Yes',
    '',
    '待翻译',
    entry.layoutRisk,
    entry.note,
  ]),
]
  .map((row) => row.map(csvEscape).join(','))
  .join('\n');

await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(path.join(outputDir, 'english-source-catalog.json'), `${JSON.stringify(catalog, null, 2)}\n`);
await fs.writeFile(path.join(outputDir, 'english-ui-review.csv'), `${csv}\n`);

if (process.env.BUILD_ARTIFACT_WORKBOOK !== '1') {
  console.log(JSON.stringify({ catalog: path.join(outputDir, 'english-source-catalog.json'), csv: path.join(outputDir, 'english-ui-review.csv'), counts: catalog.metadata.counts }, null, 2));
  process.exit(0);
}

const { SpreadsheetFile, Workbook } = await import('@oai/artifact-tool');
const workbook = Workbook.create();
const summary = workbook.worksheets.add('Summary');

summary.tabColor = '#243044';

const fontFamily = 'Helvetica Neue';
const bodyFont = { name: fontFamily, size: 10 };
const chunk = (values, size) =>
  Array.from({ length: Math.ceil(values.length / size) }, (_, index) => values.slice(index * size, (index + 1) * size));

const columnLetter = (number) => {
  let result = '';
  let value = number;
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
};

const addReviewSheet = ({ sheet, title, description, headers, rows, widths }) => {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${columnLetter(headers.length)}1`).values = [[title]];
  sheet.getRange(`A2:${columnLetter(headers.length)}2`).values = [[description]];
  sheet.getRange(`A4:${columnLetter(headers.length)}4`).values = [headers];
  if (rows.length > 0) {
    sheet
      .getRange(`A5:${columnLetter(headers.length)}${rows.length + 4}`)
      .values = rows.map((row) => row.map(spreadsheetSafe));
  }

  sheet.getRange('A1').format.font = { name: fontFamily, size: 16, bold: true, color: '#111827' };
  sheet.getRange('A2').format.font = { name: fontFamily, size: 10, italic: true, color: '#4B5563' };
  sheet.getRange(`A1:${columnLetter(headers.length)}1`).format.rowHeight = 26;
  sheet.getRange(`A2:${columnLetter(headers.length)}2`).format.rowHeight = 22;
  sheet.getRange(`A1:${columnLetter(headers.length)}${Math.max(rows.length + 4, 4)}`).format.font = bodyFont;
  sheet.getRange(`A4:${columnLetter(headers.length)}4`).format = {
    fill: '#243044',
    font: { name: fontFamily, size: 10, bold: true, color: '#FFFFFF' },
    horizontalAlignment: 'center',
    verticalAlignment: 'center',
    wrapText: true,
    rowHeight: 28,
  };

  widths.forEach((width, index) => {
    sheet.getRange(`${columnLetter(index + 1)}:${columnLetter(index + 1)}`).format.columnWidth = width;
  });

  if (rows.length > 0) {
    const dataRange = sheet.getRange(`A5:${columnLetter(headers.length)}${rows.length + 4}`);
    dataRange.format.verticalAlignment = 'center';
    dataRange.format.rowHeight = 22;
    dataRange.format.wrapText = true;
  }
  sheet.freezePanes.freezeRows(4);
};

const uiRows = uiEntries.map((entry) => [
  entry.id,
  entry.source,
  entry.key,
  entry.module,
  entry.textType,
  entry.sourceRefs,
  entry.placeholders,
  entry.pdf ? 'Yes' : 'No',
  'Yes',
  '',
  '待翻译',
  entry.layoutRisk,
  entry.note,
]).slice(0, Number(process.env.LOCALIZATION_UI_ROW_LIMIT ?? uiEntries.length));
const uiChunks = chunk(uiRows, 2000);
const uiSheets = uiChunks.map((rows, index) => {
  const suffix = uiChunks.length > 1 ? ` ${index + 1}` : '';
  const sheet = workbook.worksheets.add(`UI Strings${suffix}`);
  sheet.tabColor = '#2F5D7C';
  addReviewSheet({
    sheet,
    title: `Open Shot Designer 界面英文本地化清单${suffix}`,
    description: `按唯一英文原文归并；共 ${uiChunks.length} 个审校分表。中文译文列供逐项填写，审校后再迁移到正式 i18n 键。`,
    headers: [
      '编号',
      '英文原文',
      '临时键',
      '模块',
      '文本类型',
      '来源位置',
      '变量',
      'PDF/打印',
      '可翻译',
      '简体中文',
      '状态',
      '布局风险',
      '审校备注',
    ],
    rows,
    widths: [13, 52, 18, 22, 18, 42, 20, 11, 10, 44, 12, 10, 44],
    tableName: `UIStringsTable${index + 1}`,
  });
  sheet.freezePanes.freezeColumns(3);
  if (rows.length > 0) {
    sheet.getRange(`J5:J${rows.length + 4}`).format.fill = '#FFF3CD';
    sheet.getRange(`J5:J${rows.length + 4}`).format.font = { name: fontFamily, size: 10, color: '#111827' };
  }
  return sheet;
});

const terminologySheet = workbook.worksheets.add('Terminology');
terminologySheet.tabColor = '#4E6A43';
const termRows = terminology.map((term, index) => [
  index + 1,
  term.source,
  term.suggestion,
  term.area,
  term.confidence,
  term.status,
  term.note,
]);
addReviewSheet({
  sheet: terminologySheet,
  title: '电影制作与摄影术语建议',
  description: '这些译名用于保持界面一致；“建议译文”仍需结合具体页面语境审校。',
  headers: ['序号', '英文术语', '建议简体中文', '使用范围', '置信度', '状态', '说明'],
  rows: termRows,
  widths: [8, 28, 28, 22, 10, 12, 60],
  tableName: 'TerminologyTable',
});
terminologySheet.getRange(`C5:C${termRows.length + 4}`).format.fill = '#FFF3CD';

const pdfSheet = workbook.worksheets.add('PDF Strings');
pdfSheet.tabColor = '#6B4E71';
const pdfRows = pdfEntries.map((entry) => [
  entry.id,
  entry.source,
  entry.module,
  entry.sourceRefs,
  entry.placeholders,
  entry.layoutRisk,
  'Yes',
  '',
  '待翻译',
  entry.note || '需验证嵌入式中文字体、断行与分页。',
]).slice(0, Number(process.env.LOCALIZATION_PDF_ROW_LIMIT ?? pdfEntries.length));
addReviewSheet({
  sheet: pdfSheet,
  title: 'PDF 与打印文案',
  description: '这些文案进入 canvases/report/PDF 输出；中文 PDF 必须先替换仅支持 WinAnsi 的标准字体。',
  headers: ['编号', '英文原文', '模块', '来源位置', '变量', '布局风险', 'PDF/打印', '简体中文', '状态', '技术备注'],
  rows: pdfRows,
  widths: [13, 54, 22, 44, 20, 10, 11, 44, 12, 54],
  tableName: 'PDFStringsTable',
});
if (pdfRows.length > 0) {
  pdfSheet.getRange(`H5:H${pdfRows.length + 4}`).format.fill = '#FFF3CD';
}

const translatableOccurrences = uiEntries.flatMap((entry) => entry.occurrences);
const doNotRowsForSheet = doNotRows.map((entry, index) => [
  index + 1,
  entry.source,
  entry.reason,
  entry.module,
  entry.refs,
  entry.note,
]).slice(0, Number(process.env.LOCALIZATION_DO_NOT_LIMIT ?? doNotRows.length));
const doNotChunks = chunk(doNotRowsForSheet, 1000);
const doNotSheets = doNotChunks.map((rows, index) => {
  const suffix = doNotChunks.length > 1 ? ` ${index + 1}` : '';
  const sheet = workbook.worksheets.add(`Do Not Translate${suffix}`);
  sheet.tabColor = '#7A5C45';
  addReviewSheet({
    sheet,
    title: `不翻译项与保留项${suffix}`,
    description: '品牌、协议、文件格式、内部值和示例内容保持稳定；个别短标签可按上下文另建显示译文。',
    headers: ['序号', '英文原文', '原因', '模块/规则', '来源位置', '说明'],
    rows,
    widths: [8, 44, 28, 24, 48, 58],
    tableName: `DoNotTranslateTable${index + 1}`,
  });
  return sheet;
});

summary.showGridLines = false;
summary.getRange('A1:K1').format.font = bodyFont;
summary.getRange('A2').values = [['Open Shot Designer — 简体中文本地化审校']];
summary.getRange('A3').values = [['英文界面文本提取、领域术语与 PDF 风险清单']];
summary.getRange('A2').format.font = { name: fontFamily, size: 18, bold: true, color: '#111827' };
summary.getRange('A3').format.font = { name: fontFamily, size: 10, italic: true, color: '#4B5563' };
summary.getRange('A2:K2').format.rowHeight = 30;
summary.getRange('A3:K3').format.rowHeight = 22;

summary.getRange('A5:B8').values = [
  ['项目版本', `v${projectVersion}`],
  ['源码提交', projectCommit.slice(0, 12)],
  ['本地化分支', 'codex/zh-cn-localization'],
  ['提取方式', 'TypeScript AST'],
];
summary.getRange('D5:E8').values = [
  ['候选字符串', entries.length],
  ['可翻译唯一文案', uiEntries.length],
  ['PDF/打印文案', pdfEntries.length],
  ['术语建议', terminology.length],
];
summary.getRange('G5:H8').values = [
  ['源码命中', translatableOccurrences.length],
  ['来源文件', sourceFiles.length],
  ['不翻译项', doNotTranslateEntries.length],
  ['人工保留规则', manualDoNotTranslate.length],
];
summary.getRange('J5:K8').values = [
  ['英文文本', '已导出'],
  ['中文译文', '待审校'],
  ['PDF 中文支持', '尚未实现'],
  ['代码迁移', '尚未开始'],
];

for (const range of ['A5:A8', 'D5:D8', 'G5:G8', 'J5:J8']) {
  summary.getRange(range).format = {
    fill: '#E5E7EB',
    font: { name: fontFamily, size: 10, bold: true, color: '#374151' },
    verticalAlignment: 'center',
  };
}
for (const range of ['B5:B8', 'E5:E8', 'H5:H8', 'K5:K8']) {
  summary.getRange(range).format = {
    fill: '#F9FAFB',
    font: { name: fontFamily, size: 10, color: '#111827' },
    verticalAlignment: 'center',
    wrapText: true,
  };
}
summary.getRange('A5:K8').format.rowHeight = 26;
summary.getRange('A5:K8').format.borders = { preset: 'outside', style: 'thin', color: '#D1D5DB' };

summary.getRange('A11').values = [['执行顺序']];
summary.getRange('A11').format.font = { name: fontFamily, size: 12, bold: true, color: '#111827' };
summary.getRange('A12:A16').values = [
  ['1. 先审校“电影制作与摄影术语建议”，锁定高频术语。'],
  ['2. 在“UI Strings”中填写简体中文并更新状态。'],
  ['3. 优先处理“PDF Strings”，同时设计嵌入式中文字体与换行方案。'],
  ['4. 将同一原文的不同语义拆成独立稳定键，避免只按英文文本复用。'],
  ['5. 迁移后运行 lint、测试、构建，并逐页面截图回归。'],
];
summary.getRange('A12:A16').format = {
  font: { name: fontFamily, size: 10, color: '#374151' },
  wrapText: true,
  verticalAlignment: 'top',
  rowHeight: 30,
};
summary.getRange('A18').values = [['基线记录']];
summary.getRange('A18').format.font = { name: fontFamily, size: 12, bold: true, color: '#111827' };
summary.getRange('A19:A21').values = [
  ['lint：通过（TypeScript、ESLint、编码检查）。'],
  ['tests：238 / 239 个测试文件通过；2840 / 2841 个测试通过。既有失败位于 callSheetSun.test.ts。'],
  ['build：通过；Vite 仅提示大分块。'],
];
summary.getRange('A19:A21').format = {
  font: { name: fontFamily, size: 10, color: '#374151' },
  wrapText: true,
  verticalAlignment: 'top',
  rowHeight: 28,
};
summary.getRange('A23:K23').values = [
  [
    '注意：本表是本地化审校清单，不是已完成的中文版本；枚举值、持久化字段、CSV/Resolve 表头和第三方专名不能直接翻译。',
  ],
];
summary.getRange('A23:K23').format = {
  fill: '#FEF3C7',
  font: { name: fontFamily, size: 10, color: '#92400E' },
  wrapText: true,
  verticalAlignment: 'center',
  rowHeight: 36,
};
summary.getRange('A:A').format.columnWidth = 22;
summary.getRange('B:B').format.columnWidth = 20;
summary.getRange('C:C').format.columnWidth = 3;
summary.getRange('D:D').format.columnWidth = 20;
summary.getRange('E:E').format.columnWidth = 20;
summary.getRange('F:F').format.columnWidth = 3;
summary.getRange('G:G').format.columnWidth = 18;
summary.getRange('H:H').format.columnWidth = 18;
summary.getRange('I:I').format.columnWidth = 3;
summary.getRange('J:J').format.columnWidth = 18;
summary.getRange('K:K').format.columnWidth = 20;

workbook.recalculate();

const uiCheck = await workbook.inspect({
  kind: 'table',
  range: `UI Strings!A1:M${Math.min(uiRows.length + 4, 24)}`,
  include: 'values,formulas',
  tableMaxRows: 20,
  tableMaxCols: 13,
});
console.log(`UI inspect: ${uiCheck.ndjson.split('\n').length} record(s)`);

const errorScan = await workbook.inspect({
  kind: 'match',
  searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',
  options: { useRegex: true, maxResults: 100 },
  summary: 'final formula error scan',
});
if (errorScan.ndjson.trim() && !errorScan.ndjson.includes('"matches":[]')) {
  console.log(`Formula scan: ${errorScan.ndjson}`);
}

const workbookOutput = await SpreadsheetFile.exportXlsx(workbook);
const workbookPath = path.join(outputDir, 'OpenShotDesigner-zh-CN-review.xlsx');
await workbookOutput.save(workbookPath);

if (process.env.SKIP_WORKBOOK_RENDER !== '1') {
  try {
    const previewTargets = [
      ['Summary', 'A1:K24'],
      ...uiSheets.map((sheet) => [sheet.name, 'A1:M24']),
      ['Terminology', 'A1:G24'],
      ['PDF Strings', 'A1:J24'],
      ...doNotSheets.map((sheet) => [sheet.name, 'A1:F24']),
    ];
    for (const [sheetName, range] of previewTargets) {
      const preview = await workbook.render({ sheetName, range, scale: 1.25, format: 'png' });
      const filename = `${sheetName.toLowerCase().replaceAll(/[^a-z]+/g, '-')}.png`;
      await fs.writeFile(path.join(previewDir, filename), new Uint8Array(await preview.arrayBuffer()));
    }
  } catch (error) {
    console.warn(`Workbook render skipped after runtime error: ${error instanceof Error ? error.message : error}`);
  }
}

console.log(
  JSON.stringify(
    {
      workbook: workbookPath,
      catalog: path.join(outputDir, 'english-source-catalog.json'),
      csv: path.join(outputDir, 'english-ui-review.csv'),
      counts: catalog.metadata.counts,
      previewDir,
    },
    null,
    2,
  ),
);
