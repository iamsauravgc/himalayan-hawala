"use client";
import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Area, ReferenceLine
} from "recharts";

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

  :root {
    --canvas: #0b0e11;
    --surface: #1e2329;
    --surface-elevated: #2b3139;
    --hairline: #2b3139;
    --primary: #FCD535;
    --on-primary: #181a20;
    --on-dark: #ffffff;
    --body: #eaecef;
    --muted: #707a8a;
    --muted-strong: #929aa5;
    --trading-up: #0ecb81;
    --trading-down: #f6465d;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--canvas); color: var(--body); font-family: 'Inter', sans-serif; }
  .app { min-height: 100vh; padding: 40px clamp(20px, 4vw, 56px); width: 100%; }

  .header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 28px; }
  .brand { font-size: 19px; font-weight: 700; letter-spacing: -0.3px; }
  .brand span { color: var(--primary); }
  .tagline { color: var(--muted); font-size: 11px; font-weight: 500; letter-spacing: 0.4px; margin-top: 2px; }
  .header-meta { font-size: 11px; color: var(--muted); }

  /* Top metrics row */
  .metrics-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 14px; }
  @media (max-width: 900px) { .metrics-row { grid-template-columns: 1fr; } }
  .metric-card { background: var(--surface); border-radius: 10px; padding: 18px 20px; }
  .metric-label { font-size: 11px; color: var(--muted); font-weight: 500; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
  .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 700; line-height: 1; }
  .metric-value.gold { color: var(--primary); }
  .metric-delta { font-size: 12px; font-weight: 600; margin-top: 8px; display: flex; align-items: center; gap: 4px; }
  .metric-delta.up { color: var(--trading-up); }
  .metric-delta.down { color: var(--trading-down); }
  .metric-sub { font-size: 11px; color: var(--muted); margin-top: 8px; }

  /* Main content row: chart + side panel */
  .main-row { display: grid; grid-template-columns: 1fr 320px; gap: 14px; margin-bottom: 14px; }
  @media (max-width: 900px) { .main-row { grid-template-columns: 1fr; } }

  .panel { background: var(--surface); border-radius: 10px; padding: 22px; display: flex; flex-direction: column; height: 100%; }
  .panel-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
  .panel-title { font-size: 14px; font-weight: 600; color: var(--on-dark); }
  .panel-sub { font-size: 11px; color: var(--muted); margin-top: 3px; }
  .panel-control {
    font-size: 10px; font-weight: 600; letter-spacing: 0.4px; text-transform: uppercase;
    padding: 5px 10px; border-radius: 5px; background: var(--surface-elevated); color: var(--primary);
  }

  .alert-panel-body { display: flex; flex-direction: column; flex: 1; }
  .alert-box { padding: 14px; background: var(--surface-elevated); border-radius: 8px; font-size: 12px; line-height: 1.7; color: var(--body); flex: 1; }
  .alert-placeholder { padding: 14px; font-size: 12px; color: var(--muted); line-height: 1.6; flex: 1; }

  .tooltip-box { background: var(--surface-elevated); border-radius: 6px; padding: 10px 14px; font-size: 12px; }
  .tooltip-box .t-label { color: var(--muted); font-size: 10px; margin-bottom: 4px; }
  .tooltip-box .t-value { font-family: 'JetBrains Mono', monospace; color: var(--primary); font-weight: 600; font-size: 15px; }

  /* News feed panel */
  .feed-panel { background: var(--surface); border-radius: 10px; padding: 22px; }
  .feed-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .refresh-btn {
    background: var(--surface-elevated); border: none; color: var(--primary);
    padding: 7px 14px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; font-family: 'Inter';
  }
  .refresh-btn:hover { background: var(--primary); color: var(--on-primary); }
  .refresh-btn:disabled { opacity: 0.5; cursor: default; }
  .last-updated { font-size: 10px; color: var(--muted); margin-top: 3px; }

  .news-row { padding: 13px 0; border-bottom: 1px solid var(--hairline); font-size: 13px; line-height: 1.5; }
  .news-row:last-child { border-bottom: none; }
  .news-meta { display: flex; gap: 10px; align-items: center; margin-top: 6px; font-size: 11px; color: var(--muted); }
  .pill { padding: 3px 9px; border-radius: 4px; font-size: 10px; font-weight: 600; letter-spacing: 0.3px; text-transform: uppercase; }
  .pill.positive { background: rgba(14,203,129,0.15); color: var(--trading-up); }
  .pill.negative { background: rgba(246,70,93,0.15); color: var(--trading-down); }
  .pill.neutral { background: var(--surface-elevated); color: var(--muted-strong); }

  .currency-bar { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 20px; }
  .currency-btn {
    background: var(--surface); border: 1px solid var(--hairline); color: var(--muted);
    padding: 6px 14px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; font-family: 'Inter', sans-serif;
    transition: all 0.15s;
  }
  .currency-btn:hover { border-color: var(--primary); color: var(--primary); }
  .currency-btn.active { background: var(--primary); color: var(--on-primary); border-color: var(--primary); }

  .chart-legend { display: flex; gap: 16px; margin-bottom: 12px; font-size: 10px; color: var(--muted); align-items: center; }
  .chart-legend span { display: flex; align-items: center; gap: 5px; }
  .legend-line { width: 18px; height: 2px; border-radius: 1px; display: inline-block; }
  .legend-line.solid { background: var(--primary); }
  .legend-line.dashed { height: 0; border-top: 2px dashed var(--trading-up); width: 18px; }
  .legend-band { width: 18px; height: 8px; border-radius: 2px; display: inline-block; background: rgba(252,213,53,0.15); border: 1px solid rgba(252,213,53,0.3); }
