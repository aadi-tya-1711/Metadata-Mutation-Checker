import React, { useState } from 'react';
import FileUpload from './components/FileUpload.jsx';
import Report from './components/Report.jsx';
import CompareReport from './components/CompareReport.jsx';
import { analyzeFile, compareFiles } from './api.js';

export default function App() {
  const [mode, setMode] = useState('single');
  const [report, setReport] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState(null);
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);

  const handleFile = async (file) => {
    setError(null);
    setReport(null);
    setComparison(null);
    setFileName(file.name);
    setLoading(true);
    try {
      const data = await analyzeFile(file);
      setReport(data);
    } catch (e) {
      setError(e.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setReport(null);
    setComparison(null);
    setError(null);
    setFileName(null);
    setFileA(null);
    setFileB(null);
  };

  const runCompare = async () => {
    if (!fileA || !fileB) return;
    setError(null);
    setReport(null);
    setComparison(null);
    setLoading(true);
    try {
      const data = await compareFiles(fileA, fileB);
      setComparison(data);
    } catch (e) {
      setError(e.message || 'Comparison failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app__header">
        <div className="brand">
          <div className="brand__logo" aria-hidden>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
              <path
                d="M12 2 4 6v6c0 5 3.4 9.2 8 10 4.6-.8 8-5 8-10V6l-8-4z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinejoin="round"
              />
              <path
                d="m9 12 2 2 4-4"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <div className="brand__name">Metadata Mutation Checker</div>
            <div className="brand__tag">
              Responsible PDF metadata forensics
            </div>
          </div>
        </div>
      </header>

      <main className="app__main">
        {!report && (
          <section className="hero">
            <h1 className="hero__title">
              Surface metadata inconsistencies, responsibly.
            </h1>
            <p className="hero__subtitle">
              Upload a PDF to extract its metadata and run a battery of
              rule-based checks. The result is a transparent report of
              observations — never an accusation of tampering.
            </p>

            <div className="mode-toggle mode-toggle--main">
              <button
                className={`btn btn--ghost ${mode === 'single' ? 'is-active' : ''}`}
                onClick={() => setMode('single')}
              >
                Single file analysis
              </button>
              <button
                className={`btn btn--ghost ${mode === 'compare' ? 'is-active' : ''}`}
                onClick={() => setMode('compare')}
              >
                Compare two files
              </button>
            </div>

            {mode === 'single' ? (
              <FileUpload onFile={handleFile} disabled={loading} />
            ) : (
              <div className="compare-uploader">
                <label className="compare-field">
                  <span>File A</span>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                    onChange={(e) => setFileA(e.target.files?.[0] || null)}
                    disabled={loading}
                  />
                </label>
                <label className="compare-field">
                  <span>File B</span>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                    onChange={(e) => setFileB(e.target.files?.[0] || null)}
                    disabled={loading}
                  />
                </label>
                <button
                  className="btn btn--primary"
                  onClick={runCompare}
                  disabled={loading || !fileA || !fileB}
                >
                  Compare metadata
                </button>
              </div>
            )}

            {loading && (
              <div className="status status--loading">
                <span className="spinner" />
                {mode === 'single' ? (
                  <>
                    Analysing <strong>{fileName}</strong>…
                  </>
                ) : (
                  <>Comparing selected files…</>
                )}
              </div>
            )}
            {error && !loading && (
              <div className="status status--error">
                <strong>Could not analyse file.</strong>
                <div>{error}</div>
              </div>
            )}

            <div className="features">
              <Feature
                title="Date anomaly checks"
                desc="Missing dates, modified-before-created, large gaps."
              />
              <Feature
                title="Editor fingerprinting"
                desc="Detects Acrobat, Photoshop, Canva, online editors and more."
              />
              <Feature
                title="XMP cross-checks"
                desc="Compares the XMP packet against the document info dictionary."
              />
              <Feature
                title="Hedged language"
                desc="Findings use careful, non-accusatory wording with confidence scores."
              />
            </div>
          </section>
        )}

        {report && <Report report={report} onReset={reset} />}
        {comparison && <CompareReport comparison={comparison} onReset={reset} />}
      </main>

      <footer className="app__footer">
        <span>
          Built with FastAPI + React • Findings are signals, not verdicts.
        </span>
      </footer>
    </div>
  );
}

function Feature({ title, desc }) {
  return (
    <div className="feature">
      <div className="feature__title">{title}</div>
      <div className="feature__desc">{desc}</div>
    </div>
  );
}
