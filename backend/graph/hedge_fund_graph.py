"""
hedge_fund_graph.py
LangGraph StateGraph pipeline:

  ┌──────────────────────────────┐
  │  research_quant (parallel)   │  ← ResearchAgent + QuantAgent run concurrently
  └─────────────┬────────────────┘
                │
          ┌─────▼──────┐
          │    bull     │
          └─────┬───────┘
                │
          ┌─────▼──────┐
          │    bear     │
          └─────┬───────┘
                │
          ┌─────▼──────┐
          │   decide    │
          └─────┬───────┘
                │
               END
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from agents.bear_agent import BearAgent
from agents.bull_agent import BullAgent
from agents.decision_agent import DecisionAgent
from agents.quant_agent import QuantAgent
from agents.research_agent import ResearchAgent

logger = logging.getLogger(__name__)


class HedgeFundState(TypedDict, total=False):
    ticker:           str
    fundamentals:     Dict
    news:             list
    research_summary: str
    indicators:       Dict
    quant_signal:     str
    bull_thesis:      str
    bear_thesis:      str
    decision:         Dict
    error:            Optional[str]


class HedgeFundGraph:
    """
    Builds and compiles the LangGraph pipeline.
    - research_quant node: runs ResearchAgent + QuantAgent in parallel via asyncio.gather
    - bull / bear / decide nodes: run sequentially
    - stream() yields per-node state updates for WebSocket streaming
    """

    def __init__(self, llm=None):
        self.llm = llm
        self._research = ResearchAgent()
        self._quant    = QuantAgent()
        self._bull     = BullAgent(llm=llm)
        self._bear     = BearAgent(llm=llm)
        self._decision = DecisionAgent(llm=llm)
        self._graph    = self._build()

    # ── Graph construction ───────────────────────────────────────────────────

    def _build(self):
        g = StateGraph(HedgeFundState)

        g.add_node("research_quant", self._research_quant_node)
        g.add_node("bull",           self._bull.run)
        g.add_node("bear",           self._bear.run)
        g.add_node("decide",         self._decision.run)

        g.set_entry_point("research_quant")
        g.add_edge("research_quant", "bull")
        g.add_edge("bull",           "bear")
        g.add_edge("bear",           "decide")
        g.add_edge("decide",         END)

        return g.compile()

    # ── Parallel research + quant node ───────────────────────────────────────

    async def _research_quant_node(self, state: HedgeFundState) -> HedgeFundState:
        """Run ResearchAgent and QuantAgent concurrently; merge their outputs."""
        research_task = asyncio.create_task(self._research.run(dict(state)))
        quant_task    = asyncio.create_task(self._quant.run(dict(state)))

        research_result, quant_result = await asyncio.gather(
            research_task, quant_task,
            return_exceptions=False,
        )

        # Both agents return a full state dict; merge over the incoming state.
        # research adds: fundamentals, news, research_summary
        # quant adds:    indicators, quant_signal
        merged = dict(state)
        _RESEARCH_KEYS = {"fundamentals", "news", "research_summary"}
        _QUANT_KEYS    = {"indicators", "quant_signal"}

        for k, v in research_result.items():
            if k in _RESEARCH_KEYS:
                merged[k] = v
        for k, v in quant_result.items():
            if k in _QUANT_KEYS:
                merged[k] = v

        logger.info(
            "research_quant_node done: signal=%s, news=%d articles",
            merged.get("quant_signal", "?"),
            len(merged.get("news", [])),
        )
        return merged

    # ── Public API ───────────────────────────────────────────────────────────

    async def run(self, ticker: str) -> HedgeFundState:
        """Run the full pipeline and return the final state."""
        logger.info("HedgeFundGraph.run: %s", ticker)
        state: HedgeFundState = {"ticker": ticker.upper()}
        result = await self._graph.ainvoke(state)
        logger.info(
            "HedgeFundGraph.run complete: %s → %s",
            ticker, result.get("decision", {}).get("action", "N/A"),
        )
        return result

    async def stream(self, ticker: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream state updates one node at a time.
        Each yielded dict has the shape:
          { "node": <node_name>, "state": <state_dict_after_this_node> }
        """
        logger.info("HedgeFundGraph.stream: %s", ticker)
        state: HedgeFundState = {"ticker": ticker.upper()}

        async for step in self._graph.astream(state):
            # LangGraph 0.1.x yields {node_name: state_dict} per step
            for node_name, node_state in step.items():
                logger.info("stream: node=%s done", node_name)
                yield {"node": node_name, "state": node_state}
