import React, { useMemo } from 'react';
import RiskMeter from './RiskMeter.jsx';
import MetadataTable from './MetadataTable.jsx';
import FindingCard from './FindingCard.jsx';

function downloadJSON(report) {
  const blob = new Blob([JSON.stringify(report, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const safeName =
    (report.document_name || 'report').replace(/\.[^/.]+$/, '') || 'report';
  a.href = url;
  a.download = `${safeName}-metadata-report.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

const SEVERITY_ORDER = { High: 0, Medium: 1, Low: 2 };

export default function Report({ report, onReset }) {
  const [explanationMode, setExplanationMode] = React.useState('technical');
  const sortedFindings = useMemo(() => {
    return [...(report.findings || [])].sort((a, b) => {
      const s = (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3);
      if (s !== 0) return s;
      return (b.confidence ?? 0) - (a.confidence ?? 0);
    });
  }, [report]);

  const counts = useMemo(() => {
    const c = { High: 0, Medium: 0, Low: 0 };
    for (const f of report.findings || []) {
      if (c[f.severity] !== undefined) c[f.severity] += 1;
    }
    return c;
  }, [report]);

  return (
    <section className="report">
      <div className="report__top">
        <div className="report__left">
          <button className="btn btn--ghost report__back" onClick={onReset}>
            Back to Dashboard
          </button>
          <div className="report__heading">
            <div className="report__eyebrow">Forensics report</div>
            <h2 className="report__title">{report.document_name}</h2>
            <div className="report__filetype">{report.file_type}</div>
          </div>
        </div>
        <div className="report__actions">
          <div className="mode-toggle">
            <button
              className={`btn btn--ghost ${explanationMode === 'simple' ? 'is-active' : ''}`}
              onClick={() => setExplanationMode('simple')}
            >
              Simple explanation
            </button>
            <button
              className={`btn btn--ghost ${explanationMode === 'technical' ? 'is-active' : ''}`}
              onClick={() => setExplanationMode('technical')}
            >
              Technical explanation
            </button>
          </div>
          <button
            className="btn btn--primary"
            onClick={() => downloadJSON(report)}
          >
            Download JSON
          </button>
          <button
            className="btn btn--ghost"
            onClick={() => downloadSummaryAsPdf(report)}
          >
            PDF-style summary
          </button>
        </div>
      </div>

      <div className="report__summary-grid">
        <div className="card card--meter">
          <div className="card__title">Metadata risk score</div>
          <RiskMeter
            score={report.metadata_risk_score}
            level={report.metadata_risk_level}
          />
          <div className="legend">
            <span className="legend__chip legend__chip--low">Low 0–30</span>
            <span className="legend__chip legend__chip--medium">Medium 31–65</span>
            <span className="legend__chip legend__chip--high">High 66–100</span>
          </div>
        </div>
        <div className="card card--summary">
          <div className="card__title">Summary</div>
          <p className="card__body">{report.summary}</p>
          <div className="counts">
            <div className="counts__item counts__item--high">
              <strong>{counts.High}</strong> High
            </div>
            <div className="counts__item counts__item--medium">
              <strong>{counts.Medium}</strong> Medium
            </div>
            <div className="counts__item counts__item--low">
              <strong>{counts.Low}</strong> Low
            </div>
          </div>
          <div className="card__title card__title--sub">Recommended action</div>
          <p className="card__body">{report.recommended_action}</p>
        </div>
      </div>

      <div className="report__columns">
        <div>
          <MetadataTable metadata={report.extracted_metadata} />
          <div className="card">
            <div className="card__title">Raw metadata (machine view)</div>
            <pre className="raw-block">
              {JSON.stringify(report.extracted_metadata?.raw_info || {}, null, 2)}
            </pre>
          </div>
        </div>
        <div>
          <div className="card">
            <div className="card__title">
              Interpreted findings ({explanationMode} mode){' '}
              <span className="muted">
                ({sortedFindings.length}{' '}
                {sortedFindings.length === 1 ? 'item' : 'items'})
              </span>
            </div>
            {sortedFindings.length === 0 ? (
              <p className="muted">
                No rule-based observations were triggered for this document.
              </p>
            ) : (
              <div className="findings">
                {sortedFindings.map((f) => (
                  <FindingCard
                    key={f.id}
                    finding={f}
                    explanationMode={explanationMode}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <footer className="disclaimer">
        These observations are signals for review, not conclusions about
        authenticity. Metadata can be missing, stripped, or altered for
        legitimate reasons; any decision should consider the full context of
        the document.
      </footer>
    </section>
  );
}

function downloadSummaryAsPdf(report) {
  const popup = window.open('', '_blank', 'width=900,height=700');
  if (!popup) return;
  const findings = (report.findings || [])
    .map(
      (f) =>
        `<li><strong>${escapeHtml(f.title)}</strong> (${escapeHtml(
          f.severity
        )}, ${(f.confidence * 100).toFixed(0)}%)<br/>${escapeHtml(
          f.simple_explanation || f.explanation
        )}</li>`
    )
    .join('');

  popup.document.write(`
    <html><head><title>${escapeHtml(report.document_name)} - Summary</title>
    <style>
      body{font-family:Arial,sans-serif;padding:28px;color:#0f172a}
      h1{margin:0 0 6px} .muted{color:#475569}
      .card{border:1px solid #cbd5e1;border-radius:8px;padding:14px;margin:14px 0}
      ul{padding-left:18px} li{margin-bottom:10px;line-height:1.45}
    </style></head><body>
      <h1>Document Metadata Summary</h1>
      <div class="muted">${escapeHtml(report.document_name)} · ${escapeHtml(
    report.file_type
  )}</div>
      <div class="card"><strong>Risk:</strong> ${report.metadata_risk_score}/100 (${escapeHtml(
    report.metadata_risk_level
  )})<br/><br/>${escapeHtml(report.summary)}</div>
      <div class="card"><strong>Recommended action:</strong><br/>${escapeHtml(
    report.recommended_action
  )}</div>
      <div class="card"><strong>Findings</strong><ul>${findings || '<li>No findings.</li>'}</ul></div>
      <div class="muted">This summary surfaces metadata inconsistencies responsibly; it does not prove tampering.</div>
    </body></html>
  `);
  popup.document.close();
  popup.focus();
  popup.print();
}

function escapeHtml(s) {
  return String(s ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}
