import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function PriceStat({ label, value, color }) {
  return (
    <div className="text-center">
      <div className="text-[9px] font-mono text-terminal-dim uppercase tracking-wider">{label}</div>
      <div className={`text-xs font-mono font-semibold ${color ?? "text-terminal-text"}`}>{value}</div>
    </div>
  );
}

export default function StockChart({ ticker, ohlcv, loading, indicators }) {
  if (loading && !ohlcv.length) {
    return (
      <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
        <div className="panel-header">Price Chart</div>
        <div className="h-48 bg-terminal-bg rounded animate-pulse" />
      </div>
    );
  }
  if (!ohlcv.length) return null;

  const labels  = ohlcv.map((d) => d.date.slice(5));   // MM-DD
  const closes  = ohlcv.map((d) => d.close);
  const first   = closes[0];
  const last    = closes[closes.length - 1];
  const trend   = last >= first;
  const changePct = (((last - first) / first) * 100).toFixed(2);

  const lineColor = trend ? "#00d964" : "#ff2d55";
  const fillColor = trend ? "rgba(0,217,100,0.06)" : "rgba(255,45,85,0.06)";

  const chartData = {
    labels,
    datasets: [{
      label:           ticker,
      data:            closes,
      borderColor:     lineColor,
      backgroundColor: fillColor,
      borderWidth:     1.5,
      pointRadius:     0,
      fill:            true,
      tension:         0.2,
    }],
  };

  // Overlay SMA lines if available
  if (indicators?.sma_20) {
    // We only have the last value; skip line overlay for simplicity
  }

  const options = {
    responsive:          true,
    maintainAspectRatio: true,
    interaction:         { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#0a0c10",
        borderColor:     "#1e2535",
        borderWidth:     1,
        titleColor:      "#4b5563",
        bodyColor:       "#c9d1d9",
        titleFont:       { family: "'IBM Plex Mono'" },
        bodyFont:        { family: "'IBM Plex Mono'", size: 11 },
        padding:         10,
        callbacks: {
          title: (items) => items[0].label,
          label: (item)  => ` $${item.raw.toFixed(2)}`,
        },
      },
    },
    scales: {
      x: {
        ticks:  { color: "#374151", font: { family: "'IBM Plex Mono'", size: 9 }, maxTicksLimit: 8 },
        grid:   { color: "#0f1117" },
        border: { color: "#151b26" },
      },
      y: {
        position: "right",
        ticks:    { color: "#374151", font: { family: "'IBM Plex Mono'", size: 9 }, maxTicksLimit: 6,
                    callback: (v) => `$${v.toFixed(0)}` },
        grid:     { color: "#0f1117" },
        border:   { color: "#151b26" },
      },
    },
  };

  const hi  = Math.max(...closes).toFixed(2);
  const lo  = Math.min(...closes).toFixed(2);
  const vol = ohlcv[ohlcv.length - 1]?.volume;
  const volStr = vol ? (vol / 1e6).toFixed(1) + "M" : "—";

  return (
    <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="panel-header">
          <span>{ticker}</span>
          <span className="text-terminal-dim">— 3 MONTH</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-lg font-semibold text-terminal-text">
            ${last.toFixed(2)}
          </span>
          <span className={`font-mono text-xs font-semibold ${trend ? "text-terminal-green" : "text-terminal-red"}`}>
            {trend ? "▲" : "▼"} {Math.abs(changePct)}%
          </span>
        </div>
      </div>

      <Line data={chartData} options={options} />

      {/* Mini stats row */}
      <div className="flex justify-between mt-3 pt-2 border-t border-terminal-border">
        <PriceStat label="3M HIGH"  value={`$${hi}`}  color="text-terminal-green" />
        <PriceStat label="3M LOW"   value={`$${lo}`}  color="text-terminal-red"   />
        <PriceStat label="LAST VOL" value={volStr} />
        {indicators?.rsi_14 && (
          <PriceStat
            label="RSI-14"
            value={indicators.rsi_14}
            color={indicators.rsi_14 > 70 ? "text-terminal-red" : indicators.rsi_14 < 30 ? "text-terminal-green" : "text-terminal-text"}
          />
        )}
        {indicators?.sma_20 && indicators?.sma_50 && (
          <PriceStat
            label="SMA X"
            value={indicators.sma_20 > indicators.sma_50 ? "GOLDEN" : "DEATH"}
            color={indicators.sma_20 > indicators.sma_50 ? "text-terminal-green" : "text-terminal-red"}
          />
        )}
      </div>
    </div>
  );
}
