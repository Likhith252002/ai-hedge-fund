/** PortfolioTracker.jsx — Terminal-style positions table */

const ACTION_CFG = {
  BUY:  { color: "text-terminal-green", badge: "bg-terminal-green/10 border-terminal-green/30" },
  SELL: { color: "text-terminal-red",   badge: "bg-terminal-red/10 border-terminal-red/30"     },
  HOLD: { color: "text-terminal-amber", badge: "bg-terminal-amber/10 border-terminal-amber/30" },
};

function ConfDots({ value }) {
  const filled = Math.round(value / 10);
  return (
    <span className="font-mono text-[9px] tracking-[-1px]">
      {"●".repeat(filled)}
      <span className="text-terminal-border2">{"●".repeat(10 - filled)}</span>
    </span>
  );
}

export default function PortfolioTracker({ portfolio, onRemove }) {
  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
      <div className="panel-header">
        <span>Portfolio</span>
        <span className="ml-auto text-terminal-dim">{portfolio.length} POSITION{portfolio.length !== 1 ? "S" : ""}</span>
      </div>

      {portfolio.length === 0 ? (
        <div className="py-4 text-center">
          <div className="text-terminal-dim font-mono text-[10px] uppercase tracking-wider">NO POSITIONS</div>
          <div className="text-terminal-dim/50 font-sans text-xs mt-1">Analyse a stock and add to portfolio</div>
        </div>
      ) : (
        <>
          {/* Column headers */}
          <div className="grid grid-cols-[1fr_auto_auto_auto] gap-2 mb-1 pb-1 border-b border-terminal-border">
            {["SYMBOL", "ACTION", "SIZE", "CONF"].map((h) => (
              <span key={h} className="text-[9px] font-mono text-terminal-dim uppercase tracking-wider text-right first:text-left">
                {h}
              </span>
            ))}
          </div>

          {/* Rows */}
          <div className="space-y-0.5">
            {portfolio.map((p) => {
              const cfg = ACTION_CFG[p.action] ?? ACTION_CFG.HOLD;
              return (
                <div
                  key={p.ticker}
                  className="grid grid-cols-[1fr_auto_auto_auto] gap-2 items-center py-1.5
                             border-b border-terminal-border/40 last:border-0
                             hover:bg-terminal-bg/50 rounded px-1 transition-colors group"
                >
                  <span className="font-mono text-sm font-semibold text-terminal-text">{p.ticker}</span>

                  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${cfg.color} ${cfg.badge}`}>
                    {p.action}
                  </span>

                  <span className="font-mono text-xs text-terminal-text text-right">
                    {p.positionSize}%
                  </span>

                  <div className="text-right">
                    <ConfDots value={p.confidence} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="mt-3 pt-2 border-t border-terminal-border flex justify-between items-center">
            <span className="text-[9px] font-mono text-terminal-dim">
              TOTAL ALLOCATED: {portfolio.reduce((s, p) => s + (p.positionSize || 0), 0)}%
            </span>
            <span className="text-[9px] font-mono text-terminal-dim">
              {portfolio.filter(p => p.action === "BUY").length}L /&nbsp;
              {portfolio.filter(p => p.action === "SELL").length}S
            </span>
          </div>
        </>
      )}
    </div>
  );
}
