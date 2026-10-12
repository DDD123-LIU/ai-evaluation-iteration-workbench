"""按U01整份校验，保留原始字节、字段及有序上下文。"""
import csv
import io
import sys
from dataclasses import dataclass, field

HEADERS = {
    "dialogues": ("案例编号", "用户问题", "客服回答", "聊天记录"),
    "rules": ("规则编号", "规则名称", "规则内容"),
    "knowledge": ("知识编号", "知识标题", "知识内容"),
}
# 标准库默认128KiB不是业务限制；字段仍完整读取。
csv.field_size_limit(sys.maxsize)


class ImportValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("；".join(item["message"] for item in errors))


@dataclass(frozen=True)
class ParsedRow:
    cells: tuple[str, ...]
    line: int
    history: list[dict[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedCSV:
    raw_csv: bytes
    rows: tuple[ParsedRow, ...]


def issue(code, message, line=1, case_id=None, field=None):
    return {"code": code, "message": message, "line": line, "case_id": case_id, "field": field}


def parse_history(raw: str, question: str) -> list[dict[str, str]]:
    messages = []
    # 仅CR/LF是消息分行；Unicode分隔字符仍是原正文。
    for line in io.StringIO(raw, newline=""):
        role = "user" if line.startswith("用户：") else "assistant" if line.startswith("AI：") else None
        if role:
            if messages:
                # 去除消息之间的行分隔符；保留同一消息内部所有续行。
                content = messages[-1]["content"]
                for ending in ("\r\n", "\n", "\r"):
                    if content.endswith(ending):
                        messages[-1]["content"] = content[:-len(ending)]
                        break
            messages.append({"role": role, "content": line[3:]})
        elif messages:
            messages[-1]["content"] += line
        else:
            raise ValueError("聊天记录首行须以用户：或AI：开始")
    if not messages or messages[-1]["role"] != "user":
        raise ValueError("聊天记录须止于当前用户问题，不含当前回复或未来消息")
    if messages[-1]["content"] != question:
        raise ValueError("用户问题与聊天记录最后一条用户消息正文不完全一致")
    return messages


def parse_csv(kind: str, raw: bytes) -> ParsedCSV:
    if kind not in HEADERS:
        raise ImportValidationError([issue("INVALID_KIND", "请选择三类规定模板之一")])
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ImportValidationError([issue("INVALID_ENCODING", "文件须使用UTF-8编码，可带BOM")]) from None
    reader = csv.reader(io.StringIO(decoded, newline=""), strict=True)
    errors, rows, ids, contents = [], [], set(), set()
    try:
        header = next(reader, None)
        if header != list(HEADERS[kind]):
            raise ImportValidationError([issue("INVALID_HEADER", "请使用固定表头及顺序：" + "、".join(HEADERS[kind]))])
        while True:
            line = reader.line_num + 1
            cells = next(reader, None)
            if cells is None:
                break
            case_id = cells[0] if cells and kind == "dialogues" else None
            if len(cells) != len(header):
                errors.append(issue("COLUMN_COUNT", "列数与模板不一致", line, case_id))
                continue
            missing = [name for name, cell in zip(header, cells) if not cell.strip()]
            if missing:
                errors.extend(issue("REQUIRED", "此列必填且不能仅含空白", line, case_id, name) for name in missing)
                continue
            if cells[0] in ids:
                errors.append(issue("DUPLICATE_ID", "同一文件编号重复", line, case_id, header[0]))
            ids.add(cells[0])
            history = []
            if kind == "dialogues":
                content = tuple(cells[1:])
                if content in contents:
                    errors.append(issue("DUPLICATE_CONTENT", "不同编号的其余三列完全相同", line, case_id))
                contents.add(content)
                try:
                    history = parse_history(cells[3], cells[1])
                except ValueError as error:
                    errors.append(issue("INVALID_HISTORY", str(error), line, case_id, "聊天记录"))
            rows.append(ParsedRow(tuple(cells), line, history))
    except csv.Error as error:
        errors.append(issue("INVALID_CSV", "CSV引用格式无效：" + str(error), reader.line_num or 1))
    if not rows and not errors:
        errors.append(issue("NO_DATA", "文件没有可导入的数据行", 2))
    if kind == "dialogues" and len(rows) > 100:
        errors.append(issue("CASE_LIMIT", "每批最多100条，请拆分文件后重传", rows[100].line))
    if errors:
        raise ImportValidationError(errors)
    return ParsedCSV(raw, tuple(rows))
