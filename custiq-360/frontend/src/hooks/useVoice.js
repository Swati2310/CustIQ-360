import { useState, useRef, useCallback, useEffect } from 'react'

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition || null

export function useVoice({ onResult, onEnd, continuous = false, lang = 'en-US' } = {}) {
  const [isListening, setIsListening]   = useState(false)
  const [transcript,  setTranscript]    = useState('')
  const [error,       setError]         = useState('')
  const recognitionRef = useRef(null)

  const isSupported = Boolean(SpeechRecognition)

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }, [])

  const start = useCallback(() => {
    if (!isSupported) {
      setError('Speech recognition is not supported in this browser. Use Chrome or Edge.')
      return
    }
    setError('')
    setTranscript('')

    const rec = new SpeechRecognition()
    rec.lang             = lang
    rec.continuous       = continuous
    rec.interimResults   = true
    rec.maxAlternatives  = 1

    rec.onstart = () => setIsListening(true)

    rec.onresult = (e) => {
      let interim = ''
      let final   = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const text = e.results[i][0].transcript
        if (e.results[i].isFinal) final += text
        else interim += text
      }
      const current = (final || interim).trim()
      setTranscript(current)
      if (final && onResult) onResult(final.trim())
    }

    rec.onerror = (e) => {
      if (e.error !== 'aborted') setError(`Mic error: ${e.error}`)
      setIsListening(false)
    }

    rec.onend = () => {
      setIsListening(false)
      if (onEnd) onEnd()
    }

    recognitionRef.current = rec
    rec.start()
  }, [isSupported, lang, continuous, onResult, onEnd])

  // Cleanup on unmount
  useEffect(() => () => recognitionRef.current?.abort(), [])

  return { isListening, transcript, error, isSupported, start, stop }
}
