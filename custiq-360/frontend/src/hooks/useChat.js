import { useState, useCallback, useRef } from 'react'
import { sendChatPost } from '../utils/api.js'

export default function useChat(customerId) {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || isStreaming) return

      const userMsg = { role: 'user', content: text.trim(), id: Date.now() }
      const assistantMsg = { role: 'assistant', content: '', id: Date.now() + 1 }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsStreaming(true)
      setError(null)

      // Build history from existing messages (exclude the new ones just added)
      const history = messages.map((m) => ({ role: m.role, content: m.content }))

      try {
        const response = await sendChatPost(text.trim(), customerId, history)

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        abortRef.current = reader

        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() // keep incomplete line

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') {
                setIsStreaming(false)
                return
              }
              if (data) {
                try {
                  const parsed = JSON.parse(data)
                  // Only append 'chunk' type events — skip 'done' and 'error' metadata events
                  if (parsed.type !== 'chunk') continue
                  const chunk = parsed.content || ''
                  if (!chunk) continue
                  setMessages((prev) => {
                    const updated = [...prev]
                    const last = updated[updated.length - 1]
                    if (last && last.role === 'assistant') {
                      updated[updated.length - 1] = { ...last, content: last.content + chunk }
                    }
                    return updated
                  })
                } catch {
                  // plain text chunk (non-JSON SSE line)
                  setMessages((prev) => {
                    const updated = [...prev]
                    const last = updated[updated.length - 1]
                    if (last && last.role === 'assistant') {
                      updated[updated.length - 1] = { ...last, content: last.content + data }
                    }
                    return updated
                  })
                }
              }
            }
          }
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Failed to send message')
          setMessages((prev) => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            if (last && last.role === 'assistant' && last.content === '') {
              updated[updated.length - 1] = {
                ...last,
                content: 'Sorry, I encountered an error. Please try again.',
                isError: true,
              }
            }
            return updated
          })
        }
      } finally {
        setIsStreaming(false)
        abortRef.current = null
      }
    },
    [customerId, isStreaming, messages]
  )

  const clearMessages = useCallback(() => {
    if (abortRef.current) {
      try {
        abortRef.current.cancel()
      } catch {}
    }
    setMessages([])
    setError(null)
    setIsStreaming(false)
  }, [])

  return { messages, sendMessage, isStreaming, error, clearMessages }
}
