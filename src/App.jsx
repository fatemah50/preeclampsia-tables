import { useMemo, useState } from 'react'
import evidenceData from './data/evidence.json'

const initialForm = {
  maternalAge: '30',
  gestationalWeek: '24',
  bmi: '28',
  sbp: '120',
  dbp: '75',
  parity: 'nulliparous',
  priorPreeclampsia: 'no',
  familyHistory: 'no',
  chronicHypertension: 'no',
  diabetes: 'no',
  chronicKidneyDisease: 'no',
  autoimmuneDisease: 'no',
  multipleGestation: 'no',
  ivfConception: 'no',
  proteinuria: 'unknown'
}

const yesNoOptions = [
  { label: 'No', value: 'no' },
  { label: 'Yes', value: 'yes' }
]

const parityOptions = [
  { label: 'Nulliparous', value: 'nulliparous' },
  { label: 'Multiparous', value: 'multiparous' }
]

const proteinuriaOptions = [
  { label: 'Unknown', value: 'unknown' },
  { label: 'No', value: 'no' },
  { label: 'Yes', value: 'yes' }
]

const systemPrompt = `You are an explainable preeclampsia risk assessment tool built on ACOG and NICE guidelines and peer-reviewed literature ORs. Use these weights:
- Prior preeclampsia: 3 points
- Chronic hypertension: 3 points
- Multiple gestation: 2 points
- Diabetes mellitus: 2 points
- Chronic kidney disease: 2 points
- Autoimmune disease: 2 points
- BMI >= 30: 1 point
- Nulliparity: 1 point
- Age > 35: 1 point
- Age < 20: 1 point
- Family history: 1 point
- IVF conception: 1 point
- Proteinuria present: 2 points
- SBP >= 140 or DBP >= 90: 3 points

Score interpretation: 0-2 Low, 3-4 Moderate, 5+ High risk.

Always respond in exactly this JSON format:
{
  risk_level: Low/Moderate/High,
  score: number,
  top_factors: [array of 3 strings],
  reasoning: string of 2-3 plain language sentences,
  bias_flag: string or null,
  guideline_reference: string citing ACOG or NICE
}`

const riskWeights = {
  priorPreeclampsia: 3,
  chronicHypertension: 3,
  multipleGestation: 2,
  diabetes: 2,
  chronicKidneyDisease: 2,
  autoimmuneDisease: 2,
  bmi30: 1,
  nulliparity: 1,
  ageOver35: 1,
  ageUnder20: 1,
  familyHistory: 1,
  ivfConception: 1,
  proteinuria: 2,
  bloodPressure: 3
}

const factorLabels = {
  priorPreeclampsia: 'Prior preeclampsia',
  chronicHypertension: 'Chronic hypertension',
  multipleGestation: 'Multiple gestation',
  diabetes: 'Diabetes mellitus',
  chronicKidneyDisease: 'Chronic kidney disease',
  autoimmuneDisease: 'Autoimmune disease',
  bmi30: 'BMI ≥ 30',
  nulliparity: 'Nulliparity',
  ageOver35: 'Age > 35',
  ageUnder20: 'Age < 20',
  familyHistory: 'Family history of preeclampsia',
  ivfConception: 'IVF conception',
  proteinuria: 'Proteinuria present',
  bloodPressure: 'Hypertension (SBP ≥ 140 or DBP ≥ 90)'
}

