"use client";
import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Area, ReferenceLine
} from "recharts";

const isValidUrl = (string) => {
  try {
    const url = new URL(string);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="tooltip-box">
        <div className="t-label">{label}</div>
        <div className="t-value">{payload[0]?.value?.toFixed(2)} NPR</div>
      </div>
    );
  }
  return null;
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [currency, setCurrency] = useState("USD");
  const [currencies, setCurrencies] = useState([]);
  const [liveRate, setLiveRate] = useState(null);
  const [history, setHistory] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [news, setNews] = useState([]);
  const [alert, setAlert] = useState(null);
  const [backtest, setBacktest] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/rates/currencies`).then(r => r.json()).then(setCurrencies).catch(err => console.error("[API]", err));
    fetch(`${API}/api/sentiment/`).then(r => r.json()).then(d => {
      setNews(d.slice(0, 6));
      setLastUpdated(new Date());
    }).catch(err => console.error("[API]", err));
  }, []);

  useEffect(() => {
    const c = encodeURIComponent(currency);
    fetch(`${API}/api/rates/live?currency=${c}`).then(r => r.json()).then(setLiveRate).catch(err => console.error("[API]", err));
    fetch(`${API}/api/rates/history?currency=${c}&days=90`).then(r => r.json()).then(setHistory).catch(err => console.error("[API]", err));
    fetch(`${API}/api/predict/?currency=${c}`).then(r => r.json()).then(setPredictions).catch(err => console.error("[API]", err));
    fetch(`${API}/api/alerts/generate?currency=${c}&lang=en`).then(r => {
      if (r.status === 429) return null;
      if (!r.ok) throw new Error(r.statusText);
      return r.json();
    }).then(d => { if (d) setAlert(d); }).catch(err => console.error("[API]", err));
    fetch(`${API}/api/predict/backtest?currency=${c}`).then(r => r.json()).then(setBacktest).catch(err => console.error("[API]", err));
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
    await fetch(`${API}/api/sentiment/refresh`, { method: "POST" });
    const newsRes = await fetch(`${API}/api/sentiment/`);
    setNews((await newsRes.json()).slice(0, 6));
    setLastUpdated(new Date());
    setRefreshing(false);
  };

  return (
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
            <div className="metric-value gold">{liveRate ? parseFloat(liveRate.mid_rate).toFixed(2) : "—"}</div>
            <div className="metric-sub">Buy {liveRate ? parseFloat(liveRate.buy_rate).toFixed(2) : "—"} · Sell {liveRate ? parseFloat(liveRate.sell_rate).toFixed(2) : "—"}</div>
            <div className="metric-sub" style={{ marginTop: 6, fontSize: 11 }}>{liveRate ? new Date(liveRate.recorded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ""}</div>
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

        {/* Chart */}
        <div className="chart-section">
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
            <div className="chart-wrap">
              {chartData.length > 0 ? (
                <ResponsiveContainer key={currency} width="100%" height={380}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="2 4" stroke="#2b3139" />
                    <XAxis dataKey="date" stroke="#707a8a" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono' }} />
                    <YAxis stroke="#707a8a" tick={{ fontSize: 10, fontFamily: 'JetBrains Mono' }} domain={['auto', 'auto']} tickFormatter={(v) => v.toFixed(2)} />
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
              ) : (
                <div className="chart-placeholder">Loading chart data...</div>
              )}
            </div>
          </div>

          {/* Smart Alert */}
          <div className="panel" style={{ marginTop: 16 }}>
            <div className="panel-header">
              <div>
                <div className="panel-title">Smart Alert</div>
                <div className="panel-sub">AI-generated guidance for {currency}</div>
              </div>
            </div>
            {alert ? (
              <div className="alert-box">{alert.alert}</div>
            ) : (
              <div className="alert-placeholder">Select a currency above to see AI-generated guidance.</div>
            )}
          </div>
        </div>

        {/* Model Backtest */}
        <div className="panel" style={{ marginTop: 16 }}>
          <div className="panel-header">
            <div>
              <div className="panel-title">Model Backtest · {currency}</div>
              <div className="panel-sub">Predicted vs actual rate accuracy</div>
            </div>
          </div>

          {backtest && backtest.count > 0 ? (
            <>
              <div className="backtest-stats">
                <div className="backtest-stat">
                  <div className="backtest-stat-value">{backtest.mae.toFixed(2)}</div>
                  <div className="backtest-stat-label">Avg Error (NPR)</div>
                </div>
                <div className="backtest-stat">
                  <div className="backtest-stat-value" style={{ color: backtest.direction_accuracy >= 50 ? 'var(--trading-up)' : 'var(--trading-down)' }}>
                    {backtest.direction_accuracy}%
                  </div>
                  <div className="backtest-stat-label">Direction Accuracy</div>
                </div>
                <div className="backtest-stat">
                  <div className="backtest-stat-value">{backtest.count}</div>
                  <div className="backtest-stat-label">Matched Predictions</div>
                </div>
                <div className="backtest-stat">
                  <div className="backtest-stat-value" style={{ color: backtest.simulated_gain_npr >= 0 ? 'var(--trading-up)' : 'var(--trading-down)' }}>
                    {backtest.simulated_gain_npr > 0 ? '+' : ''}{backtest.simulated_gain_npr.toFixed(2)}
                  </div>
                  <div className="backtest-stat-label">Simulated Gain (NPR)</div>
                </div>
              </div>

              <div className="backtest-table-wrap">
                <table className="backtest-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Predicted</th>
                      <th>Actual</th>
                      <th>Error</th>
                      <th>Error %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {backtest.results.slice(0, 10).map((r, i) => (
                      <tr key={i}>
                        <td>{r.date}</td>
                        <td>{r.predicted.toFixed(2)}</td>
                        <td>{r.actual.toFixed(2)}</td>
                        <td style={{ color: r.error > 0 ? 'var(--trading-up)' : r.error < 0 ? 'var(--trading-down)' : 'inherit' }}>
                          {r.error > 0 ? '+' : ''}{r.error.toFixed(2)}
                        </td>
                        <td>{r.error_pct.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="backtest-empty">
              Predictions need time to mature into actual rates before backtesting data is available.
            </div>
          )}
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
              {isValidUrl(item.url) ? (
                <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>
                  <div style={{ cursor: 'pointer' }}>{item.headline}</div>
                </a>
              ) : (
                <div style={{ color: 'inherit' }}>{item.headline}</div>
              )}
              <div className="news-meta">
                {isValidUrl(item.url) ? (
                  <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)', textDecoration: 'none', fontSize: 11, fontWeight: 600 }}>{item.source} ↗</a>
                ) : (
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted-strong)' }}>{item.source}</span>
                )}
                <span className={`pill ${item.sentiment}`}>{item.sentiment}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
  );
}