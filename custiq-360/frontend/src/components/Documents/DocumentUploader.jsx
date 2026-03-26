import React, { useState, useRef, useCallback } from 'react'
import {
  Upload, FileText, X, CheckCircle, AlertTriangle,
  Loader2, Image, ShieldCheck, BadgeCheck, RefreshCw, CreditCard, MapPin,
} from 'lucide-react'
import { extractDocument, applyExtraction } from '../../utils/api.js'
import clsx from 'clsx'

const DOC_TYPES = [
  {
    value: 'id_proof',
    label: 'Aadhaar / Primary ID',
    description: 'Aadhaar, Passport, Emirates ID, NRIC…',
    icon: ShieldCheck,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    fields: ['id_type', 'id_number', 'name', 'dob', 'expiry_date', 'address'],
    applies: 'Updates KYC primary document',
  },
  {
    value: 'pan_card',
    label: 'PAN / Secondary ID',
    description: 'PAN Card, SingPass ID, Residency Visa…',
    icon: CreditCard,
    color: 'text-indigo-600',
    bg: 'bg-indigo-50',
    fields: ['id_type', 'id_number', 'name', 'dob', 'expiry_date'],
    applies: 'Updates KYC secondary document',
  },
  {
    value: 'address_proof',
    label: 'Address Proof',
    description: 'Driving Licence, Utility Bill, Lease…',
    icon: MapPin,
    color: 'text-orange-600',
    bg: 'bg-orange-50',
    fields: ['id_type', 'id_number', 'name', 'address', 'expiry_date'],
    applies: 'Updates KYC address proof',
  },
  {
    value: 'salary_slip',
    label: 'Salary Slip',
    description: 'Monthly payslip / pay stub',
    icon: BadgeCheck,
    color: 'text-green-600',
    bg: 'bg-green-50',
    fields: ['employee_name', 'employer', 'gross_salary', 'net_salary', 'deductions', 'month_year'],
    applies: 'Updates annual income & occupation',
  },
  {
    value: 'property_doc',
    label: 'Property Document',
    description: 'Sale deed, registration certificate',
    icon: FileText,
    color: 'text-violet-600',
    bg: 'bg-violet-50',
    fields: ['owner_name', 'property_address', 'property_value', 'registration_date'],
    applies: 'Adds property to wealth holdings',
  },
]

const FIELD_LABELS = {
  id_type: 'Document Type',
  id_number: 'ID Number',
  name: 'Name on Document',
  dob: 'Date of Birth',
  expiry_date: 'Expiry Date',
  address: 'Address',
  employee_name: 'Employee Name',
  employer: 'Employer / Company',
  gross_salary: 'Gross Salary',
  net_salary: 'Net Salary',
  deductions: 'Total Deductions',
  month_year: 'Pay Period',
  owner_name: 'Owner Name',
  property_address: 'Property Address',
  property_value: 'Property Value',
  registration_date: 'Registration Date',
}

