import { useCallback, useEffect, useState } from 'react'
import { useDropzone } from 'react-dropzone'

const MAX_SIZE = 5 * 1024 * 1024

export default function ResumeInput({ onChange, disabled, preloadedFile }) {
  const [mode, setMode] = useState('upload')
  const [file, setFile] = useState(null)

  useEffect(() => {
    if (preloadedFile && !file) {
      setFile(preloadedFile)
      onChange({ mode: 'upload', file: preloadedFile })
    }
  }, [preloadedFile])
  const [text, setText] = useState('')
  const [dropError, setDropError] = useState('')

  const onDrop = useCallback(
    (accepted, rejected) => {
      setDropError('')
      if (rejected.length > 0) {
        const err = rejected[0].errors[0]
        if (err.code === 'file-too-large') setDropError('File exceeds 5 MB limit.')
        else if (err.code === 'file-invalid-type') setDropError('Only PDF and DOCX files are supported.')
        else setDropError(err.message)
        setFile(null)
        onChange({ mode: 'upload', file: null })
        return
      }
      if (accepted.length > 0) {
        setFile(accepted[0])
        onChange({ mode: 'upload', file: accepted[0] })
      }
    },
    [onChange],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: MAX_SIZE,
    multiple: false,
    disabled,
  })

  function handleTextChange(e) {
    setText(e.target.value)
    onChange({ mode: 'paste', text: e.target.value })
  }

  function switchMode(m) {
    setMode(m)
    setDropError('')
    if (m === 'upload') onChange({ mode: 'upload', file })
    else onChange({ mode: 'paste', text })
  }

  return (
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-2">Your Resume</label>

      {/* Tab Toggle */}
      <div className="flex border border-gray-200 rounded-lg overflow-hidden mb-3 w-fit">
        {['upload', 'paste'].map((m) => (
          <button
            key={m}
            onClick={() => switchMode(m)}
            disabled={disabled}
            className={`px-5 py-2 text-sm font-medium transition-colors ${
              mode === m
                ? 'bg-brand text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            {m === 'upload' ? 'Upload File' : 'Paste Text'}
          </button>
        ))}
      </div>

      {/* Upload Mode */}
      {mode === 'upload' && (
        <div>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-brand bg-brand-pale'
                : 'border-gray-300 hover:border-brand hover:bg-brand-pale'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="text-4xl mb-2">📄</div>
            {file ? (
              <div>
                <p className="font-semibold text-brand">{file.name}</p>
                <p className="text-xs text-gray-400 mt-1">{(file.size / 1024).toFixed(0)} KB · Click or drag to replace</p>
              </div>
            ) : (
              <div>
                <p className="text-gray-600 font-medium">
                  {isDragActive ? 'Drop it here…' : 'Drag & drop your resume here'}
                </p>
                <p className="text-gray-400 text-sm mt-1">or click to browse · PDF or DOCX · max 5 MB</p>
              </div>
            )}
          </div>
          {dropError && <p className="text-red-500 text-sm mt-2">{dropError}</p>}
        </div>
      )}

      {/* Paste Mode */}
      {mode === 'paste' && (
        <div>
          <textarea
            value={text}
            onChange={handleTextChange}
            disabled={disabled}
            placeholder="Paste your resume text here…"
            maxLength={50000}
            rows={12}
            className="w-full border border-gray-300 rounded-xl p-4 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand resize-y disabled:opacity-50"
          />
          <p className="text-xs text-gray-400 text-right mt-1">{text.length.toLocaleString()} / 50,000</p>
        </div>
      )}
    </div>
  )
}
