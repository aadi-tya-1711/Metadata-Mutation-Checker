import React from 'react';

const PRIMARY_FIELDS = [
  ['file_name', 'File name'],
  ['file_size_human', 'File size'],
  ['file_type', 'File type'],
  ['pdf_version', 'PDF version'],
  ['page_count', 'Page count'],
  ['encrypted', 'Encrypted'],
  ['title', 'Title'],
  ['author', 'Author'],
  ['subject', 'Subject'],
  ['keywords', 'Keywords'],
  ['creator', 'Creator'],
  ['producer', 'Producer'],
  ['created_at', 'Created'],
  ['modified_at', 'Modified'],
  ['has_xmp', 'XMP packet'],
  ['xmp_creator_tool', 'XMP creator tool'],
  ['xmp_producer', 'XMP producer'],
  ['xmp_create_date', 'XMP create date'],
  ['xmp_modify_date', 'XMP modify date'],
  ['incremental_updates', 'Incremental updates'],
];

function formatValue(v) {
  if (v === null || v === undefined || v === '') return '—';
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  return String(v);
}

export default function MetadataTable({ metadata }) {
  if (!metadata) return null;

  return (
    <div className="card">
      <div className="card__title">Extracted metadata</div>
      <div className="meta-table-wrap">
        <table className="meta-table">
          <tbody>
            {PRIMARY_FIELDS.map(([key, label]) => (
              <tr key={key}>
                <th scope="row">{label}</th>
                <td>
                  <span className={metadata[key] == null ? 'muted' : ''}>
                    {formatValue(metadata[key])}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
