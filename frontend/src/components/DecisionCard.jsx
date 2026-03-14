/** DecisionCard.jsx — Bloomberg-style final decision panel */

const ACTION_CFG = {
  BUY:  { color: "text-terminal-green", bg: "bg-terminal-green/10",  border: "border-terminal-green/30",  glow: "shadow-terminal-green/10"  },
  SELL: { color: "text-terminal-red",   bg: "bg-terminal-red/10",    border: "border-terminal-red/30",    glow: "shadow-terminal-red/10"    },
  HOLD: { color: "text-terminal-amber", bg: "bg-terminal-amber/10",  border: "border-terminal-amber/30",  glow: "shadow-terminal-amber/10"  },
};

function BlockBar({ value, max = 100, color }) {
  const filled = Math.round((value / max) * 10);
  return (
    <div className={`font-mono text-xs tracking-[-2px] ${color}`}>
      {"█".repeat(filled)}
      <span className="text-terminal-border2">{"█".repeat(10 - filled)}</span>
    </div>
  );
}

function DataRow({ label, value, valueClass }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-terminal-border last:border-0">
      <span className="text-[10px] font-mono text-terminal-dim uppercase tracking-wider">{label}</span>
      <span className={`text-xs font-mono font-semibold ${valueClass ?? "text-terminal-text"}`}>{value}</span>
    </div>
  );
}

export default function DecisionCard({ decision, loading, onAddToPortfolio }) {
  if (loading && !decision) {
    return (
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <div className="panel-header">Final Decision</div>
        <div className="space-y-3">
          <div className="h-12 bg-terminal-bg rounded animate-pulse" />
          <div className="h-4 bg-terminal-bg rounded animate-pulse w-3/4" />
          <div className="h-4 bg-terminal-bg rounded animate-pulse w-1/2" />
          <div className="h-4 bg-terminal-bg rounded animate-pulse w-2/3" />
        </div>
      </div>
    );
  }
  if (!decision) return null;

  const cfg = ACTION_CFG[decision.action] ?? ACTION_CFG.HOLD;

  const upside = decision.current_price && decision.analyst_target
    ? (((decision.analyst_target - decision.current_price) / decision.current_price) * 100).toFixed(1)
    : null;

  return (
    <div className={`bg-terminal-panel border ${cfg.border} rounded-lg p-4 shadow-lg ${cfg.glow}`}>
      <div className="panel-header">Final Decision</div>

      {/* Big action badge */}
      <div className={`flex items-center gap-3 mb-4 p-3 rounded ${cfg.bg} border ${cfg.border}`}>
        <span className={`font-mono text-3xl font-bold tracking-tight ${cfg.color}`}>
          {decision.action}
        </span>
        <div className="ml-auto text-right">
          {decision.current_price > 0 && (
            <div className="font-mono text-sm font-semibold text-terminal-text">
              ${decision.current_price.toFixed(2)}
            </div>
          )}
          {upside !== null && (
            <div className={`font-mono text-[10px] ${parseFloat(upside) >= 0 ? "text-terminal-green" : "text-terminal-red"}`}>
              {parseFloat(upside) >= 0 ? "▲" : "▼"} {Math.abs(upside)}% to target
            </div>
          )}
        </div>
      </div>

      {/* Data grid */}
      <div className="space-y-0 mb-3">
        <DataRow
          label="Confidence"
          value={`${decision.confidence}%`}
          valueClass={cfg.color}
        />
        <div className="py-1.5 border-b border-terminal-border">
          <BlockBar value={decision.confidence} color={cfg.color} />
        </div>
        <DataRow
          label="Position Size"
          value={`${decision.position_size}%`}
          valueClass="text-terminal-text"
        />
        <div className="py-1.5 border-b border-terminal-border">
          <BlockBar value={decision.position_size} max={10} color={cfg.color} />
        </div>
      </div>

      {/* Rationale */}
      <p className="text-[11px] font-sans text-terminal-dim leading-relaxed mb-4 border-t border-terminal-border pt-3">
        {decision.rationale}
      </p>

      <button
        onClick={onAddToPortfolio}
        className={`w-full py-2 rounded border ${cfg.border} ${cfg.bg}
                    ${cfg.color} font-mono text-[11px] uppercase tracking-widest
                    hover:brightness-125 transition-all`}
      >
        + ADD TO PORTFOLIO
      </button>
    </div>
  );
}
