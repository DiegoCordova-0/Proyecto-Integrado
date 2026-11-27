const formulaPrefix = /^[\t\r\n ]*[=+\-@]/

function encodeCell(value) {
  let text = value == null ? '' : String(value)
  if (typeof value === 'string' && formulaPrefix.test(text)) text = `'${text}`
  return `"${text.replace(/"/g, '""')}"`
}

export function downloadCsv(filename, headers, rows) {
  const content = [headers, ...rows]
    .map((row) => row.map(encodeCell).join(','))
    .join('\r\n')
  const blob = new Blob(['\uFEFF', content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
