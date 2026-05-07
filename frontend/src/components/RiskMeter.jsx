import React from 'react';

const SIZE = 200;
const STROKE = 16;
const RADIUS = (SIZE - STROKE) / 2;

function levelColor(level) {
  switch (level) {
    case 'High':
      return '#ef4444';
    case 'Medium':
      return '#f59e0b';
    default:
      return '#10b981';
  }
}

export default function RiskMeter({ score, level }) {
  const pct = Math.max(0, Math.min(100, score)) / 100;
  // Tiny non-zero values can look like a blob with round caps; ensure
  // a small visible segment while preserving 0 as empty.
  const progressPct = pct === 0 ? 0 : Math.max(2.2, pct * 100);
  const color = levelColor(level);

  return (
    <div className="meter">
      <svg
        width={SIZE}
        height={SIZE / 2 + STROKE}
        viewBox={`0 0 ${SIZE} ${SIZE / 2 + STROKE}`}
        className="meter__svg"
        role="img"
        aria-label={`Risk score ${score} out of 100, ${level}`}
      >
        <path
          d={`M ${STROKE / 2} ${SIZE / 2} A ${RADIUS} ${RADIUS} 0 0 1 ${
            SIZE - STROKE / 2
          } ${SIZE / 2}`}
          stroke="rgba(15,23,42,0.14)"
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="round"
          pathLength="100"
        />
        <path
          d={`M ${STROKE / 2} ${SIZE / 2} A ${RADIUS} ${RADIUS} 0 0 1 ${
            SIZE - STROKE / 2
          } ${SIZE / 2}`}
          stroke={color}
          strokeWidth={STROKE}
          fill="none"
          strokeLinecap="butt"
          pathLength="100"
          strokeDasharray={`${progressPct} 100`}
          style={{ transition: 'stroke-dasharray 0.6s ease, stroke 0.3s ease' }}
        />
      </svg>
      <div className="meter__readout">
        <div className="meter__score" style={{ color }}>
          {score}
        </div>
        <div className="meter__suffix">/ 100</div>
        <div className={`meter__level meter__level--${level?.toLowerCase()}`}>
          {level} risk
        </div>
      </div>
    </div>
  );
}
