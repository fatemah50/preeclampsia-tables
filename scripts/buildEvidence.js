import fs from 'fs/promises'
import path from 'path'

const root = path.resolve(process.cwd())
const csvDir = path.join(root, 'csv preexclamsia')
const outDir = path.join(root, 'src', 'data')
const outFile = path.join(outDir, 'evidence.json')

const parseCsv = (csvText) => {
  const lines = csvText.split(/\r?\n/).filter((line) => line.trim() !== '')
  if (!lines.length) return { headers: [], rows: [] }

  const parseRow = (line) => {
    const values = []
    let current = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i += 1) {
      const char = line[i]
      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') {
          current += '"'
          i += 1
        } else {
          inQuotes = !inQuotes
        }
      } else if (char === ',' && !inQuotes) {
        values.push(current)
        current = ''
      } else {
        current += char
      }
    }
    values.push(current)
    return values.map((value) => value.trim())
  }

  const headers = parseRow(lines[0])
  const rows = lines.slice(1).map((line) => {
    const cells = parseRow(line)
    const row = headers.reduce((acc, header, index) => {
      acc[header] = cells[index] ?? ''
      return acc
    }, {})
    row.__rowText = Object.values(row).join(' | ').toLowerCase()
    return row
  })

  return { headers, rows }
}

const buildEvidence = async () => {
  try {
    const files = await fs.readdir(csvDir)
    const csvFiles = files.filter((name) => name.toLowerCase().endsWith('.csv'))
    await fs.mkdir(outDir, { recursive: true })

    const evidence = []
    for (const filename of csvFiles.sort()) {
      const filePath = path.join(csvDir, filename)
      const rawText = await fs.readFile(filePath, 'utf8')
      const { headers, rows } = parseCsv(rawText)
      evidence.push({ filename, headers, rows })
    }

    await fs.writeFile(outFile, JSON.stringify({ generatedAt: new Date().toISOString(), sourceCount: evidence.length, evidence }, null, 2), 'utf8')
    console.log(`Generated evidence JSON with ${evidence.length} CSV files at ${outFile}`)
  } catch (error) {
    console.error('Failed to build evidence data:', error)
    process.exit(1)
  }
}

buildEvidence()
