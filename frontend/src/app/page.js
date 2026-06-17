"use client";
import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts";

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@300;400&display=swap');

  :root {
    --navy: #080F1E;
    --navy-2: #0D1829;
    --navy-3: #152238;
    --gold: #C9A84C;
    --gold-dim: #8A6D2F;
    --white: #F0EDE6;
    --muted: #6B7A94;
    --positive: #4A9D6F;
    --negative: #9D4A4A;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--navy);
    color: var(--white);
    font-family: 'DM Mono', monospace;
  }

  .app { min-height: 100vh; padding: 48px; max-width: 1200px; margin: 0 auto; }

  .header { border-bottom: 1px solid var(--gold-dim); padding-bottom: 24px; margin-bottom: 48px; }

  .brand {
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    letter-spacing: -0.5px;
    color: var(--white);
  }

  .brand span { color: var(--gold); }

  .tagline { color: var(--muted); font-size: 11px; letter-spacing: 3px; text-transform: uppercase; margin-top: 4px; }

  .grid { display: grid; grid-template-columns: 300px 1fr; gap: 24px; margin-bottom: 24px; }

  .card {
    background: var(--navy-2);
    border: 1px solid var(--navy-3);
    border-top: 2px solid var(--gold);
    padding: 28px;
  }

  .card-label { font-size: 10px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; }

  .rate-big {
    font-family: 'DM Mono', monospace;
    font-size: 52px;
    font-weight: 300;
    color: var(--gold);
    line-height: 1;
    letter-spacing: -2px;
  }

  .rate-sub { display: flex; gap: 24px; margin-top: 12px; font-size: 11px; color: var(--muted); }

  .rate-sub span { color: var(--white); }

  .as-of { font-size: 10px; color: var(--muted); margin-top: 16px; border-top: 1px solid var(--navy-3); padding-top: 12px; }

  .signal {
    margin-top: 20px;
    padding: 12px;
    background: var(--navy-3);
    font-size: 11px;
    color: var(--muted);
    line-height: 1.6;
  }

  .signal strong { color: var(--gold); }

  .chart-card {
    background: var(--navy-2);
    border: 1px solid var(--navy-3);
    border-top: 2px solid var(--gold-dim);
    padding: 28px;
  }

  .chart-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }

  .chart-title { font-family: 'DM Serif Display', serif; font-size: 18px; color: var(--white); }

  .chart-sub { font-size: 10px; color: var(--muted); letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }

  .badge {
    font-size: 9px;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 4px 10px;
    border: 1px solid var(--gold-dim);
    color: var(--gold);
  }

  .custom-tooltip {
    background: var(--navy-3);
    border: 1px solid var(--gold-dim);
    padding: 12px 16px;
    font-size: 11px;
  }

  .custom-tooltip .label { color: var(--muted); margin-bottom: 4px; font-size: 10px; letter-spacing: 1px; }
  .custom-tooltip .value { color: var(--gold); font-size: 16px; }

  .table-card {
    background: var(--navy-2);
    border: 1px solid var(--navy-3);
    padding: 28px;
  }

  .table-title { font-family: 'DM Serif Display', serif; font-size: 18px; margin-bottom: 20px; }

  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { text-align: left; color: var(--muted); font-size: 10px; letter-spacing: 2px; text-transform: uppercase; padding: 8px 0; border-bottom: 1px solid var(--navy-3); font-weight: 400; }
  td { padding: 12px 0; border-bottom: 1px solid var(--navy-3); color: var(--white); }
  tr:last-child td { border-bottom: none; }

  .up { color: var(--positive); }
  .down { color: var(--negative); }
`;

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <div className="label">{label}</div>
        <div className="value">{payload[0]?.value?.toFixed(4)} NPR</div>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [liveRate, setLiveRate] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [transfers, setTransfers] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/rates/live").then(r => r.json()).then(setLiveRate);
    fetch("http://localhost:8000/api/predict/").then(r => r.json()).then(setPredictions);
    fetch("http://localhost:8000/api/transfers/Ramesh Thapa").then(r => r.json()).then(d => setTransfers(d.slice(0, 6)));
  }, []);

  const chartData = predictions.map(p => ({
    date: p.predicted_for.slice(5),
    predicted: parseFloat(p.predicted_rate),
    low: parseFloat(p.confidence_low),
    high: parseFloat(p.confidence_high),
  }));

  const trend = predictions.length >= 2
    ? predictions[predictions.length - 1].predicted_rate - predictions[0].predicted_rate
    : 0;

  return (
    <>
      <style>{CSS}</style>
      <div className="app">
        <header className="header">
          <div className="brand">Himalayan<span>Hawala</span></div>
          <div className="tagline">Remittance Intelligence · Nepal</div>
        </header>

        <div className="grid">
          {/* Live Rate */}
          <div className="card">
            <div className="card-label">USD / NPR · Live</div>
            {liveRate ? (
              <>
                <div className="rate-big">{liveRate.mid_rate}</div>
                <div className="rate-sub">
                  <div>BUY <span>{liveRate.buy_rate}</span></div>
                  <div>SELL <span>{liveRate.sell_rate}</span></div>
                </div>
                <div className="as-of">NRB Official · {new Date(liveRate.recorded_at).toLocaleDateString('en-GB')}</div>
                <div className="signal">
                  <strong>7-DAY SIGNAL</strong><br />
                  {trend < 0
                    ? `Rate projected to fall ${Math.abs(trend).toFixed(2)} NPR. Favorable window to receive.`
                    : `Rate projected to rise ${trend.toFixed(2)} NPR. Consider sending soon.`}
                </div>
              </>
            ) : <div style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</div>}
          </div>

          {/* Chart */}
          <div className="chart-card">
            <div className="chart-header">
              <div>
                <div className="chart-title">7-Day Rate Forecast</div>
                <div className="chart-sub">Random Forest · MAE 0.59 NPR</div>
              </div>
              <div className="badge">AI Prediction</div>
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="2 4" stroke="#152238" />
                <XAxis dataKey="date" stroke="#6B7A94" tick={{ fontSize: 10, fontFamily: 'DM Mono' }} />
                <YAxis stroke="#6B7A94" tick={{ fontSize: 10, fontFamily: 'DM Mono' }} domain={['auto', 'auto']} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="high" stroke="#8A6D2F" strokeDasharray="3 3" dot={false} strokeWidth={1} />
                <Line type="monotone" dataKey="predicted" stroke="#C9A84C" strokeWidth={2} dot={{ r: 3, fill: '#C9A84C' }} />
                <Line type="monotone" dataKey="low" stroke="#8A6D2F" strokeDasharray="3 3" dot={false} strokeWidth={1} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Transfer History */}
        <div className="table-card">
          <div className="table-title">Transfer History</div>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Sender</th>
                <th>Recipient</th>
                <th>USD</th>
                <th>NPR</th>
                <th>Rate</th>
                <th>Purpose</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {transfers.map(t => (
                <tr key={t.id}>
                  <td>{new Date(t.transferred_at).toLocaleDateString('en-GB')}</td>
                  <td>{t.sender_name}</td>
                  <td>{t.recipient_name}</td>
                  <td>${t.amount_usd}</td>
                  <td>₨{t.amount_npr.toLocaleString()}</td>
                  <td>{t.rate_at_send}</td>
                  <td style={{ textTransform: 'capitalize' }}>{t.purpose}</td>
                  <td className={t.status === 'completed' ? 'up' : 'down'}>{t.status.toUpperCase()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}