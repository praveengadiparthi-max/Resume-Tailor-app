import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

const ERROR_MESSAGES = {
  400: 'Only PDF and DOCX files are supported.',
  413: 'File exceeds the 5 MB size limit.',
  422: 'Could not extract text from the file. Try pasting the text instead.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'Something went wrong generating your resume. Please try again.',
  502: 'AI service returned an error. Please try again.',
  503: 'AI service is temporarily unavailable. Please try again shortly.',
}

function friendlyError(err) {
  if (err.response) {
    const msg = err.response.data?.detail
    return msg || ERROR_MESSAGES[err.response.status] || 'An unexpected error occurred.'
  }
  if (err.code === 'ECONNABORTED') {
    return 'Request timed out. The AI may be busy — please try again.'
  }
  return 'Network error. Please check your connection and try again.'
}

export async function tailorFromUpload(file, jobDescription, qualityMode, onProgress) {
  const form = new FormData()
  form.append('file', file)
  form.append('job_description', jobDescription)
  form.append('quality_mode', qualityMode ? 'true' : 'false')
  try {
    const response = await api.post('/tailor/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 40))
      },
      timeout: 120000,
    })
    return response.data
  } catch (err) {
    throw new Error(friendlyError(err))
  }
}

export async function tailorFromText(resumeText, jobDescription, qualityMode) {
  try {
    const response = await api.post(
      '/tailor/text',
      { resume_text: resumeText, job_description: jobDescription, quality_mode: qualityMode },
      { timeout: 120000 },
    )
    return response.data
  } catch (err) {
    throw new Error(friendlyError(err))
  }
}

export function getDownloadUrl(token) {
  return `/api/download/${token}`
}

export async function fetchDefaultResume() {
  const resp = await fetch('/api/default-resume')
  if (!resp.ok) return null
  const blob = await resp.blob()
  return new File([blob], 'default_resume.pdf', { type: 'application/pdf' })
}
