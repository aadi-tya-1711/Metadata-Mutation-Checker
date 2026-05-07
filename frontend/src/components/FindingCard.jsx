import React, { useMemo, useState } from 'react';

export default function FindingCard({ finding, explanationMode = 'technical' }) {
  const [open, setOpen] = useState(false);
  const sev = (finding.severity || '').toLowerCase();
  const conf = Math.round((finding.confidence ?? 0) * 100);
  const explanation = useMemo(() => {
    if (explanationMode === 'simple') {
      return finding.simple_explanation || finding.explanation;
    }
    return finding.technical_explanation || finding.explanation;
  }, [finding, explanationMode]);

  const evidence = finding.evidence || {};
  const hasEvidence = Object.keys(evidence).length > 0;

  return (
    <article className={`finding finding--${sev}`}>
      <header className="finding__header">
        <div className="finding__title">{finding.title}</div>
        <div className="finding__badges">
          <span className={`badge badge--${sev}`}>{finding.severity}</span>
          <span className="badge badge--ghost">{conf}% confidence</span>
        </div>
      </header>
      <p className="finding__explanation">{explanation}</p>
      {hasEvidence && (
        <div className="finding__evidence">
          <button
            type="button"
            className="finding__toggle"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
          >
            {open ? 'Hide evidence' : 'Show evidence'}
          </button>
          {open && (
            <pre className="finding__pre">
              {JSON.stringify(evidence, null, 2)}
            </pre>
          )}
        </div>
      )}
    </article>
  );
}