const getLocalRiskAssessment = (form) => {
  const values = {
    priorPreeclampsia: form.priorPreeclampsia === 'yes',
    chronicHypertension: form.chronicHypertension === 'yes',
    multipleGestation: form.multipleGestation === 'yes',
    diabetes: form.diabetes === 'yes',
    chronicKidneyDisease: form.chronicKidneyDisease === 'yes',
    autoimmuneDisease: form.autoimmuneDisease === 'yes',
    nulliparity: form.parity === 'nulliparous',
    familyHistory: form.familyHistory === 'yes',
    ivfConception: form.ivfConception === 'yes',
    proteinuria: form.proteinuria === 'yes',
    ageUnder20: Number(form.maternalAge) < 20,
    ageOver35: Number(form.maternalAge) > 35,
    bmi30: Number(form.bmi) >= 30,
    bloodPressure: Number(form.sbp) >= 140 || Number(form.dbp) >= 90
  }

  const score = Object.entries(values).reduce((sum, [key, active]) => sum + (active ? riskWeights[key] : 0), 0)
  const risk_level = score >= 5 ? 'High' : score >= 3 ? 'Moderate' : 'Low'
  const major_factors = Object.keys(values)
    .filter((key) => values[key])
    .map((key) => factorLabels[key])
    .slice(0, 3)
  return { score, risk_level, major_factors, majorRisk: score >= 5, values }
}

const getEvidenceMatches = (form) => {
  const activeTerms = []
  const addTerm = (term) => activeTerms.push(term.toLowerCase())

  if (form.priorPreeclampsia === 'yes') addTerm('preeclampsia')
  if (form.chronicHypertension === 'yes') addTerm('hypertension')
  if (form.multipleGestation === 'yes') addTerm('multiple gestation')
  if (form.diabetes === 'yes') addTerm('diabetes')
  if (form.chronicKidneyDisease === 'yes') addTerm('kidney disease')
  if (form.autoimmuneDisease === 'yes') addTerm('autoimmune')
  if (form.familyHistory === 'yes') addTerm('family history')
  if (form.ivfConception === 'yes') addTerm('ivf')
  if (form.proteinuria === 'yes') addTerm('proteinuria')
  if (Number(form.bmi) >= 30) addTerm('bmi')
  if (Number(form.maternalAge) < 20) addTerm('age < 20')
  if (Number(form.maternalAge) > 35) addTerm('age > 35')
  if (Number(form.sbp) >= 140 || Number(form.dbp) >= 90) addTerm('hypertension')
  if (form.parity === 'nulliparous') addTerm('nulliparity')
  if (form.parity === 'multiparous') addTerm('multiparity')

  if (!activeTerms.length) return []

  const matches = []
  const seenSnippets = new Set()

  evidenceData.evidence.forEach((table) => {
    table.rows.forEach((row) => {
      const rowText = row.__rowText || ''
      if (activeTerms.some((term) => rowText.includes(term))) {
        const snippet = rowText.replace(/\s+/g, ' ').slice(0, 180)
        if (!seenSnippets.has(snippet)) {
          seenSnippets.add(snippet)
          matches.push({
            source: table.filename,
            snippet,
            reference: row.Source || row['Source'] || ''
          })
        }
      }
    })
  })

  return matches.slice(0, 4)
}

