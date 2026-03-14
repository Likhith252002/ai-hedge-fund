/**
 * AgentStream.jsx — Bloomberg-terminal log style agent pipeline view.
 * Each agent shows as a row that transitions pending → running → done.
 */

const PIPELINE = [
  {
    node:   "research_quant",
    label:  "RESEARCH + QUANT",
    icon:   "⬡",
    accent: "text-terminal-blue",
    border: "border-terminal-blue/20",
    bg:     "bg-terminal-blue/5",
    extract: (s) => s?.research_summary
      ? { primary: s.research_summary, tag: s.quant_signal, tagColor: signalColor(s.quant_signal) }
      : null,
  },
  {
    node:   "bull",
    label:  "BULL THESIS",
    icon:   "▲",
    accent: "text-terminal-green",
    border: "border-terminal-green/20",
    bg:     "bg-terminal-green/5",
    extract: (s) => s?.bull_thesis ? { primary: s.bull_thesis, tag: "BULL", tagColor: "text-terminal-green" } : null,
  },
  {
    node:   "bear",
    label:  "BEAR THESIS",
    icon:   "▼",
    accent: "text-terminal-red",
    border: "border-terminal-red/20",
    bg:     "bg-terminal-red/5",
    extract: (s) => s?.bear_thesis ? { primary: s.bear_thesis, tag: "BEAR", tagColor: "text-terminal-red" } : null,
  },
  {
    node:   "decide",
    label:  "DECISION ENGINE",
    icon:   "◈",
    accent: "text-terminal-orange",
    border: "border-terminal-orange/20",
    bg:     "bg-terminal-orange/5",
    extract: (s) => s?.decision
      ? {
          primary: s.decision.rationale,
          tag: s.decision.action,
          tagColor: signalColor(s.decision.action),
        }
      : null,
  },
];

function signalColor(sig) {
  if (!sig) return "text-terminal-dim";
  const u = sig.toUpperCase();
  if (u === "BUY"  || u === "BULL") return "text-terminal-green";
  if (u === "SELL" || u === "BEAR") return "text-terminal-red";
  return "text-terminal-amber";
}

function NodeStatus({ status, accent }) {
  if (status === "done")    return <span className={`text-[10px] font-mono ${accent}`}>✓ DONE</span>;
  if (status === "running") return <span className="text-[10px] font-mono text-terminal-orange animate-pulse">● RUNNING</span>;
  return <span className="text-[10px] font-mono text-terminal-dim">○ QUEUE</span>;
}

function SkeletonLines() {
  return (
    <div className="space-y-1.5 mt-2">
      <div className="h-2 bg-terminal-border2 rounded animate-pulse w-full" />
      <div className="h-2 bg-terminal-border2 rounded animate-pulse w-5/6" />
      <div className="h-2 bg-terminal-border2 rounded animate-pulse w-4/6" />
    </div>
  );
}

export default function AgentStream({ streamState, activeNode, isStreaming, ticker }) {
  if (!isStreaming && !streamState) return null;

  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
      <div className="panel-header">
        <span>Agent Pipeline</span>
        <span className="text-terminal-dim">— {ticker}</span>
        {isStreaming && (
          <span className="ml-auto flex items-center gap-1.5 text-[10px] font-mono text-terminal-orange">
            <span className="live-dot inline-block w-1.5 h-1.5 rounded-full bg-terminal-orange" />
            LIVE
          </span>
        )}
      </div>

      <div className="space-y-2">
        {PIPELINE.map(({ node, label, icon, accent, border, bg, extract }) => {
          const data   = extract(streamState);
          const isDone = !!data;
          const isActive = activeNode === node;
          const status = isDone ? "done" : isActive ? "running" : "pending";

          return (
            <div
              key={node}
              className={`rounded border px-3 py-2.5 transition-all duration-300 log-entry
                ${isDone  ? `${border} ${bg}` : "border-terminal-border bg-terminal-bg"}
                ${isActive ? "ring-1 ring-terminal-orange/20" : ""}
              `}
            >
              {/* Header row */}
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-mono ${accent}`}>{icon}</span>
                <span className="text-[11px] font-mono text-terminal-dim tracking-widest">{label}</span>
                <div className="flex items-center gap-1.5 ml-auto">
                  {isDone && data.tag && (
                    <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${data.tagColor}
                      border-current/30 bg-current/5`}>
                      {data.tag}
                    </span>
                  )}
                  <NodeStatus status={status} accent={accent} />
                </div>
              </div>

              {/* Content */}
              {isDone ? (
                <p className="text-xs text-terminal-text/80 font-sans leading-relaxed whitespace-pre-line mt-1.5
                              border-t border-terminal-border/50 pt-1.5">
                  {data.primary}
                </p>
              ) : isActive ? (
                <SkeletonLines />
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
