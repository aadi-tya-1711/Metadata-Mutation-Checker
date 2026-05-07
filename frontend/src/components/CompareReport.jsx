import React from 'react';

function downloadJSON(name, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function CompareReport({ comparison, onReset }) {
  const diffs = comparison.differences || [];
  return (
    <section className="report">
      <div className="report__top">
        <div className="report__heading">
          <div className="report__eyebrow">Comparison report</div>
          <h2 className="report__title">
            {comparison.file_a_report.document_name} vs {comparison.file_b_report.document_name}
          </h2>
          <div className="report__filetype">{comparison.summary}</div>
        </div>
        <div className="report__actions">
          <button className="btn btn--ghost" onClick={onReset}>
            Compare another pair
          </button>
          <button
            className="btn btn--primary"
            onClick={() => downloadJSON('metadata-comparison-report.json', comparison)}
          >
            Download JSON
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card__title">
          Metadata differences <span className="muted">({diffs.length})</span>
        </div>
        {diffs.length === 0 ? (
          <p className="muted">No extracted metadata differences were observed.</p>
        ) : (
          <div className="diff-table-wrap">
            <table className="meta-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>File A</th>
                  <th>File B</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {diffs.map((d) => (
                  <tr key={d.field}>
                    <td>{d.field}</td>
                    <td>{format(d.file_a_value)}</td>
                    <td>{format(d.file_b_value)}</td>
                    <td>{d.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="report__summary-grid">
        <ScoreCard title="File A risk" report={comparison.file_a_report} />
        <ScoreCard title="File B risk" report={comparison.file_b_report} />
      </div>
    </section>
  );
}

function ScoreCard({ title, report }) {
  return (
    <div className="card">
      <div className="card__title">{title}</div>
      <p className="card__body">
        <strong>
          {report.metadata_risk_score}/100 ({report.metadata_risk_level})
        </strong>
      </p>
      <p className="card__body">{report.summary}</p>
    </div>
  );
}

function format(v) {
  if (v === null || v === undefined || v === '') return '—';
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}
