import { useState } from "react";

const WATCHLIST = [
  { t: "AAPL",  label: "AAPL"  },
  { t: "TSLA",  label: "TSLA"  },
  { t: "NVDA",  label: "NVDA"  },
  { t: "MSFT",  label: "MSFT"  },
  { t: "GOOGL", label: "GOOGL" },
  { t: "AMZN",  label: "AMZN"  },
  { t: "META",  label: "META"  },
  { t: "SPY",   label: "SPY"   },
];

export default function TickerInput({ onAnalyse, loading }) {
  const [value, setValue] = useState("");

  function submit(t) {
    const ticker = (t ?? value).trim().toUpperCase();
    if (ticker) onAnalyse(ticker);
  }

  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
      <div className="panel-header mb-3">
        <span>Symbol Lookup</span>
        {loading && (
          <span className="ml-auto text-terminal-orange font-mono text-[10px] animate-pulse">
            ● RUNNING ANALYSIS
          </span>
        )}
      </div>

      <div className="flex gap-2">
        {/* Terminal-style input */}
        <div className="flex-1 relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-terminal-orange font-mono text-sm select-none">
            &gt;
          </span>
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="ENTER TICKER SYMBOL"
            disabled={loading}
            className="w-full bg-terminal-bg border border-terminal-border2 rounded pl-8 pr-4 py-2.5
                       font-mono text-sm text-terminal-text placeholder-terminal-dim
                       focus:outline-none focus:border-terminal-orange/60 focus:ring-1 focus:ring-terminal-orange/20
                       disabled:opacity-40 transition-colors"
          />
        </div>

        <button
          onClick={() => submit()}
          disabled={loading || !value.trim()}
          className="px-5 py-2.5 bg-terminal-orange/10 hover:bg-terminal-orange/20
                     border border-terminal-orange/40 hover:border-terminal-orange/70
                     disabled:opacity-30 disabled:cursor-not-allowed
                     rounded text-terminal-orange font-mono text-xs font-semibold
                     uppercase tracking-widest transition-all"
        >
          {loading ? "ANALYSING" : "ANALYSE"}
        </button>
      </div>

      {/* Watchlist chips */}
      <div className="flex gap-1.5 mt-3 flex-wrap">
        <span className="text-[10px] font-mono text-terminal-dim self-center mr-1">WATCHLIST:</span>
        {WATCHLIST.map(({ t, label }) => (
          <button
            key={t}
            onClick={() => { setValue(t); submit(t); }}
            disabled={loading}
            className="px-2.5 py-0.5 bg-terminal-bg border border-terminal-border2
                       hover:border-terminal-border hover:text-terminal-text
                       rounded text-[11px] font-mono text-terminal-dim
                       disabled:opacity-30 transition-all"
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
