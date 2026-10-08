"""LangChain ChatPromptTemplate 封装 — 包装核心提示词。"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from daa.core.prompts import DATA_ANALYSIS_SYSTEM_PROMPT, FINAL_REPORT_SYSTEM_PROMPT


def build_analysis_prompt_template() -> ChatPromptTemplate:
    """构建数据分析用的 ChatPromptTemplate。

    系统消息使用 DATA_ANALYSIS_SYSTEM_PROMPT，
    用户消息为对话历史上下文。
    """
    system_msg = SystemMessagePromptTemplate.from_template(DATA_ANALYSIS_SYSTEM_PROMPT)
    human_msg = HumanMessagePromptTemplate.from_template("{conversation_context}")
    return ChatPromptTemplate.from_messages([system_msg, human_msg])


def build_report_prompt_template() -> ChatPromptTemplate:
    """构建最终报告生成用的 ChatPromptTemplate。"""
    system_msg = SystemMessagePromptTemplate.from_template(FINAL_REPORT_SYSTEM_PROMPT)
    human_msg = HumanMessagePromptTemplate.from_template("{report_request}")
    return ChatPromptTemplate.from_messages([system_msg, human_msg])
