#!/usr/bin/env python3
"""Create traceable Simplified Chinese first-pass drafts from the AST catalog.

The output is intentionally reviewable rather than presented as finished
localization. Exact UI strings and domain phrases are translated first. Longer
sentences receive a glossary-assisted draft and a lower confidence value so a
Chinese-speaking film professional can focus review on uncertain wording.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOCALIZATION = ROOT / "localization" / "zh-CN"
CATALOG = LOCALIZATION / "english-source-catalog.json"
DICTIONARY = ROOT / "src" / "i18n" / "dictionary.ts"
OUTPUT = LOCALIZATION / "zh-cn-drafts.json"


def normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def sentence_key(value: str) -> str:
    value = normalise(value).lower()
    value = re.sub(r"^[^\w]+|[^\w]+$", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


@lru_cache(maxsize=1)
def parse_dictionary() -> dict[str, str]:
    """Use the translations already implemented in the application."""
    source = DICTIONARY.read_text(encoding="utf-8")

    def parse_block(name: str) -> dict[str, str]:
        match = re.search(
            rf"const {name}(?::\s*Record<I18nKey,\s*string>)?\s*=\s*\{{(.*?)\n\}}(?:\s+as\s+const)?;",
            source,
            flags=re.S,
        )
        if not match:
            raise ValueError(f"Could not find {name} dictionary block")
        entries: dict[str, str] = {}
        for key, value in re.findall(r"^\s*'([^']+)':\s*'((?:\\'|[^'])*)',\s*$", match.group(1), re.M):
            entries[key] = value.replace("\\'", "'")
        return entries

    english = parse_block("en")
    chinese = parse_block("zhCN")
    return {
        normalise(source_text): chinese[key]
        for key, source_text in english.items()
        if key in chinese
    }


# Short application labels and frequent actions. These are deliberately explicit:
# changing terminology changes the language of the whole interface, so each
# high-confidence label remains easy to review in one place.
EXACT_OVERRIDES: dict[str, str] = {
    "Active": "有效",
    "Add": "添加",
    "Add a camera": "添加摄影机",
    "Add a light": "添加灯光",
    "Add a power source": "添加电源",
    "Add a source first": "请先添加电源",
    "Add circuit": "添加回路",
    "Add consumer": "添加用电设备",
    "Add gear": "添加器材",
    "Add item": "添加项目",
    "Add light": "添加灯光",
    "Add power source": "添加电源",
    "Add prop": "添加道具",
    "Add row": "添加行",
    "Add Shot": "添加镜头",
    "Add unplanned shot": "添加计划外镜头",
    "All": "全部",
    "All projects": "所有项目",
    "Apply": "应用",
    "Apply to": "应用于",
    "@DP — 50mm instead?": "摄影指导（DP）— 改用 50mm？",
    "Archive": "归档",
    "Area": "面积",
    "Aspect ratio": "画幅比例",
    "Attach": "附加",
    "Attach photo": "附加照片",
    "Audio": "音频",
    "Back": "返回",
    "Back to the workspace": "返回工作区",
    "Blank": "留空",
    "Block": "阻挡",
    "Board": "看板",
    "Board name": "看板名称",
    "Brand": "品牌",
    "Budget": "预算",
    "Call sheet": "通告单",
    "Call sheets": "通告单",
    "Call time": "集合时间",
    "Camera": "摄影机",
    "Camera Aperture": "摄影机光圈",
    "Camera angle": "摄影机角度",
    "Camera Height": "摄影机高度",
    "Camera movement": "摄影机运动",
    "Camera Notes": "摄影机备注",
    "Camera Type": "摄影机类型",
    "CAMERA ANGLE": "摄影机角度",
    "Cancel": "取消",
    "Cast": "演员",
    "Category": "类别",
    "Character": "角色",
    "Choose": "选择",
    "Circuit": "回路",
    "Clear": "清除",
    "Close": "关闭",
    "Close Viewfinder": "关闭取景器",
    "Color": "颜色",
    "Complete": "完成",
    "Configure": "配置",
    "Contacts": "联系人",
    "Continuity": "场记",
    "Continuity log": "场记记录",
    "Copy": "复制",
    "Coverage": "镜头覆盖",
    "Create": "创建",
    "Create project": "创建项目",
    "Crew": "剧组",
    "Crew call": "剧组集合时间",
    "Cue": "提示点",
    "Current": "当前",
    "Custom": "自定义",
    "Date": "日期",
    "Date Recorded": "记录日期",
    "Day": "日",
    "Day / Night": "日/夜",
    "Delete": "删除",
    "Delete board?": "删除看板？",
    "Delete item": "删除项目",
    "Delete project": "删除项目",
    "Delete Shot": "删除镜头",
    "Department": "部门",
    "Department heads": "部门负责人",
    "Description": "说明",
    "Details": "详情",
    "Director": "导演",
    "Director of Photography": "摄影指导",
    "Dismiss": "关闭",
    "Distance": "距离",
    "Download": "下载",
    "Draft": "草稿",
    "Drag to move": "拖动以移动",
    "Duplicate": "复制",
    "Duplicate item": "复制项目",
    "Edit": "编辑",
    "Edit item": "编辑项目",
    "Element": "元素",
    "Element name": "元素名称",
    "Empty": "空",
    "End": "结束",
    "Equipment": "器材",
    "Equipment manifest": "器材清单",
    "Estimated": "估算",
    "Export": "导出",
    "Export & Print Studio": "导出与打印工作室",
    "File Name": "文件名",
    "Filter": "筛选",
    "First meal": "第一餐",
    "Floor plan": "拍摄平面图",
    "Focal length": "焦距",
    "Focal Point (mm)": "焦点（mm）",
    "Gear": "器材",
    "General": "常规",
    "General notes": "常规备注",
    "Good take": "可用条次",
    "Grid units": "网格单位",
    "Group": "组",
    "Help": "帮助",
    "Hide": "隐藏",
    "Hour": "小时",
    "Image": "图像",
    "Import": "导入",
    "In progress": "进行中",
    "Include": "包含",
    "Item": "项目",
    "Item name": "项目名称",
    "Keyboard shortcuts": "键盘快捷键",
    "Label": "标签",
    "Light": "灯光",
    "Lighting": "灯光",
    "Line": "行",
    "Locations": "拍摄地点",
    "Lock": "锁定",
    "Locked": "已锁定",
    "Logistics": "运输与包装",
    "Logo": "标志",
    "Make-up": "化妆",
    "Map": "地图",
    "Mark": "标记",
    "Medium": "中等",
    "Model": "型号",
    "Module": "模块",
    "Mood board": "情绪板",
    "More": "更多",
    "More controls": "更多控件",
    "Move": "移动",
    "Name": "名称",
    "New": "新建",
    "New project": "新建项目",
    "Nearest hospital": "最近医院",
    "Next": "下一步",
    "No": "否",
    "No Camera": "无摄影机",
    "No crew listed.": "尚未列出剧组人员。",
    "No equipment": "无器材",
    "No items": "无项目",
    "No light": "无灯光",
    "No lighting": "无灯光",
    "No location": "无地点",
    "No output": "无输出",
    "No props": "无道具",
    "No scene": "无场次",
    "No shot": "无镜头",
    "No storyboard": "无故事板",
    "None": "无",
    "Note": "备注",
    "Notes": "备注",
    "Not attached": "未附加",
    "Not counted": "未计入",
    "Not judged": "未判定",
    "Not marked": "未标记",
    "Not set": "未设置",
    "Not shot": "未拍摄",
    "Off": "关闭",
    "On": "开启",
    "On set": "在片场",
    "Open": "打开",
    "Open floor plan": "打开拍摄平面图",
    "Open viewfinder": "打开取景器",
    "Options": "选项",
    "Other": "其他",
    "Owner": "负责人",
    "Page": "页",
    "Panel": "面板",
    "Peak concurrent": "并发峰值",
    "People": "人员",
    "Photo": "照片",
    "Planned wrap": "计划收工",
    "Power": "电力",
    "Prepared by": "制表人",
    "Previous": "上一步",
    "Print": "打印",
    "Production": "制作",
    "Production company": "制作公司",
    "Production logo": "制作公司标志",
    "Profile": "配置",
    "Project": "项目",
    "Project title": "项目名称",
    "Props": "道具",
    "Quantity": "数量",
    "Rate": "费率",
    "Remove": "移除",
    "Remove row": "移除行",
    "Rename": "重命名",
    "Reset": "重置",
    "Restore": "恢复",
    "Return": "返回",
    "Role": "职务",
    "Role / Function": "职务/职能",
    "Run of Show": "节目流程单",
    "Safety bulletin": "安全通告",
    "Save": "保存",
    "Save project file": "保存项目文件",
    "Scene": "场次",
    "Scene Heading": "场景标题",
    "Scene numbers": "场次编号",
    "Schedule": "计划",
    "Script": "剧本",
    "Script Supervisor": "场记",
    "Search": "搜索",
    "Select": "选择",
    "Settings": "设置",
    "Setup": "机位设置",
    "Shoot days": "拍摄天数",
    "Shooting day": "拍摄日",
    "Shooting schedule": "拍摄计划",
    "Shot": "镜头",
    "Shot list": "镜头表",
    "Shot name": "镜头名称",
    "Shot size": "景别",
    "Show": "显示",
    "Show all": "全部显示",
    "Size": "尺寸",
    "Source": "来源",
    "Status": "状态",
    "Storyboard": "故事板",
    "Solar noon": "太阳正午",
    "Sunrise": "日出",
    "Sunset": "日落",
    "Take": "条次",
    "Tasks": "任务",
    "Time": "时间",
    "Title": "标题",
    "To do": "待办",
    "Total": "总计",
    "Total run time": "总运行时长",
    "Type": "类型",
    "Unit base": "剧组停车点",
    "Unknown": "未知",
    "Unknown profile": "未知配置",
    "Unlock": "解锁",
    "Untitled item": "未命名项目",
    "Untitled production": "未命名制作",
    "Upload": "上传",
    "Video": "视频",
    "Viewfinder": "取景器",
    "View": "视图",
    "Walkie channels": "对讲频道",
    "Weight": "重量",
    "Where it is": "位置",
    "Wild track": "独立音轨",
    "Works offline.": "可离线使用。",
    "Yes": "是",
    "Zoom in": "放大",
    "Zoom out": "缩小",
}


# Longer phrases are replaced before individual terms. Keeping phrase order
# explicit prevents "shooting day" becoming "拍摄日", "call sheet" becoming a
# literal "呼叫表", or "power source" becoming "力量来源".
PHRASE_TRANSLATIONS: dict[str, str] = {
    "-- Custom / Generic Cinema Camera --": "-- 自定义/通用电影摄影机 --",
    "-- Custom Brand --": "-- 自定义品牌 --",
    "-- Custom Model --": "-- 自定义型号 --",
    "-- Select Camera Accessory Preset --": "-- 选择摄影机配件预设 --",
    "-- Standalone Item (Not in package) --": "-- 独立项目（不属于器材包）--",
    "— Kit Accessories Manifest": "— 摄影机套装配件清单",
    "— no catalogue fixture": "— 目录中没有对应灯具",
    "— no weight": "— 无重量",
    "— none (label only) —": "— 无（仅标签）—",
    "— none (top level) —": "— 无（顶层）—",
    "— not counted": "— 未计入",
    "— not printed until the box above is ticked": "— 勾选上方选项后才打印",
    "— barn doors / framing shutters that cut spill at the fixture face.": (
        "— 四叶挡板/遮光叶片，用于在灯具出光面裁切溢光。"
    ),
    "— blocks / removes light (negative fill).": "— 遮挡或移除光线（负补光）。",
    "— reduces intensity in a wash without changing color or softness.": (
        "— 在泛光照明中降低强度，同时不改变色温或柔光程度。"
    ),
    "— shapes light with a long blade (kicks, forehead shadows).": (
        "— 用长遮光叶片控制光线形状（压暗轮廓高光、额头阴影）。"
    ),
    "— softens & diffuses the light passing through it.": "— 对穿过的光线进行柔化和扩散。",
    "— throws a dappled, broken-up shadow pattern through cut-outs.": (
        "— 通过镂空图案投射斑驳、破碎的阴影。"
    ),
    "— resolve before show time.": "— 请在拍摄开始前解决。",
    "(${reachM}m moving)": "（移动范围 ${reachM}m）",
    "1st Assistant Director": "第一副导演",
    "2nd Assistant Director": "第二副导演",
    "Above the line": "线上成本",
    "Add a separate unplanned shot": "添加一条单独的计划外镜头",
    "Add to first shooting day": "添加至第一个拍摄日",
    "Add unplanned shot at end of scene": "在场次末尾添加计划外镜头",
    "Ambient light": "环境光",
    "Average shot length": "平均镜头时长",
    "Below the line": "线下成本",
    "Best boy": "灯光副组长",
    "Birds-eye": "俯视",
    "Bird's eye": "俯视",
    "Bounce light": "反射光",
    "Broadcast & Production": "广电与制作",
    "Camera FPS": "摄影机帧率",
    "Camera movement": "摄影机运动",
    "Camera Power": "摄影机供电",
    "Camera Rig": "摄影机组件",
    "Cable allowance": "电缆余量",
    "Cable Cam": "索道摄影机",
    "Cable Run": "线缆路由",
    "Call sheet type": "通告单类型",
    "Cast contact visibility": "演员联系方式可见性",
    "Cinema Camera": "电影摄影机",
    "Color temperature": "色温",
    "Continuity conflicts": "场记连续性冲突",
    "Continuity photo": "场记照片",
    "Core Scene Elements": "核心场景元素",
    "Crew call": "剧组集合时间",
    "Crew, cast & contacts": "剧组、演员与联系人",
    "Day out of days": "演员按日工作安排",
    "Decrease quantity": "减少数量",
    "Department catalog": "部门目录",
    "Distro zone": "配电区域",
    "Dutch angle": "荷兰倾斜角",
    "Equipment manifest": "器材清单",
    "First shooting day": "第一个拍摄日",
    "Floor plan": "拍摄平面图",
    "Focal Point": "焦点",
    "Gear movement": "器材运输",
    "Good take": "可用条次",
    "Grass Valley": "Grass Valley",
    "Hotel Astoria": "Hotel Astoria",
    "Increase quantity": "增加数量",
    "Key grip": "灯光器材组长",
    "Lined script": "镜位标注剧本",
    "Live shot tracker": "现场镜头跟踪表",
    "Low angle": "低角度",
    "Main menu": "主菜单",
    "Make-up": "化妆",
    "Mood board": "情绪板",
    "No shooting days yet": "尚无拍摄日",
    "Not covered": "未覆盖",
    "Nothing packed in here yet.": "尚未装入任何物品。",
    "DOP ${crew('cinematographer')}": "摄影指导 ${crew('cinematographer')}",
    "On set": "在片场",
    "One-liner": "一行式拍摄计划",
    "Overhead / Bird's Eye": "俯拍/鸟瞰",
    "Planned wrap": "计划收工",
    "Power source": "电源",
    "Production company": "制作公司",
    "Production logo": "制作公司标志",
    "Return to unscheduled": "移回未排期",
    "Run of Show": "节目流程单",
    "Safety bulletin": "安全通告",
    "Script supervisor": "场记",
    "Sensor format": "传感器画幅",
    "Shooting day": "拍摄日",
    "Shooting schedule": "拍摄计划",
    "Shot list": "镜头表",
    "Shot name": "镜头名称",
    "Shot number": "镜号",
    "Shot size": "景别",
    "Shutter angle": "快门角度",
    "Shutter speed": "快门速度",
    "Signal flow": "信号流",
    "Sound mixer": "录音师",
    "Studio & Stage": "演播室与舞台",
    "Studio & Grip": "演播室与器械",
    "What ${subjectNameOf(note, characters)} looked like": "${subjectNameOf(note, characters)} 当时的样貌",
    "Studio & Grip": "演播室与器械",
    "Super-reduced": "超低预算",
    "Truss self-weight": "桁架自重",
    "Unit base": "剧组停车点",
    "Walkie channels": "对讲频道",
    "White Point": "白点",
    "Wild track": "独立音轨",
    "Workspace preset": "工作区预设",
}


GLOSSARY: dict[str, str] = {
    "above-the-line": "线上成本",
    "actor": "演员",
    "actress": "女演员",
    "address": "地址",
    "aircraft": "飞行器",
    "amount": "金额",
    "aperture": "光圈",
    "archive": "归档",
    "assembly": "组合",
    "assistant": "助理",
    "assignee": "负责人",
    "atmosphere": "氛围",
    "audio": "音频",
    "auteur": "作者导演",
    "background": "背景演员",
    "backup": "备份",
    "barn doors": "四叶挡板",
    "battery": "电池",
    "batteries": "电池",
    "beam": "光束",
    "below-the-line": "线下成本",
    "blocking": "走位调度",
    "blue": "蓝色",
    "board": "看板",
    "brand": "品牌",
    "breakdown": "剧本拆解",
    "brief": "简报",
    "budget": "预算",
    "cable": "电缆",
    "call": "集合",
    "camera": "摄影机",
    "can": "可以",
    "candidate": "候选",
    "capacity": "容量",
    "cards": "存储卡",
    "cast": "演员",
    "category": "类别",
    "center": "中心",
    "centre": "中心",
    "channels": "通道",
    "character": "角色",
    "check": "检查",
    "check-in": "签到",
    "check-out": "签退",
    "circuit": "回路",
    "click": "点击",
    "client": "客户",
    "close": "关闭",
    "code": "代码",
    "color": "颜色",
    "colour": "颜色",
    "column": "列",
    "company": "公司",
    "complete": "完成",
    "conflict": "冲突",
    "consumer": "用电设备",
    "contact": "联系人",
    "container": "容器",
    "continuity": "场记",
    "cost": "成本",
    "coverage": "镜头覆盖",
    "crew": "剧组",
    "cue": "提示点",
    "currency": "币种",
    "current": "当前",
    "custom": "自定义",
    "cut": "切",
    "data": "数据",
    "date": "日期",
    "day": "日",
    "decrease": "减少",
    "delete": "删除",
    "department": "部门",
    "description": "说明",
    "destination": "目的地",
    "detail": "详情",
    "details": "详情",
    "dialogue": "对白",
    "diffusion": "柔光",
    "dim": "调光",
    "director": "导演",
    "distance": "距离",
    "dolly": "移动车",
    "download": "下载",
    "draft": "草稿",
    "drag": "拖动",
    "duplicate": "复制",
    "edit": "编辑",
    "electric": "电气",
    "element": "元素",
    "elements": "元素",
    "empty": "空",
    "end": "结束",
    "equipment": "器材",
    "estimate": "估算",
    "event": "事件",
    "exposure": "曝光",
    "export": "导出",
    "field": "字段",
    "file": "文件",
    "fill": "填充",
    "filter": "滤镜",
    "first": "第一",
    "fixture": "灯具",
    "fixtures": "灯具",
    "flag": "遮光板",
    "focal": "焦点",
    "frame": "画幅",
    "frames": "帧",
    "free": "可用",
    "gear": "器材",
    "generator": "发电机",
    "green": "绿色",
    "group": "组",
    "hair": "发型",
    "headroom": "余量",
    "height": "高度",
    "hold": "预留",
    "hour": "小时",
    "house": "现场建筑",
    "image": "图像",
    "images": "图像",
    "import": "导入",
    "intensity": "强度",
    "item": "项目",
    "items": "项目",
    "label": "标签",
    "length": "长度",
    "light": "灯光",
    "lighting": "灯光",
    "line": "行",
    "lines": "行",
    "load": "负载",
    "loads": "负载",
    "location": "地点",
    "locations": "地点",
    "lock": "锁定",
    "locked": "锁定",
    "logo": "标志",
    "manufacturer": "制造商",
    "map": "地图",
    "mark": "标记",
    "meal": "用餐",
    "media": "媒体",
    "minutes": "分钟",
    "minute": "分钟",
    "model": "型号",
    "modifier": "控光附件",
    "money": "金额",
    "month": "月",
    "more": "更多",
    "motor": "电机",
    "move": "移动",
    "movement": "运动",
    "name": "名称",
    "nearest": "最近的",
    "net": "减光网",
    "new": "新建",
    "next": "下一步",
    "note": "备注",
    "notes": "备注",
    "number": "编号",
    "opacity": "不透明度",
    "open": "打开",
    "package": "器材包",
    "page": "页",
    "pages": "页",
    "panel": "面板",
    "path": "路径",
    "people": "人员",
    "performer": "演员",
    "person": "人员",
    "phase": "相",
    "photo": "照片",
    "plan": "方案",
    "planned": "计划的",
    "power": "电力",
    "prepared": "已准备",
    "print": "打印",
    "production": "制作",
    "profile": "配置",
    "project": "项目",
    "prop": "道具",
    "properties": "属性",
    "quantity": "数量",
    "rate": "费率",
    "receipt": "收据",
    "red": "红色",
    "remove": "移除",
    "report": "报告",
    "reports": "报告",
    "revision": "修订",
    "rig": "器材组",
    "rigging": "灯光吊挂",
    "role": "职务",
    "room": "房间",
    "rotation": "旋转",
    "run": "运行",
    "safety": "安全",
    "save": "保存",
    "scene": "场次",
    "scenes": "场次",
    "schedule": "计划",
    "scheduled": "已排期",
    "screenplay": "剧本",
    "script": "剧本",
    "search": "搜索",
    "sensor": "传感器",
    "set": "设置",
    "setup": "机位设置",
    "sheet": "表",
    "shoot": "拍摄",
    "shooting": "拍摄",
    "shot": "镜头",
    "shots": "镜头",
    "show": "显示",
    "side": "侧",
    "signal": "信号",
    "size": "尺寸",
    "source": "来源",
    "specification": "规格",
    "specifications": "规格",
    "specs": "规格",
    "start": "开始",
    "status": "状态",
    "storyboard": "故事板",
    "street": "街道",
    "subject": "主体",
    "supply": "供电",
    "suspended": "悬吊",
    "sync": "同步",
    "tag": "标签",
    "take": "条次",
    "takes": "条次",
    "task": "任务",
    "technical": "技术",
    "time": "时间",
    "title": "名称",
    "today": "今天",
    "total": "总计",
    "track": "轨道",
    "truck": "器材车",
    "truss": "桁架",
    "type": "类型",
    "unit": "单位",
    "unknown": "未知",
    "value": "值",
    "variant": "变体",
    "video": "视频",
    "view": "视图",
    "volume": "体积",
    "wardrobe": "服装",
    "watts": "瓦",
    "weight": "重量",
    "welcome": "欢迎",
    "white": "白色",
    "width": "宽度",
    "with": "带有",
    "without": "不含",
    "wrap": "收工",
    "yellow": "黄色",
    "zone": "区域",
}


FUNCTION_WORDS: dict[str, str] = {
    "a": "",
    "an": "",
    "and": "和",
    "are": "",
    "as": "为",
    "at": "位于",
    "before": "之前",
    "by": "由",
    "each": "每",
    "every": "每个",
    "for": "",
    "from": "从",
    "has": "有",
    "in": "在",
    "into": "到",
    "is": "",
    "its": "其",
    "of": "的",
    "on": "在",
    "or": "或",
    "per": "每",
    "the": "",
    "this": "此",
    "to": "至",
    "was": "",
    "with": "带有",
    "without": "不含",
}


PRESERVE_EXACT = {
    "A001C002",
    "Allgemeine Hinweise",
    "Anton Bauer",
    "Avid",
    "Avid ALE",
    "Blackmagic Design",
    "Ctrl/Cmd + D",
    "Ctrl/Cmd + Shift + Z / Ctrl + Y",
    "Ctrl/Cmd + Z",
    "DaVinci Resolve",
    "Dana Dolly",
    "DMX",
    "Entfällt",
    "Erneut versuchen",
    "FPS",
    "Fountain",
    "Funkkanäle",
    "Geschätzte Gesamtzeit",
    "Google Drive",
    "Grass Valley",
    "Hotel Astoria",
    "I/E",
    "ISO",
    "Klicken zum Umbenennen",
    "MVR",
    "ND",
    "Nextcloud",
    "noreferrer noopener",
    "Nächstes Krankenhaus",
    "OFL",
    "P/U",
    "SAG-AFTRA",
    "Speichern fehlgeschlagen",
    "V-Mount",
    "WebDAV",
}


PRESERVE_PATTERNS = [
    re.compile(r"^(?:M|C|L|A|Z)(?:\s+[-.$()\w]+){2,}$"),
    re.compile(r"^(?:https?://|mailto:|data:|blob:)"),
    re.compile(r"^(?:/|~/|\./|\.\./)"),
    re.compile(r"^(?:#right-sidebar|\[[^\]]+\]|a\[href\])"),
    re.compile(r"^(?:\$\{[^}]+\}\s*)+$"),
    re.compile(r"^(?:[^\s]+(?:px|vh|vw|rem|em|ms|%|kg|mm|m|h|s|A|W|V|K))$"),
    re.compile(r"^(?:[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+)$"),
    re.compile(r"^(?:[A-Za-z0-9]+-){2,}[A-Za-z0-9]+$"),
    re.compile(r"^(?:\^|\$|\(\?:|\[[^\]]+\]|\\(?:s|d|w|b))"),
    re.compile(r"^(?:M|L|C|A|Z)\s+[-$\d]"),
    re.compile(r"^(?:translate|scale|rotate)\([^)]*\)"),
    re.compile(r"^(?:[A-Za-z0-9_$.-]+\[[^\]]+\](?:\.[A-Za-z0-9_$.-]+)+)$"),
    re.compile(r"^(?:\d+(?:\.\d+)?(?:px)?\s+){2,}\d"),
    re.compile(r"^(?:\d+(?:\.\d+)?(?:px)?\s+)\d+(?:\.\d+)?(?:px)?$"),
    re.compile(r"^\d+(?:\.\d+)?(?:px)?(?:\s+\d+)+,\s*\d"),
    re.compile(r"^[MLCAZ]\d"),
    re.compile(r"^(?:DMX\b|openshotdesigner_)"),
    re.compile(r"^SAG-AFTRA Exhibit G(?: - .+)?$"),
    re.compile(r"^(?:[A-Za-z0-9_$-]+(?:\$\{[^}]+\}[A-Za-z0-9_$-]*)+)$"),
    re.compile(r"^[A-Za-z_$][\w$]*\[.*\]\."),
]


STYLE_TOKEN = re.compile(
    r"^(?:"
    r"[!-]?(?:(?:sm|md|lg|xl|2xl):|absolute|active:|block|bottom-|break-|col-|contents|cursor-|dark:|disabled:|divide-|"
    r"fill|fixed|flex|font-|grid|group-|h-|hidden|hover:|inset-|items-|justify-|"
    r"left-|m[trblxy]?-|max-|min-|not-|object-|opacity-|overflow-|p[trblxy]?-|"
    r"pointer-|relative|resize-|right-|rotate\(|rounded|select-|shadow|shrink-|sm:|space-|"
    r"stroke|text-|top-|transform-|transition-|translate[- (]|truncate|uppercase|w-|whitespace-|z-)"
    r")"
)


PREFIX_REWRITES = [
    (r"^Add a new (.+)$", r"新建\1"),
    (r"^Add an? (.+)$", r"添加\1"),
    (r"^Add (.+)$", r"添加\1"),
    (r"^Create an? (.+)$", r"创建\1"),
    (r"^Create (.+)$", r"创建\1"),
    (r"^Delete (.+)$", r"删除\1"),
    (r"^Remove (.+)$", r"移除\1"),
    (r"^Open (.+)$", r"打开\1"),
    (r"^Close (.+)$", r"关闭\1"),
    (r"^Show (.+)$", r"显示\1"),
    (r"^Hide (.+)$", r"隐藏\1"),
    (r"^Select (.+)$", r"选择\1"),
    (r"^Set (.+)$", r"设置\1"),
    (r"^Change (.+)$", r"更改\1"),
    (r"^Edit (.+)$", r"编辑\1"),
    (r"^Copy (.+)$", r"复制\1"),
    (r"^Upload (.+)$", r"上传\1"),
    (r"^Download (.+)$", r"下载\1"),
    (r"^Print (.+)$", r"打印\1"),
    (r"^Export (.+)$", r"导出\1"),
    (r"^Import (.+)$", r"导入\1"),
    (r"^Use (.+)$", r"使用\1"),
    (r"^Enter (.+)$", r"输入\1"),
    (r"^Reset (.+)$", r"重置\1"),
    (r"^Clear (.+)$", r"清除\1"),
    (r"^Save (.+)$", r"保存\1"),
    (r"^Click to (.+)$", r"点击\1"),
    (r"^Could not (.+)$", r"无法\1"),
    (r"^Cannot (.+)$", r"无法\1"),
    (r"^Please (.+)$", r"请\1"),
]


def module_context(module_field: str) -> str:
    modules = {item.strip() for item in module_field.split(",")}

    def has(prefix: str) -> bool:
        return any(item == prefix or item.startswith(f"{prefix}/") for item in modules)

    if has("components/inspector"):
        return "摄影机、灯光、元素属性与制作参数面板；优先采用摄影和灯光专业术语。"
    if has("components/equipment") or has("domain/assets"):
        return "器材清单与器材包；品牌、型号和协议保留英文，职责与器材类别使用行业译名。"
    if has("components/schedule") or has("domain/scheduling"):
        return "通告单与拍摄计划；区分剧组集合、演员集合、拍摄日和计划收工。"
    if has("components/script") or has("domain/script"):
        return "剧本与镜位标注；保留剧本格式标记，场次、场景标题行与表演提示分开处理。"
    if has("components/continuity") or has("domain/continuity"):
        return "场记与连续性记录；Take 使用“条次”，Good take 使用“可用条次”。"
    if has("components/shotlist") or has("domain/shots"):
        return "镜头表与镜头覆盖；Shot 使用“镜头”，Coverage 使用“镜头覆盖”。"
    if has("components/storyboard"):
        return "故事板与取景画面；景别、机位高度和摄影机运动沿用摄影术语。"
    if has("components/viewfinder"):
        return "取景器模拟；保留画幅、安全框、焦距和摄影机参数符号。"
    if has("components/power") or has("domain/technical"):
        return "电力与配电；相、回路、负载、余量等采用现场电气术语。"
    if has("components/rigging"):
        return "灯光吊挂与结构安全；桁架、吊点、电机和额定负载采用技术术语。"
    if has("components/budget") or has("domain/budget"):
        return "预算与成本；线上/线下成本、估算、实际值、费率和税额保持财务含义。"
    if has("components/locations"):
        return "拍摄地点与勘景；特指制片场景地点时使用“拍摄地点”。"
    if has("components/logistics"):
        return "器材运输与包装；Pickup 在运输语境中译为“接送”，不译为补拍。"
    if has("components/runofshow"):
        return "节目流程与现场执行；使用“提示点”“运行顺序”等现场口径。"
    if has("utils/pdf") or has("domain/reports") or has("components/reports"):
        return "打印报表与制作文档；固定表头优先使用简短、专业的片场译名。"
    return "通用程序界面；优先使用简洁、明确的中文控件语言。"


def should_preserve(source: str, module_field: str) -> tuple[bool, str]:
    value = normalise(source)
    stripped = value.strip("—–-·• ")
    if value in PRESERVE_EXACT:
        return True, "品牌、协议或行业缩写保持英文。"
    if any(pattern.search(stripped) for pattern in PRESERVE_PATTERNS):
        return True, "样式类名、技术标识、路径或只含变量的模板不属于显示文案。"
    style_tokens = stripped.replace("/", " ").split()
    if style_tokens and sum(bool(STYLE_TOKEN.match(token)) for token in style_tokens) >= max(
        2, len(style_tokens) - 1
    ):
        return True, "Tailwind 样式类名或组件布局字符串不属于显示文案。"
    if (
        style_tokens
        and STYLE_TOKEN.match(style_tokens[0])
        and any(token.startswith("${") for token in style_tokens)
    ):
        return True, "样式类名与动态类名组合不属于显示文案。"
    if re.fullmatch(r"[\W_]+", value):
        return True, "仅含符号或分隔符。"
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:\s*[A-Za-z%°]+)?", value):
        return True, "纯数值或计量单位。"
    if re.fullmatch(r"[A-Za-z_$][\w$]*(?:[-:.][A-Za-z0-9_$]+)+", value) and not " " in value:
        return True, "字段标识或稳定键。"
    if "${" in value:
        outside = re.sub(r"\$\{.*?\}", " ", value)
        words = re.findall(r"[A-Za-z][A-Za-z'’-]*", outside)
        meaningful = [word for word in words if word.lower() not in {"px", "m", "h", "s", "a", "w", "v", "k", "mm", "kg"}]
        if (
            (not meaningful or all(len(word.strip("'’-")) <= 2 for word in meaningful))
            and not re.search(r"[\u4e00-\u9fff]", outside)
        ):
            return True, "模板只组合动态值，没有需要翻译的静态显示文字。"
    if module_field == "components/icons":
        return True, "图标目录中的字符串通常为内部标识。"
    return False, ""


def replace_phrases(text: str) -> str:
    result = text
    for source, chinese in sorted(PHRASE_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        result = re.sub(rf"(?<![A-Za-z]){re.escape(source)}(?![A-Za-z])", chinese, result, flags=re.I)
    return result


def replace_terms(text: str) -> str:
    result = text
    combined = {**GLOSSARY, **FUNCTION_WORDS}
    for source, chinese in sorted(combined.items(), key=lambda item: len(item[0]), reverse=True):
        replacement = chinese
        result = re.sub(
            rf"(?<![A-Za-z]){re.escape(source)}(?![A-Za-z])",
            replacement,
            result,
            flags=re.I,
        )
    return result


def polish_mixed_chinese(text: str) -> str:
    result = text
    result = re.sub(r"\s*([，。！？：；、（）])\s*", r"\1", result)
    result = re.sub(r"[ \t]+", " ", result)
    result = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", result)
    result = re.sub(r"\s+([,.;:!?])", r"\1", result)
    result = re.sub(r"([,;:])(?=\S)", r"\1 ", result)
    return result.strip()


def translate_with_patterns(source: str) -> tuple[str, str] | None:
    text = normalise(source)
    # Preserve decorative wrappers while allowing the inner phrase to localize.
    wrappers = [
        (r"^—\s*(.+)$", "— "),
        (r"^–\s*(.+)$", "– "),
        (r"^•\s*(.+)$", "• "),
        (r"^·\s*(.+)$", "· "),
        (r"^\+\s*(.+)$", "+ "),
        (r"^✓\s*(.+)$", "✓ "),
    ]
    for pattern, prefix in wrappers:
        match = re.match(pattern, text)
        if match:
            translated_inner = translate_text(match.group(1), allow_patterns=False)
            if translated_inner[1] != "fallback-unchanged":
                return prefix + translated_inner[0], translated_inner[1]

    for pattern, replacement in PREFIX_REWRITES:
        match = re.match(pattern, text, flags=re.I)
        if not match:
            continue
        tail = match.group(1).rstrip(".")
        translated_tail = translate_text(tail, allow_patterns=False)
        if translated_tail[1] == "fallback-unchanged":
            continue
        return polish_mixed_chinese(replacement.replace(r"\1", translated_tail[0])), "pattern"

    match = re.match(r"^(.+?)\s+(?:for|of)\s+(.+)$", text, flags=re.I)
    if match:
        left = translate_text(match.group(1), allow_patterns=False)
        right = translate_text(match.group(2), allow_patterns=False)
        if left[1] != "fallback-unchanged" and right[1] != "fallback-unchanged":
            return f"{right[0]}的{left[0]}", "pattern"

    match = re.match(r"^Remove (.+?) from (.+)$", text, flags=re.I)
    if match:
        item = translate_text(match.group(1), allow_patterns=False)
        owner = translate_text(match.group(2), allow_patterns=False)
        if item[1] != "fallback-unchanged" and owner[1] != "fallback-unchanged":
            return f"从{owner[0]}中移除{item[0]}", "pattern"

    match = re.match(r"^(.+?) is not set$", text, flags=re.I)
    if match:
        item = translate_text(match.group(1), allow_patterns=False)
        if item[1] != "fallback-unchanged":
            return f"{item[0]}未设置", "pattern"

    match = re.match(r"^No (.+)$", text, flags=re.I)
    if match:
        item = translate_text(match.group(1), allow_patterns=False)
        if item[1] != "fallback-unchanged":
            return f"没有{item[0]}", "pattern"

    match = re.match(r"^(.+?) (?:saved|complete|completed)$", text, flags=re.I)
    if match:
        item = translate_text(match.group(1), allow_patterns=False)
        if item[1] != "fallback-unchanged":
            return f"{item[0]}已完成", "pattern"

    match = re.match(r"^(.+?) (?:failed|error)$", text, flags=re.I)
    if match:
        item = translate_text(match.group(1), allow_patterns=False)
        if item[1] != "fallback-unchanged":
            return f"{item[0]}失败", "pattern"

    return None


def protect_placeholders(text: str) -> tuple[str, dict[str, str]]:
    values: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        token = f"⟦PH{len(values)}⟧"
        values[token] = match.group(0)
        return token

    return re.sub(r"\$\{.*?\}|\{[A-Za-z][\w.[\]-]*\}", replace, text), values


def restore_placeholders(text: str, values: dict[str, str]) -> str:
    for token, value in values.items():
        text = text.replace(token, value)
    return text


def translate_text(source: str, allow_patterns: bool = True) -> tuple[str, str]:
    value = normalise(source)
    wrapped, placeholders = protect_placeholders(value)

    exact = EXACT_OVERRIDES.get(value)
    if exact:
        return restore_placeholders(exact, placeholders), "exact"

    english_dictionary = parse_dictionary()
    exact = english_dictionary.get(value)
    if exact:
        return restore_placeholders(exact, placeholders), "dictionary"

    if allow_patterns:
        pattern_result = translate_with_patterns(wrapped)
        if pattern_result:
            return restore_placeholders(pattern_result[0], placeholders), pattern_result[1]

    phrase_result = replace_phrases(wrapped)
    if phrase_result != wrapped:
        result = restore_placeholders(polish_mixed_chinese(phrase_result), placeholders)
        return result, "phrase"

    result = replace_terms(wrapped)
    if result != wrapped:
        result = polish_mixed_chinese(result)
        return restore_placeholders(result, placeholders), "glossary"

    return source, "fallback-unchanged"


def confidence_for(method: str, source: str, translation: str) -> tuple[str, str]:
    if method in {"exact", "dictionary"}:
        return "高", "已匹配当前界面词典或明确的专业标签译名。"
    if method == "pattern":
        return "中", "按片场与界面动作句式初译，需结合页面确认语序。"
    if method == "phrase":
        return "中", "核心专业短语已匹配；需核对句子中的连接词和语义。"
    if method == "glossary":
        remaining = re.findall(
            r"\b[A-Za-z][A-Za-z'’-]{2,}\b",
            re.sub(r"\$\{.*?\}", " ", translation),
        )
        if len(remaining) <= 2:
            return "中", "主要术语已按专业表替换；需核对中文语序与未覆盖词。"
        return "低", "已优先替换专业术语；仍有未覆盖词或复杂句式，请重点核对。"
    return "低", "自动规则未能可靠拆解；保留原文供人工完成专业初译。"


def build() -> Path:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    entries: list[dict[str, object]] = []
    counts = Counter()

    for entry in catalog["entries"]:
        if not entry["translatable"]:
            continue
        source = entry["source"]
        preserve, preserve_reason = should_preserve(source, entry["module"])
        if preserve:
            draft = {
                "id": entry["id"],
                "source": source,
                "module": entry["module"],
                "pdf": entry["pdf"],
                "translation": source,
                "status": "待确认",
                "disposition": "保留英文",
                "confidence": "不适用",
                "context_note": f"{module_context(entry['module'])} {preserve_reason}",
                "reason": preserve_reason,
                "method": "preserve",
            }
        else:
            translation, method = translate_text(source)
            confidence, confidence_note = confidence_for(method, source, translation)
            draft = {
                "id": entry["id"],
                "source": source,
                "module": entry["module"],
                "pdf": entry["pdf"],
                "translation": translation,
                "status": "待确认",
                "disposition": "初译",
                "confidence": confidence,
                "context_note": f"{module_context(entry['module'])} {confidence_note}",
                "reason": "",
                "method": method,
            }
        entries.append(draft)
        counts["entries"] += 1
        counts[f"status:{draft['status']}"] += 1
        counts[f"disposition:{draft['disposition']}"] += 1
        counts[f"confidence:{draft['confidence']}"] += 1
        counts[f"method:{draft['method']}"] += 1

    by_id = {entry["id"]: entry for entry in entries}
    pdf_entries = [entry for entry in catalog["entries"] if entry["translatable"] and entry["pdf"]]
    result = {
        "metadata": {
            "project": catalog["metadata"]["project"],
            "version": catalog["metadata"]["version"],
            "sourceCommit": catalog["metadata"]["commit"],
            "sourceCatalogGeneratedAt": catalog["metadata"]["generatedAt"],
            "method": "专业术语与面板语境规则辅助初译；所有非保留项默认等待人工核对",
            "counts": dict(sorted(counts.items())),
            "pdfEntries": len(pdf_entries),
        },
        "entries": entries,
    }
    # The assertion catches accidental formatting regressions in future edits.
    missing = [entry["id"] for entry in catalog["entries"] if entry["translatable"] and entry["id"] not in by_id]
    if missing:
        raise RuntimeError(f"Draft coverage missing {len(missing)} catalog entries")

    OUTPUT.write_text(f"{json.dumps(result, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    print(build())
