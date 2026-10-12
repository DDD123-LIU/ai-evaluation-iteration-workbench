"""009与010/011/013/016的交接类型；不包含模型调用或业务评分。"""
from dataclasses import dataclass, field
from typing import Any, Awaitable, Protocol


@dataclass(frozen=True)
class ConfigSpec:
    stage: str
    contract_version: str
    prompt_version: str
    full_prompt: str
    request_model: str
    parameters: dict
    documented_release: str


@dataclass(frozen=True)
class ItemSpec:
    case_id: str
    stage: str
    side: str
    gap_key: str
    request: dict


@dataclass(frozen=True)
class Plan:
    kind: str
    upload_id: str
    rule_version_id: str
    kb_version_id: str
    case_ids: list[str]
    configs: list[ConfigSpec]
    items: list[ItemSpec]


@dataclass(frozen=True)
class Outcome:
    success: bool
    payload: dict = field(default_factory=dict)
    raw: str = ''
    error_category: str | None = None
    error_detail: str | None = None
    retry_after: float | None = None
    envelope: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Transition:
    phase: str
    items: list[ItemSpec]


class Transport(Protocol):
    def start_once(self, attempt: dict) -> Awaitable[Outcome]:
        """同步交给transport，然后返回可等待对象。只发送一次，无SDK重试。

        010负责300秒截止及真正结束后的清理。009等待清理完成才释放名额。
        """
        ...


class BusinessHooks(Protocol):
    def item_saved(self, session: Any, task: Any, item: Any, outcome: Outcome) -> list[ItemSpec]:
        """业务结果写入同一事务；016在G成功后返回E，013保存QA。不得网络调用。"""
        ...

    def phase_finished(self, session: Any, task: Any) -> Transition:
        """011/013提供应生成Q；016冻结自动结果。done释放窗口。"""
        ...


class NoSend(Exception):
    """010能证明没有交给HTTP transport；009撤销预留，不计调用预算。"""


class LocalBlocked(Exception):
    """010本地预检失败，未发送；记录CALL_ERROR及次数0。"""