`;

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="tooltip-box">
        <div className="t-label">{label}</div>
        <div className="t-value">{payload[0]?.value?.toFixed(4)} NPR</div>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [currency, setCurrency] = useState("USD");
  const [currencies, setCurrencies] = useState([]);
  const [liveRate, setLiveRate] = useState(null);
  const [history, setHistory] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [news, setNews] = useState([]);
  const [alert, setAlert] = useState(null);
  const [loadingAlert, setLoadingAlert] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/api/rates/currencies").then(r => r.json()).then(setCurrencies);
    fetch("http://localhost:8000/api/sentiment/").then(r => r.json()).then(d => {
      setNews(d.slice(0, 6));
      setLastUpdated(new Date());
    });
  }, []);

  useEffect(() => {
    fetch(`http://localhost:8000/api/rates/live?currency=${currency}`).then(r => r.json()).then(setLiveRate);
    fetch(`http://localhost:8000/api/rates/history?currency=${currency}&days=90`).then(r => r.json()).then(setHistory);
    fetch(`http://localhost:8000/api/predict/?currency=${currency}`).then(r => r.json()).then(setPredictions);
    setAlert(null);
    setLoadingAlert(true);
    fetch(`http://localhost:8000/api/alerts/generate?currency=${currency}&lang=en`).then(r => r.json()).then(d => {
      setAlert(d);
      setLoadingAlert(false);
    });
  }, [currency]);

  const chartData = (() => {
    if (!history.length && !predictions.length) return [];

    const dataMap = {};

    history.forEach(h => {
      const d = new Date(h.recorded_at).toISOString().slice(5, 10);
      dataMap[d] = { ...dataMap[d], date: d, actual: parseFloat(h.mid_rate) };
    });

    predictions.forEach(p => {
      const d = p.predicted_for.slice(5);
      dataMap[d] = {
        ...dataMap[d],
        date: d,
        predicted: parseFloat(p.predicted_rate),
        low: parseFloat(p.confidence_low),
        high: parseFloat(p.confidence_high),
      };
    });

    return Object.values(dataMap).sort((a, b) => a.date.localeCompare(b.date));
  })();

  const trend = predictions.length >= 2
    ? predictions[predictions.length - 1].predicted_rate - predictions[0].predicted_rate
    : 0;

  const refreshNews = async () => {
    setRefreshing(true);
    await fetch("http://localhost:8000/api/sentiment/refresh", { method: "POST" });
    const newsRes = await fetch("http://localhost:8000/api/sentiment/");
    setNews((await newsRes.json()).slice(0, 6));
    setLastUpdated(new Date());
    setRefreshing(false);
  };

  return (
    <>
      <style>{CSS}</style>
      <div className="app">
        <div className="header">
          <div>
            <div className="brand">Himalayan<span>Hawala</span></div>
            <div className="tagline">REMITTANCE INTELLIGENCE · NEPAL</div>
          </div>
          <div className="header-meta">NRB Official Data</div>
        </div>

        {/* Currency selector */}
        <div className="currency-bar">
          {currencies.map(c => (
            <button
              key={c}
              className={`currency-btn${c === currency ? ' active' : ''}`}
              onClick={() => setCurrency(c)}
            >{c}</button>
          ))}
        </div>

        {/* Top metrics row */}
        <div className="metrics-row">
          <div className="metric-card">
            <div className="metric-label">{currency} / NPR · LIVE</div>
            <div className="metric-value gold">{liveRate ? liveRate.mid_rate : "—"}</div>
            <div className="metric-sub">Buy {liveRate?.buy_rate} · Sell {liveRate?.sell_rate}</div>
          </div>

          <div className="metric-card">
            <div className="metric-label">7-DAY PROJECTED CHANGE</div>
            <div className="metric-value">{trend ? `${trend > 0 ? '+' : ''}${trend.toFixed(2)}` : "—"}</div>
            <div className={`metric-delta ${trend < 0 ? "down" : "up"}`}>
              {trend < 0 ? "\u2193 Falling" : "\u2191 Rising"}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">MARKET SIGNAL</div>
            <div className="metric-value" style={{
              color: trend > 0 ? "var(--trading-up)" :
                     trend < 0 ? "var(--trading-down)" : "var(--muted-strong)",
              fontSize: 22
            }}>
              {trend > 0 ? "BULLISH" : trend < 0 ? "BEARISH" : "NEUTRAL"}
            </div>
            <div className="metric-sub">{currency}/NPR forecast</div>
          </div>
        </div>

        {/* Main chart + alert panel */}
        <div className="main-row">
          <div className="panel">
            <div className="panel-header">
              <div>
                <div className="panel-title">{currency}/NPR Rate</div>
                <div className="panel-sub">90-day history + 7-day forecast</div>
              </div>
            </div>
            <div className="chart-legend">
              <span><i className="legend-line solid" /> Actual</span>
              <span><i className="legend-line dashed" /> Forecast</span>
              <span><i className="legend-band" /> Confidence</span>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="2 4" stroke="#2b3139" />
                <XAxis dataKey="date" stroke="#707a8a" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono' }} />
                <YAxis stroke="#707a8a" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono' }} domain={['auto', 'auto']} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="high" stroke="none" fill="#FCD535" fillOpacity={0.08} />
                <Area type="monotone" dataKey="low" stroke="none" fill="#FCD535" fillOpacity={0.08} />
                <Line type="monotone" dataKey="actual" stroke="#FCD535" strokeWidth={2} dot={false} connectNulls={false} />
                <Line type="monotone" dataKey="predicted" stroke="#0ecb81" strokeWidth={2} strokeDasharray="5 3" dot={{ r: 3, fill: '#0ecb81' }} connectNulls />
                <Line type="monotone" dataKey="high" stroke="transparent" strokeWidth={0} dot={false} />
                <Line type="monotone" dataKey="low" stroke="transparent" strokeWidth={0} dot={false} />
                <ReferenceLine
                  x={predictions.length > 0 ? predictions[0].predicted_for.slice(5) : ''}
                  stroke="#2b3139" strokeWidth={1} strokeDasharray="3 3"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <div className="panel-title">Smart Alert</div>
                <div className="panel-sub">AI-generated guidance</div>
              </div>
            </div>
            <div className="alert-panel-body">
              {loadingAlert && <div style={{ color: "var(--muted)", fontSize: 11 }}>Generating alert...</div>}
              {alert && !loadingAlert && <div className="alert-box">{alert.alert}</div>}
              {!alert && !loadingAlert && (
                <div className="alert-placeholder">Select a currency above to see AI-generated guidance.</div>
              )}
            </div>
          </div>
        </div>

        {/* News feed */}
        <div className="feed-panel">
          <div className="feed-header">
            <div>
              <div className="panel-title">Financial News Sentiment</div>
              {lastUpdated && <div className="last-updated">Last updated {lastUpdated.toLocaleTimeString()}</div>}
            </div>
            <button className="refresh-btn" onClick={refreshNews} disabled={refreshing}>
              {refreshing ? "Refreshing..." : "Refresh News"}
            </button>
          </div>
          {news.map((item, i) => (
            <div className="news-row" key={i}>
              <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>
                <div style={{ cursor: 'pointer' }}>{item.headline}</div>
              </a>
              <div className="news-meta">
                <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)', textDecoration: 'none', fontSize: 11, fontWeight: 600 }}>{item.source} ↗</a>
                <span className={`pill ${item.sentiment}`}>{item.sentiment}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}