export default function DocumentUploader({ customerId, onApplied }) {
  const [docType, setDocType] = useState('id_proof')
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [applying, setApplying] = useState(false)
  const [extracted, setExtracted] = useState(null)   // { success, extracted_data, method, confidence }
  const [applied, setApplied] = useState(null)        // { updated_fields, message }
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const selectedType = DOC_TYPES.find((d) => d.value === docType)

  const handleFile = useCallback((f) => {
    if (!f) return
    if (!f.type.startsWith('image/') && f.type !== 'application/pdf') {
      setError('Only images (JPG, PNG) and PDF files are accepted.')
      return
    }
    setFile(f)
    setExtracted(null)
    setApplied(null)
    setError(null)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files?.[0])
  }, [handleFile])

  const handleExtract = async () => {
    if (!file) return
    setExtracting(true)
    setError(null)
    setExtracted(null)
    setApplied(null)
    try {
      const res = await extractDocument(file, docType)
      setExtracted(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Extraction failed')
    } finally {
      setExtracting(false)
    }
  }

  const handleApply = async () => {
    if (!extracted || !customerId) return
    setApplying(true)
    setError(null)
    try {
      const res = await applyExtraction(customerId, docType, extracted.extracted_data)
      setApplied(res.data)
      if (onApplied) onApplied()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to apply to profile')
    } finally {
      setApplying(false)
    }
  }

  const reset = () => {
    setFile(null)
    setExtracted(null)
    setApplied(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const hasData = extracted?.extracted_data &&
    Object.values(extracted.extracted_data).some((v) => v)

  return (
    <div className="card">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
        <FileText className="w-4 h-4 text-primary-600" />
        <h3 className="text-sm font-semibold text-gray-800">Document Extraction</h3>
        <span className="badge bg-amber-100 text-amber-700 text-xs">AI-Powered</span>
      </div>

      <div className="p-5 space-y-5">

        {/* Doc type selector */}
        <div className="grid grid-cols-5 gap-2">
          {DOC_TYPES.map((dt) => {
            const Icon = dt.icon
            const active = docType === dt.value
            return (
              <button
                key={dt.value}
                onClick={() => { setDocType(dt.value); reset() }}
                className={clsx(
                  'flex flex-col items-center gap-1 p-3 rounded-xl border-2 text-center transition-all',
                  active
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                )}
              >
                <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center', active ? 'bg-primary-100' : dt.bg)}>
                  <Icon className={clsx('w-4 h-4', active ? 'text-primary-600' : dt.color)} />
                </div>
                <span className={clsx('text-xs font-semibold leading-tight', active ? 'text-primary-700' : 'text-gray-700')}>
                  {dt.label}
                </span>
              </button>
            )
          })}
        </div>

        <p className="text-xs text-gray-500 -mt-1">
          {selectedType?.description} &bull;{' '}
          <span className="text-primary-600 font-medium">{selectedType?.applies}</span>
        </p>

        {/* Drop zone / file selected */}
        {!file ? (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={clsx(
              'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
              dragOver ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-300 hover:bg-gray-50'
            )}
          >
            <Upload className={clsx('w-8 h-8 mx-auto mb-2', dragOver ? 'text-primary-500' : 'text-gray-400')} />
            <p className="text-sm font-medium text-gray-700">
              {dragOver ? 'Drop file here' : 'Drag & drop or click to upload'}
            </p>
            <p className="text-xs text-gray-400 mt-1">JPG, PNG or PDF — max 10 MB</p>
            <input ref={fileInputRef} type="file" accept="image/*,application/pdf" className="hidden" onChange={(e) => handleFile(e.target.files?.[0])} />
          </div>
        ) : (
          <div className="border border-gray-200 rounded-xl p-3 flex items-center gap-3 bg-gray-50">
            <div className="w-9 h-9 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0">
              {file.type.startsWith('image/') ? <Image className="w-4 h-4 text-primary-600" /> : <FileText className="w-4 h-4 text-primary-600" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">{file.name}</p>
              <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <button onClick={reset} className="p-1.5 rounded-lg hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Extract button */}
        {file && !extracted && (
          <button
            onClick={handleExtract}
            disabled={extracting}
            className={clsx(
              'w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all',
              extracting ? 'bg-primary-400 text-white cursor-not-allowed' : 'bg-primary-600 hover:bg-primary-700 text-white shadow-sm'
            )}
          >
            {extracting ? <><Loader2 className="w-4 h-4 animate-spin" />Extracting with AI...</> : <><Upload className="w-4 h-4" />Extract Document Data</>}
          </button>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5">
            <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        {/* Extracted data — readable card */}
        {extracted && hasData && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm font-semibold text-green-700">Extraction Complete</span>
                <span className="text-xs text-gray-400">via {extracted.method === 'llava' ? 'Gemini Vision' : 'OCR'}</span>
              </div>
              <button onClick={reset} className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
                <RefreshCw className="w-3 h-3" /> Reset
              </button>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-xl divide-y divide-gray-100 overflow-hidden">
              {selectedType?.fields.map((field) => {
                const val = extracted.extracted_data[field]
                if (!val) return null
                return (
                  <div key={field} className="flex items-start gap-3 px-4 py-2.5">
                    <span className="text-xs text-gray-500 w-32 flex-shrink-0 pt-0.5">{FIELD_LABELS[field] || field}</span>
                    <span className="text-sm font-medium text-gray-800 flex-1">{val}</span>
                  </div>
                )
              })}
            </div>

            {/* Apply button */}
            {!applied ? (
              customerId ? (
                <button
                  onClick={handleApply}
                  disabled={applying}
                  className={clsx(
                    'w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all',
                    applying ? 'bg-green-400 text-white cursor-not-allowed' : 'bg-green-600 hover:bg-green-700 text-white shadow-sm'
                  )}
                >
                  {applying
                    ? <><Loader2 className="w-4 h-4 animate-spin" />Applying to Profile...</>
                    : <><CheckCircle className="w-4 h-4" />Apply to Customer Profile</>
                  }
                </button>
              ) : (
                <p className="text-xs text-gray-400 text-center">Open a customer profile to apply this data</p>
              )
            ) : (
              /* Success confirmation */
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-semibold text-green-700">Applied to Profile</span>
                </div>
                <p className="text-xs text-green-700">{applied.message}</p>
                <div className="space-y-1">
                  {Object.entries(applied.updated_fields).map(([field, value]) => (
                    <div key={field} className="flex items-center gap-2 text-xs">
                      <span className="w-2 h-2 rounded-full bg-green-400 flex-shrink-0" />
                      <span className="text-gray-500">{field}</span>
                      <span className="text-gray-700 font-medium truncate">→ {String(value)}</span>
                    </div>
                  ))}
                </div>
                <button onClick={reset} className="text-xs text-primary-600 hover:text-primary-800 font-medium mt-1">
                  Upload another document
                </button>
              </div>
            )}
          </div>
        )}

        {/* Extracted but no usable data */}
        {extracted && !hasData && (
          <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-amber-700">
              <p className="font-medium">Could not extract readable fields.</p>
              <p>Try a clearer image or a different document type.</p>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
