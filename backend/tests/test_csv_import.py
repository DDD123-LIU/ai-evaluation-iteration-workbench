"""F01～F04/D01：独立本地输入，不是正式验收集。"""
import csv
import io

import pytest

from app.domain.csv_import import HEADERS, ImportValidationError, parse_csv


def encode(kind, rows, *, bom=False, headers=None):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(HEADERS[kind] if headers is None else headers)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig" if bom else "utf-8")


def dialogue(number="1", question="有什么权益？", reply="请查看权益说明。", history=None):
    return [number, question, reply, history if history is not None else "用户：" + question]


@pytest.mark.parametrize("kind,row", [
    ("dialogues", dialogue(question='权益含逗号,和"引号"\r\n第二行')),
    ("rules", ["R1", "名称", '原文,\r\n包含"引用"']),
    ("knowledge", ["K1", "标题", '权益,\n含"引号"']),
])
@pytest.mark.parametrize("bom", [False, True])
def test_bom_quoting_and_raw_text_round_trip(kind, row, bom):
    raw = encode(kind, [row], bom=bom)
    parsed = parse_csv(kind, raw)
    assert parsed.raw_csv == raw
    assert parsed.rows[0].cells == tuple(row)


def test_message_continuations_preserve_order_and_spaces():
    history = "用户：前一个问题\nAI：先前回复\n续行,含引号\n用户：  当前问题\n第二行"
    question = "  当前问题\n第二行"
    parsed = parse_csv("dialogues", encode("dialogues", [dialogue(question=question, history=history)]))
    assert parsed.rows[0].history == [
        {"role": "user", "content": "前一个问题"},
        {"role": "assistant", "content": "先前回复\n续行,含引号"},
        {"role": "user", "content": question},
    ]
    assert parsed.rows[0].cells[3] == history


@pytest.mark.parametrize("kind", HEADERS)
@pytest.mark.parametrize("headers", [[], ["错误"], ["规则内容", "规则名称", "规则编号"]])
def test_wrong_header_rejected(kind, headers):
    if headers == list(HEADERS[kind]):
        return
    with pytest.raises(ImportValidationError) as error:
        parse_csv(kind, encode(kind, [], headers=headers))
    assert error.value.errors[0]["line"] == 1


@pytest.mark.parametrize("kind", HEADERS)
@pytest.mark.parametrize("raw", [b"", b" \r\n", b"\xff\xfe", b'"unclosed'])
def test_empty_encoding_and_unparseable_rejected(kind, raw):
    with pytest.raises(ImportValidationError):
        parse_csv(kind, raw)


@pytest.mark.parametrize("kind", HEADERS)
def test_header_only_and_blank_record_rejected(kind):
    for rows in ([], [[""] * len(HEADERS[kind])], [[" "] * len(HEADERS[kind])], [[]]):
        with pytest.raises(ImportValidationError):
            parse_csv(kind, encode(kind, rows))


@pytest.mark.parametrize("kind", HEADERS)
def test_each_required_column_and_wrong_row_width(kind):
    good = dialogue() if kind == "dialogues" else ["1", "标题", "内容"]
    bad_rows = []
    for index in range(len(good)):
        row = good.copy()
        row[index] = " \t"
        bad_rows.append(row)
    bad_rows.extend([good[:-1], good + ["多余"]])
    for row in bad_rows:
        with pytest.raises(ImportValidationError) as error:
            parse_csv(kind, encode(kind, [good, row]))
        assert error.value.errors[0]["line"] >= 3


@pytest.mark.parametrize("kind", HEADERS)
def test_duplicate_ids_within_file_rejected(kind):
    rows = [dialogue(), dialogue(reply="不同回复")] if kind == "dialogues" else [["1", "A", "内容A"], ["1", "B", "内容B"]]
    with pytest.raises(ImportValidationError) as error:
        parse_csv(kind, encode(kind, rows))
    assert error.value.errors[0]["code"] == "DUPLICATE_ID"


def test_different_ids_same_three_columns_rejected():
    with pytest.raises(ImportValidationError) as error:
        parse_csv("dialogues", encode("dialogues", [dialogue("1"), dialogue("2")]))
    assert error.value.errors[0]["code"] == "DUPLICATE_CONTENT"


@pytest.mark.parametrize("history", ["无角色", "AI：无用户消息", "用户：另一个问题", "用户：有什么权益？\nAI：当前回答", "用户："])
def test_invalid_or_mismatched_context(history):
    with pytest.raises(ImportValidationError) as error:
        parse_csv("dialogues", encode("dialogues", [dialogue("case-X", history=history)]))
    assert error.value.errors[0]["case_id"] == "case-X"


def test_question_not_trimmed_and_multiline_line_location():
    row = dialogue("bad", question=" 当前问题", history="用户：当前问题")
    raw = encode("dialogues", [dialogue(question="第一行\n第二行"), row])
    with pytest.raises(ImportValidationError) as error:
        parse_csv("dialogues", raw)
    # 前一行的问题与聊天记录均跨两行，下一条记录从物理第5行开始。
    assert error.value.errors[0]["line"] == 5


def test_100_allowed_101_rejected_but_materials_not_case_limited():
    rows = [dialogue(str(i), question=f"问题{i}") for i in range(101)]
    assert len(parse_csv("dialogues", encode("dialogues", rows[:100])).rows) == 100
    with pytest.raises(ImportValidationError) as error:
        parse_csv("dialogues", encode("dialogues", rows))
    assert "拆分" in str(error.value)
    assert len(parse_csv("knowledge", encode("knowledge", [[str(i), "标题", "内容"] for i in range(101)])).rows) == 101


def test_long_material_cell_has_no_unconfirmed_128k_limit():
    content = "说明" * 100000
    assert parse_csv("rules", encode("rules", [["1", "名称", content]])).rows[0].cells[2] == content


def test_unicode_line_separator_is_preserved_as_body_text():
    question = "正文\u2028AI：仍是正文"
    parsed = parse_csv("dialogues", encode("dialogues", [dialogue(question=question)]))
    assert parsed.rows[0].history == [{"role": "user", "content": question}]


@pytest.mark.parametrize("ending", ["\r\n", "\n", "\r"])
def test_history_preserves_final_body_newline_and_message_boundaries(ending):
    question = "本次问题" + ending
    history = "用户：此前问题" + ending + "AI：此前回复" + ending + "用户：" + question
    parsed = parse_csv("dialogues", encode("dialogues", [dialogue(question=question, history=history)]))
    assert parsed.rows[0].history == [
        {"role": "user", "content": "此前问题"},
        {"role": "assistant", "content": "此前回复"},
        {"role": "user", "content": question}]