const extractValuesFromText = (text) => {
  const updates = {}
  const lowerText = text.toLowerCase()

  // Maternal age
  const ageMatch = text.match(/age[:\s]+(\d{1,3})/i)
  if (ageMatch) updates.maternalAge = String(ageMatch[1])

  // Gestational week
  const gestMatch = text.match(/gestation(?:al)?[:\s]+(\d{1,2})\s*w/i)
  if (gestMatch) updates.gestationalWeek = String(gestMatch[1])

  // BMI
  const bmiMatch = text.match(/bmi[:\s]+(\d{1,2}(?:\.\d{1})?)/i)
  if (bmiMatch) updates.bmi = String(bmiMatch[1])

  // Systolic BP
  const sbpMatch = text.match(/(?:systolic|sbp)[:\s]+(\d{2,3})/i)
  if (sbpMatch) updates.sbp = String(sbpMatch[1])

  // Diastolic BP
  const dbpMatch = text.match(/(?:diastolic|dbp)[:\s]+(\d{2,3})/i)
  if (dbpMatch) updates.dbp = String(dbpMatch[1])

  // Parity
  if (lowerText.includes('nulliparous') || lowerText.includes('nullipara')) {
    updates.parity = 'nulliparous'
  } else if (lowerText.includes('multiparous') || lowerText.includes('multipara')) {
    updates.parity = 'multiparous'
  }

  // Yes/No fields
  const yesNoFields = [
    { key: 'priorPreeclampsia', patterns: ['prior preeclampsia', 'previous preeclampsia'] },
    { key: 'familyHistory', patterns: ['family history', 'family h/o'] },
    { key: 'chronicHypertension', patterns: ['chronic hypertension', 'htn'] },
    { key: 'diabetes', patterns: ['diabetes mellitus', 'gdm', 'diabetes'] },
    { key: 'chronicKidneyDisease', patterns: ['kidney disease', 'ckd', 'renal'] },
    { key: 'autoimmuneDisease', patterns: ['autoimmune', 'lupus', 'sle'] },
    { key: 'multipleGestation', patterns: ['multiple gestation', 'twins', 'multip'] },
    { key: 'ivfConception', patterns: ['ivf', 'in vitro'] },
    { key: 'proteinuria', patterns: ['proteinuria', 'protein in urine'] }
  ]

  yesNoFields.forEach(({ key, patterns }) => {
    const found = patterns.some((p) => lowerText.includes(p))
    if (found) {
      const hasNo = lowerText.match(new RegExp(`no\\s+${patterns[0]}|${patterns[0]}\\s*:\\s*no`, 'i'))
      updates[key] = hasNo ? 'no' : 'yes'
    }
  })

  return updates
}

const processReportImage = async (file, onProgress, onComplete) => {
  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const imageData = e.target.result
        onProgress('Extracting text from image...')

        const { Tesseract } = await import('tesseract.js')
        const {
          data: { text }
        } = await Tesseract.recognize(imageData, 'eng', {
          logger: (m) => {
            if (m.status === 'recognizing') {
              onProgress(`OCR progress: ${Math.round(m.progress * 100)}%`)
            }
          }
        })

        onProgress('Parsing extracted data...')
        const extracted = extractValuesFromText(text)
        onComplete(extracted, text)
      } catch (err) {
        onComplete(null, null)
        throw new Error(`OCR processing failed: ${err.message}. Make sure tesseract.js is installed.`)
      }
    }
    reader.readAsDataURL(file)
  } catch (error) {
    onComplete(null, null)
    throw new Error(`Failed to process image: ${error.message}`)
  }
}

