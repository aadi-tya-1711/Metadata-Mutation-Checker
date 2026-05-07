import React, { useCallback, useRef, useState } from 'react';

const ACCEPT = '.pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png';

export default function FileUpload({ onFile, disabled }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setDragOver(false);
      if (disabled) return;
      const f = e.dataTransfer.files?.[0];
      if (f) onFile(f);
    },
    [disabled, onFile]
  );

  const onDragOver = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled) setDragOver(true);
    },
    [disabled]
  );

  const onDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const onClick = () => {
    if (!disabled) inputRef.current?.click();
  };

  const onChange = (e) => {
    const f = e.target.files?.[0];
    if (f) onFile(f);
    e.target.value = '';
  };

  return (
    <div
      className={`dropzone${dragOver ? ' dropzone--over' : ''}${
        disabled ? ' dropzone--disabled' : ''
      }`}
      onClick={onClick}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        onChange={onChange}
        hidden
      />
      <div className="dropzone__icon" aria-hidden>
        <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
          <rect
            x="12"
            y="6"
            width="40"
            height="52"
            rx="6"
            stroke="currentColor"
            strokeWidth="2.5"
          />
          <path
            d="M22 28h20M22 36h20M22 44h12"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <div className="dropzone__title">
        Drop a PDF here, or <span className="link">browse</span>
      </div>
      <div className="dropzone__hint">
        PDFs are analysed for metadata anomalies. JPG/PNG also supported (EXIF).
      </div>
    </div>
  );
}
