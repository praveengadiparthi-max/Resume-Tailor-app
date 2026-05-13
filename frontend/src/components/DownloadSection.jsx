import { useState } from 'react'
import { saveLocal } from '../api/resumeApi'

export default function DownloadSection({ token, candidateName, companyName, onReset, elapsedSeconds, modelUsed, savedPath, onSaved, totalCount }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      const path = await saveLocal(token)
      onSaved(path)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const folderLabel = companyName || 'Unknown Company'

  return (
    <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
      <div className="text-5xl mb-3">✅</div>
      <h2 className="text-xl font-bold text-green-800 mb-1">Your tailored resume is ready!</h2>
      <p className="text-green-600 text-sm mb-1">
        Customized to match the job description using Claude AI.
      </p>
      {elapsedSeconds && modelUsed && (
        <p className="text-green-500 text-xs mb-4">
          Generated in {elapsedSeconds}s using {modelUsed}
        </p>
      )}
      {!(elapsedSeconds && modelUsed) && <div className="mb-4" />}

      {savedPath ? (
        <div className="bg-green-100 border border-green-300 rounded-lg px-5 py-3 mb-6 inline-block text-left">
          <p className="text-green-700 text-sm font-medium mb-0.5">Saved to your Desktop</p>
          <p className="text-green-600 text-xs font-mono break-all">{savedPath}</p>
        </div>
      ) : (
        <div className="mb-6">
          <p className="text-gray-500 text-xs mb-3">
            Will save to <span className="font-mono">Desktop/Resumes/{folderLabel}/</span>
          </p>
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-block bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-bold px-8 py-3 rounded-xl shadow transition-colors"
          >
            {saving ? 'Saving…' : '⬇ Save Resume'}
          </button>
          {error && (
            <p className="text-red-500 text-xs mt-2">{error}</p>
          )}
          <p className="text-xs text-gray-400 mt-2">Link expires in 10 minutes</p>
        </div>
      )}

      {totalCount && (
        <p className="text-xs text-gray-400 mt-4">
          Resumes tailored so far: <span className="font-semibold text-gray-500">{totalCount}</span>
        </p>
      )}

      <button
        onClick={onReset}
        className="text-sm text-gray-500 hover:text-brand underline transition-colors mt-2 block mx-auto"
      >
        Tailor another resume
      </button>
    </div>
  )
}
