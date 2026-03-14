import { useState, useEffect } from "react";
import TickerInput      from "./components/TickerInput";
import AgentStream      from "./components/AgentStream";
import StockChart       from "./components/StockChart";
import DecisionCard     from "./components/DecisionCard";
import PortfolioTracker from "./components/PortfolioTracker";
import { useWebSocket } from "./hooks/useWebSocket";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

/** Live UTC clock */
function LiveClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <span className="font-mono text-[11px] text-terminal-dim tabular-nums">
      {time.toUTCString().slice(17, 25)} UTC
    </span>
  );
}

export default function App() {
  const [ticker,     setTicker]     = useState("");
  const [loading,    setLoading]    = useState(false);
  const [result,     setResult]     = useState(null);
  const [ohlcv,      setOhlcv]      = useState([]);
  const [error,      setError]      = useState(null);
  const [portfolio,  setPortfolio]  = useState([]);

  const [streamState, setStreamState] = useState(null);
  const [activeNode,  setActiveNode]  = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [wsStatus,    setWsStatus]   = useState("idle"); // idle | connecting | live | done | error

  const { connect, disconnect } = useWebSocket();

  const ORDER = ["research_quant", "bull", "bear", "decide"];

  async function handleAnalyse(t) {
    disconnect();

    setTicker(t);
    setLoading(true);
    setResult(null);
    setError(null);
    setStreamState(null);
    setActiveNode("research_quant");
    setIsStreaming(true);
    setWsStatus("connecting");
    setOhlcv([]);

    // Fetch chart data in parallel
    const chartPromise = fetch(`${API}/api/v1/stock/${t}`)
      .then((r) => r.json())
      .then((d) => setOhlcv(d.ohlcv ?? []))
      .catch(() => {});

    try {
      await new Promise((resolve, reject) => {
        const ws = connect({
          onOpen: () => {
            setWsStatus("live");
            ws.send(JSON.stringify({ ticker: t, use_llm: !!import.meta.env.VITE_USE_LLM }));
          },
          onMessage: (evt) => {
            let msg;
            try { msg = JSON.parse(evt.data); } catch { return; }

            if (msg.event === "agent_complete") {
              const { event: _e, agent, label: _l, ...data } = msg;
              setStreamState((prev) => ({ ...(prev ?? {}), ...data }));
              const nextIdx = ORDER.indexOf(agent) + 1;
              setActiveNode(nextIdx < ORDER.length ? ORDER[nextIdx] : null);
            }

            if (msg.event === "complete") {
              setResult(msg.result);
              setIsStreaming(false);
              setActiveNode(null);
              setLoading(false);
              setWsStatus("done");
              resolve();
            }

            if (msg.event === "error") {
              reject(new Error(msg.message));
            }
          },
          onError: () => reject(new Error("WebSocket connection failed — is the backend running?")),
          onClose: (e) => {
            if (!e.wasClean && wsStatus === "live") reject(new Error("WebSocket closed unexpectedly"));
          },
        });
      });
    } catch (err) {
      setError(err.message);
      setIsStreaming(false);
      setActiveNode(null);
      setLoading(false);
      setWsStatus("error");
    }

    await chartPromise;
  }

  function handleAddToPortfolio() {
    if (!result?.decision) return;
    setPortfolio((prev) => {
      if (prev.find((p) => p.ticker === ticker)) return prev;
      return [...prev, {
        ticker,
        action:       result.decision.action,
        confidence:   result.decision.confidence,
        positionSize: result.decision.position_size,
        addedAt:      new Date().toISOString(),
      }];
    });
  }

  const liveData    = result ?? streamState;
  const hasContent  = loading || result || streamState;

  // Status bar config
  const statusMap = {
    idle:       { dot: "bg-terminal-dim",    text: "IDLE"       },
    connecting: { dot: "bg-terminal-amber animate-pulse", text: "CONNECTING" },
    live:       { dot: "bg-terminal-green live-dot",      text: "LIVE"       },
    done:       { dot: "bg-terminal-blue",   text: "COMPLETE"   },
    error:      { dot: "bg-terminal-red",    text: "ERROR"      },
  };
  const status = statusMap[wsStatus] ?? statusMap.idle;

  return (
    <div className="min-h-screen bg-terminal-bg text-terminal-text font-sans">

      {/* ── Top status bar ── */}
      <header className="scanlines relative border-b border-terminal-border bg-terminal-panel">
        <div className="relative z-10 flex items-center gap-4 px-4 py-2.5">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-terminal-orange/20 flex items-center justify-center">
              <span className="text-terminal-orange text-xs font-mono font-bold">▲</span>
            </div>
            <div>
              <div className="font-mono text-xs font-bold text-terminal-text tracking-widest uppercase">
                AI HEDGE FUND
              </div>
              <div className="font-mono text-[9px] text-terminal-dim tracking-wider">
                MULTI-AGENT LANGGRAPH TERMINAL
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="w-px h-8 bg-terminal-border mx-2" />

          {/* WS status */}
          <div className="flex items-center gap-1.5">
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${status.dot}`} />
            <span className="font-mono text-[10px] text-terminal-dim">{status.text}</span>
            {ticker && wsStatus !== "idle" && (
              <span className="font-mono text-[10px] text-terminal-orange ml-1">{ticker}</span>
            )}
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Right side */}
          <div className="flex items-center gap-4 text-[10px] font-mono text-terminal-dim">
            <span>WS /ws/analyse</span>
            <span className="text-terminal-border">│</span>
            <LiveClock />
            <span className="text-terminal-border">│</span>
            <span className="text-terminal-orange">v2.0</span>
          </div>
        </div>
      </header>

      {/* ── Main content ── */}
      <main className="p-4 space-y-4 max-w-[1400px] mx-auto">

        <TickerInput onAnalyse={handleAnalyse} loading={loading} />

        {error && (
          <div className="bg-terminal-red/5 border border-terminal-red/30 rounded-lg px-4 py-3
                          font-mono text-xs text-terminal-red flex items-center gap-2">
            <span>⚠</span>
            <span>{error}</span>
          </div>
        )}

        {hasContent && (
          <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-4">

            {/* ── Left column ── */}
            <div className="space-y-4">
              <StockChart
                ticker={ticker}
                ohlcv={ohlcv}
                loading={loading && !ohlcv.length}
                indicators={liveData?.indicators}
              />
              <AgentStream
                streamState={streamState}
                activeNode={activeNode}
                isStreaming={isStreaming}
                ticker={ticker}
              />
            </div>

            {/* ── Right column ── */}
            <div className="space-y-4">
              <DecisionCard
                decision={liveData?.decision}
                loading={loading && !liveData?.decision}
                onAddToPortfolio={handleAddToPortfolio}
              />
              <PortfolioTracker portfolio={portfolio} />

              {/* Fundamental snapshot if available */}
              {liveData?.fundamentals && (
                <FundamentalsPanel fund={liveData.fundamentals} />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

/** Mini fundamentals panel in right sidebar */
function FundamentalsPanel({ fund }) {
  const rows = [
    { k: "P/E",     v: fund.pe_ratio?.toFixed(1)          },
    { k: "FWD P/E", v: fund.forward_pe?.toFixed(1)        },
    { k: "P/B",     v: fund.price_to_book?.toFixed(2)     },
    { k: "ROE",     v: fund.roe != null ? `${(fund.roe*100).toFixed(1)}%` : null },
    { k: "REV GRW", v: fund.revenue_growth != null ? `${(fund.revenue_growth*100).toFixed(1)}%` : null },
    { k: "MARGIN",  v: fund.profit_margin != null ? `${(fund.profit_margin*100).toFixed(1)}%` : null },
    { k: "D/E",     v: fund.debt_to_equity?.toFixed(1)    },
    { k: "TARGET",  v: fund.analyst_target != null ? `$${fund.analyst_target.toFixed(2)}` : null },
  ].filter(r => r.v != null);

  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
      <div className="panel-header">
        <span>Fundamentals</span>
        <span className="ml-auto text-terminal-dim">{fund.ticker}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-0">
        {rows.map(({ k, v }) => (
          <div key={k} className="flex justify-between items-center py-1 border-b border-terminal-border/40">
            <span className="text-[9px] font-mono text-terminal-dim uppercase">{k}</span>
            <span className="text-[11px] font-mono text-terminal-text">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
