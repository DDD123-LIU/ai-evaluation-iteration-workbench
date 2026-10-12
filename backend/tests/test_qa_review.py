"""014确定性人工规则及CSV；不判断答案语义。"""
import csv
import io
from app.services.qa_review import csv_bytes


def test_csv_bom_fixed_order_and_lossless_cells():
    row={'question':'问,题\n"原文"','answer':'答\r\n多行','source_case_number':'001','category':'知识库缺少对应信息'}
    raw=csv_bytes([row])
    assert raw.startswith(b'\xef\xbb\xbf')
    parsed=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'),newline='')))
    assert parsed==[['标准问','参考答案','来源案例编号','问题分类'],list(row.values())]