function App() {
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [ocrProgress, setOcrProgress] = useState('')
  const [ocrExtracted, setOcrExtracted] = useState(null)

  const ageGroup = Number(form.maternalAge) < 20 ? '<20' : Number(form.maternalAge) <= 35 ? '20-35' : '>35'
  const parityGroup = form.parity
  const biasNote =
    ageGroup === '20-35'
      ? 'Most preeclampsia studies are centered on this age group.'
      : 'This age group is less represented in the literature, which focused on ages 20-35.'

  const getBadgeClass = (risk) => {
    if (risk === 'Low') return 'badge badge-low'
    if (risk === 'Moderate') return 'badge badge-moderate'
    return 'badge badge-high'
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleImageUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setOcrProgress('Starting OCR...')
    setError(null)
    try {
      await processReportImage(
        file,
        setOcrProgress,
        (extracted, rawText) => {
          if (extracted) {
            setOcrExtracted(rawText)
            setForm((current) => ({ ...current, ...extracted }))
            setOcrProgress(`Successfully extracted ${Object.keys(extracted).length} fields from report.`)
            setTimeout(() => setOcrProgress(''), 3000)
          } else {
            setError('Failed to extract data from image')
          }
        }
      )
    } catch (err) {
      setError(err.message)
      setOcrProgress('')
    }
  }

  const buildPatientSummary = () => {
    return `Maternal age: ${form.maternalAge}
Gestational week: ${form.gestationalWeek}
BMI: ${form.bmi}
Systolic BP: ${form.sbp}
Diastolic BP: ${form.dbp}
Parity: ${form.parity}
Prior preeclampsia: ${form.priorPreeclampsia}
Family history of preeclampsia: ${form.familyHistory}
Chronic hypertension: ${form.chronicHypertension}
Diabetes mellitus: ${form.diabetes}
Chronic kidney disease: ${form.chronicKidneyDisease}
Autoimmune disease: ${form.autoimmuneDisease}
Multiple gestation: ${form.multipleGestation}
IVF conception: ${form.ivfConception}
Proteinuria: ${form.proteinuria}`
  }

  const callGrok = async () => {
    const apiKey = import.meta.env.VITE_GROK_API_KEY
    if (!apiKey) {
      throw new Error('Missing Grok API key. Set VITE_GROK_API_KEY in your environment.')
    }

    const userMessage = `${systemPrompt}\n\nPatient data:\n${buildPatientSummary()}\n\nAnswer with the exact JSON structure only.`

    const response = await fetch('https://api.x.ai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'grok-2',
        messages: [
          {
            role: 'user',
            content: userMessage
          }
        ],
        temperature: 0.0,
        max_tokens: 512
      })
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`Grok API error: ${response.status} ${body}`)
    }

    const data = await response.json()
    const raw = data.choices?.[0]?.message?.content || ''
    const jsonText = raw.trim().replace(/^([\s\S]*?\{)/, '{').replace(/\}[\s\S]*$/, '}')

    try {
      const parsed = JSON.parse(jsonText)
      return parsed
    } catch (parseError) {
      throw new Error('Unable to parse Grok response. Ensure the model returns exact JSON.')
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const apiResult = await callGrok()
      setResult(apiResult)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const computedResult = useMemo(() => getLocalRiskAssessment(form), [form])
  const evidenceMatches = useMemo(() => getEvidenceMatches(form), [form])
  const majorRiskNote = computedResult.majorRisk
    ? 'Major risk profile detected in the evidence-weighted assessment.'
    : 'This profile does not meet major risk criteria according to the current evidence base.'

  return (
    <div className="page-shell">
      <header className="hero-card">
        <div>
          <p className="eyebrow">Research prototype</p>
          <h1>Preeclampsia risk assessment</h1>
          <p className="hero-copy">
            Enter key maternal risk factors and get an explainable risk score with a simple bias audit panel.
          </p>
        </div>
      </header>

      <main className="app-grid">
        <section className="panel card form-panel">
          <h2>Clinical variables</h2>
          
          <div className="upload-section">
            <label className="upload-label">
              📄 Upload medical report (JPG/PNG)
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="upload-input"
              />
            </label>
            {ocrProgress && <p className="ocr-status">{ocrProgress}</p>}
            {ocrExtracted && <p className="ocr-success">✓ Report data extracted and applied</p>}
          </div>

          <form onSubmit={handleSubmit}>
            <div className="field-row">
              <label>
                Maternal age
                <input
                  name="maternalAge"
                  type="number"
                  min="12"
                  max="55"
                  value={form.maternalAge}
                  onChange={handleChange}
                  required
                />
              </label>
              <label>
                Gestational week
                <input
                  name="gestationalWeek"
                  type="number"
                  min="1"
                  max="42"
                  value={form.gestationalWeek}
                  onChange={handleChange}
                  required
                />
              </label>
            </div>

            <div className="field-row">
              <label>
                BMI
                <input
                  name="bmi"
                  type="number"
                  min="10"
                  step="0.1"
                  value={form.bmi}
                  onChange={handleChange}
                  required
                />
              </label>
              <label>
                Systolic BP
                <input
                  name="sbp"
                  type="number"
                  min="60"
                  max="240"
                  value={form.sbp}
                  onChange={handleChange}
                  required
                />
              </label>
            </div>

            <div className="field-row">
              <label>
                Diastolic BP
                <input
                  name="dbp"
                  type="number"
                  min="40"
                  max="160"
                  value={form.dbp}
                  onChange={handleChange}
                  required
                />
              </label>
              <label>
                Parity
                <select name="parity" value={form.parity} onChange={handleChange}>
                  {parityOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="field-grid">
              <label>
                Prior preeclampsia
                <select name="priorPreeclampsia" value={form.priorPreeclampsia} onChange={handleChange}>
                  {yesNoOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Family history
                <select name="familyHistory" value={form.familyHistory} onChange={handleChange}>
                  {yesNoOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Chronic hypertension
                <select name="chronicHypertension" value={form.chronicHypertension} onChange={handleChange}>
                  {yesNoOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Diabetes mellitus
                <select name="diabetes" value={form.diabetes} onChange={handleChange}>
                  {yesNoOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Chronic kidney disease
                <select name="chronicKidneyDisease" value={form.chronicKidneyDisease} onChange={handleChange}>
                  {yesNoOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Autoimmune disease
                <select name="autoimmuneDisease" value={form.autoimmuneDisease} onChange={handleChange}>
                  {yesNoOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Multiple gestation
                <select name="multipleGestation" value={form.multipleGestation} onChange={handleChange}>
                  {yesNoOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                IVF conception
                <select name="ivfConception" value={form.ivfConception} onChange={handleChange}>
                  {yesNoOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Proteinuria
                <select name="proteinuria" value={form.proteinuria} onChange={handleChange}>
                  {proteinuriaOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="actions">
              <button type="submit" className="primary-button" disabled={loading}>
                {loading ? 'Assessing...' : 'Run risk assessment'}
              </button>
            </div>
          </form>
        </section>

        <section className="panel card output-panel">
          <h2>Assessment output</h2>

          {error && <div className="alert">{error}</div>}

          {result ? (
            <div className="result-card">
              <div className="result-header">
                <span className={getBadgeClass(result.risk_level)}>{result.risk_level}</span>
                <div className="score-box">
                  <span className="score-label">Score</span>
                  <strong>{Math.min(result.score, 10)} / 10</strong>
                </div>
              </div>

              <div className="chip-list">
                {result.top_factors.map((factor, index) => (
                  <span key={`${factor}-${index}`} className="chip">
                    {factor}
                  </span>
                ))}
              </div>

              <p className="reasoning">{result.reasoning}</p>

              {computedResult.majorRisk ? <div className="major-risk-callout">Major risk profile detected by dataset scoring.</div> : null}
              {result.bias_flag ? <p className="bias-flag">Bias flag: {result.bias_flag}</p> : null}

              <p className="guideline-text">Guideline reference: {result.guideline_reference}</p>

              <div className="evidence-card">
                <h3>Evidence basis</h3>
                <p className="evidence-summary">
                  Loaded {evidenceData.sourceCount} literature tables. Matched {evidenceMatches.length} evidence rows for the selected risk profile.
                </p>
                {evidenceMatches.length ? (
                  <ul className="evidence-list">
                    {evidenceMatches.map((item, index) => (
                      <li key={`${item.source}-${index}`}>
                        <span className="evidence-source">{item.source}</span>: {item.snippet}
                        {item.reference ? <span className="evidence-reference"> · Source {item.reference}</span> : null}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="evidence-summary">No direct evidence rows found for this exact profile, but all selected variables are included in the dataset.</p>
                )}
              </div>
            </div>
          ) : (
            <div className="placeholder">
              Submit the form to generate a risk level, top factors, and plain-language reasoning.
            </div>
          )}
        </section>
      </main>

      <section className="panel card audit-panel">
        <h2>Bias audit</h2>
        <div className="audit-grid">
          <div className="audit-card">
            <span className="audit-label">Age group</span>
            <strong>{ageGroup}</strong>
            <p>{biasNote}</p>
          </div>
          <div className="audit-card">
            <span className="audit-label">Parity group</span>
            <strong>{parityGroup}</strong>
            <p>
              Nulliparous and multiparous risk estimates may differ. Most literature centers on standard parity groups rather than detailed subgroup analysis.
            </p>
          </div>
        </div>
      </section>

      <footer className="disclaimer-card">
        <p>
          This tool is a research prototype only and does not replace clinical judgment.
        </p>
      </footer>
    </div>
  )
}

export default App
