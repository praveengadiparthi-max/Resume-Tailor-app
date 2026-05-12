import { useEffect, useRef, useState } from 'react'
import { tailorFromUpload, tailorFromText, fetchDefaultResume } from './api/resumeApi'
import DownloadSection from './components/DownloadSection'
import JobDescriptionInput from './components/JobDescriptionInput'
import ResumeInput from './components/ResumeInput'
import StatusMessage from './components/StatusMessage'
import TailorButton from './components/TailorButton'

const INITIAL_STATE = {
  phase: 'idle',       // 'idle' | 'processing' | 'ready' | 'error'
  inputMode: 'upload', // 'upload' | 'paste'
  file: null,
  resumeText: '',
  jobDescription: '',
  qualityMode: false,
  downloadToken: null,
  candidateName: null,
  errorMessage: null,
  progress: 0,
  elapsedSeconds: null,
  modelUsed: null,
}

export default function App() {
  const [state, setState] = useState(INITIAL_STATE)
  const progressTimer = useRef(null)

  function patch(updates) {
    setState((s) => ({ ...s, ...updates }))
  }

  function handleResumeChange({ mode, file, text }) {
    patch({ inputMode: mode, file: file ?? state.file, resumeText: text ?? state.resumeText })
  }

  function isReady() {
    const hasResume =
      state.inputMode === 'upload' ? !!state.file : state.resumeText.trim().length >= 50
    return hasResume && state.jobDescription.trim().length >= 20
  }

  function startFakeProgress() {
    patch({ progress: 5 })
    let current = 5
    progressTimer.current = setInterval(() => {
      current = current < 85 ? current + Math.random() * 4 : current
      patch({ progress: Math.min(Math.round(current), 85) })
    }, 800)
  }

  function stopFakeProgress() {
    clearInterval(progressTimer.current)
  }

  async function handleTailor() {
    const startTime = Date.now()
    const modelUsed = state.qualityMode ? 'Sonnet (Quality)' : 'Haiku (Fast)'
    patch({ phase: 'processing', errorMessage: null, progress: 0, elapsedSeconds: null, modelUsed: null })
    startFakeProgress()
    try {
      let data
      if (state.inputMode === 'upload') {
        data = await tailorFromUpload(state.file, state.jobDescription, state.qualityMode, (pct) =>
          patch({ progress: pct }),
        )
      } else {
        data = await tailorFromText(state.resumeText, state.jobDescription, state.qualityMode)
      }
      stopFakeProgress()
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1)
      patch({ progress: 100, phase: 'ready', downloadToken: data.download_token, candidateName: data.candidate_name, elapsedSeconds: elapsed, modelUsed })
    } catch (err) {
      stopFakeProgress()
      patch({ phase: 'error', errorMessage: err.message, progress: 0 })
    }
  }

  function handleReset() {
    stopFakeProgress()
    setState(INITIAL_STATE)
  }

  useEffect(() => {
    fetchDefaultResume().then((file) => {
      if (file) patch({ file, inputMode: 'upload' })
    })
  }, [])

  useEffect(() => () => clearInterval(progressTimer.current), [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-brand shadow-md py-5 px-6">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <span className="text-3xl">📝</span>
          <div>
            <h1 className="text-white text-xl font-bold leading-tight">Resume Tailor</h1>
            <p className="text-blue-200 text-xs">AI-powered resume customization</p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-10">
        {/* Intro */}
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-800 mb-2">
            Tailor your resume to any job in seconds
          </h2>
          <p className="text-gray-500 text-base max-w-xl mx-auto">
            Upload your resume and paste a job description. Claude AI will rewrite your resume to
            highlight the skills and experience that matter most for that specific role.
          </p>
        </div>

        {state.phase === 'ready' ? (
          <DownloadSection token={state.downloadToken} candidateName={state.candidateName} onReset={handleReset} elapsedSeconds={state.elapsedSeconds} modelUsed={state.modelUsed} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left column */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <ResumeInput
                onChange={handleResumeChange}
                disabled={state.phase === 'processing'}
                preloadedFile={state.file}
              />
            </div>

            {/* Right column */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <JobDescriptionInput
                value={state.jobDescription}
                onChange={(val) => patch({ jobDescription: val })}
                disabled={state.phase === 'processing'}
              />
            </div>

            {/* Full-width bottom */}
            <div className="lg:col-span-2 space-y-4">
              {state.phase === 'processing' && (
                <StatusMessage progress={state.progress} />
              )}

              {state.phase === 'error' && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
                  <strong>Error:</strong> {state.errorMessage}
                </div>
              )}

              {/* Model toggle */}
              <div className="flex items-center justify-center gap-3">
                <span className={`text-sm font-medium ${!state.qualityMode ? 'text-brand' : 'text-gray-400'}`}>
                  ⚡ Fast
                </span>
                <button
                  onClick={() => patch({ qualityMode: !state.qualityMode })}
                  disabled={state.phase === 'processing'}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none disabled:opacity-50 ${
                    state.qualityMode ? 'bg-brand' : 'bg-gray-300'
                  }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    state.qualityMode ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
                <span className={`text-sm font-medium ${state.qualityMode ? 'text-brand' : 'text-gray-400'}`}>
                  ✨ Quality
                </span>
                <span className="text-xs text-gray-400 ml-1">
                  {state.qualityMode ? '(Sonnet — best output)' : '(Haiku — fast & cheap)'}
                </span>
              </div>

              <TailorButton
                onClick={handleTailor}
                disabled={!isReady()}
                loading={state.phase === 'processing'}
              />

              <p className="text-center text-xs text-gray-400">
                Your resume is processed securely and never stored permanently.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
