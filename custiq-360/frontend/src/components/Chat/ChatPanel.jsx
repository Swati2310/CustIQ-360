import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, Trash2, Sparkles, Mic, MicOff } from 'lucide-react'
import useChat from '../../hooks/useChat.js'
import { useVoice } from '../../hooks/useVoice.js'
import MessageBubble from './MessageBubble.jsx'
import clsx from 'clsx'

const SUGGESTED_QUESTIONS = [
  'What is the total outstanding loan?',
  'Any cross-sell recommendations?',
  'What is the KYC status?',
  'Any FD maturity alerts?',
]

export default function ChatPanel({ customerId }) {
  const { messages, sendMessage, isStreaming, error, clearMessages } = useChat(customerId)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const handleVoiceResult = useCallback((text) => {
    setInput(text)
    // auto-send after a short pause so user sees what was transcribed
    setTimeout(() => {
      if (text.trim()) {
        sendMessage(text.trim())
        setInput('')
      }
    }, 800)
  }, [sendMessage])

  const { isListening, transcript, error: voiceError, isSupported: voiceSupported, start: startVoice, stop: stopVoice } = useVoice({
    onResult: handleVoiceResult,
    lang: 'en-US',
  })

  // Show interim transcript in input while listening
  useEffect(() => {
    if (isListening && transcript) setInput(transcript)
  }, [transcript, isListening])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isStreaming) return
    setInput('')
    sendMessage(text)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestion = (q) => {
    setInput(q)
    sendMessage(q)
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 border-l border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
            <Bot className="w-4.5 h-4.5 text-white" size={18} />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">AI Assistant</p>
            <p className="text-xs text-gray-400 leading-tight">
              {isStreaming ? (
                <span className="text-primary-600 font-medium">Responding...</span>
              ) : (
                'Ask about this customer'
              )}
            </p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
            title="Clear conversation"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-14 h-14 rounded-2xl bg-primary-100 flex items-center justify-center mb-3">
              <Sparkles className="w-7 h-7 text-primary-600" />
            </div>
            <p className="text-sm font-semibold text-gray-700 mb-1">Customer AI Assistant</p>
            <p className="text-xs text-gray-500 mb-5 leading-relaxed">
              Ask me anything about this customer — their portfolio, loans, KYC status, or
              cross-sell opportunities.
            </p>

            {/* Suggested questions */}
            <div className="w-full space-y-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSuggestion(q)}
                  className="w-full text-left px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-xs text-gray-700 hover:bg-primary-50 hover:border-primary-300 hover:text-primary-700 transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Suggested questions pill row (when chat started) */}
      {messages.length > 0 && (
        <div className="px-4 py-2 flex gap-2 overflow-x-auto flex-shrink-0 border-t border-gray-100 bg-white">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => !isStreaming && handleSuggestion(q)}
              disabled={isStreaming}
              className="flex-shrink-0 px-3 py-1.5 bg-primary-50 text-primary-700 rounded-full text-xs font-medium hover:bg-primary-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-primary-100"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Errors */}
      {(error || voiceError) && (
        <div className="mx-4 mb-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex-shrink-0">
          {error || voiceError}
        </div>
      )}

      {/* Voice listening indicator */}
      {isListening && (
        <div className="mx-4 mb-2 flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-xl flex-shrink-0 animate-fade-in">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse flex-shrink-0" />
          <p className="text-xs text-red-700 font-medium flex-1 truncate">
            {transcript ? `"${transcript}"` : 'Listening… speak your question'}
          </p>
          <button onClick={stopVoice} className="text-red-500 hover:text-red-700 flex-shrink-0">
            <MicOff className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Input area */}
      <div className="p-4 bg-white border-t border-gray-200 flex-shrink-0">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? 'Listening…' : 'Ask about this customer…'}
            rows={1}
            disabled={isStreaming}
            className={clsx(
              'flex-1 resize-none border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all leading-relaxed',
              'min-h-[40px] max-h-[120px]',
              isListening
                ? 'bg-red-50 border-red-200 text-gray-700'
                : isStreaming
                  ? 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-white border-gray-300'
            )}
            style={{ fieldSizing: 'content' }}
          />

          {/* Mic button */}
          {voiceSupported && (
            <button
              onClick={isListening ? stopVoice : startVoice}
              disabled={isStreaming}
              title={isListening ? 'Stop listening' : 'Speak your question'}
              className={clsx(
                'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all',
                isListening
                  ? 'bg-red-500 hover:bg-red-600 text-white shadow-md animate-pulse'
                  : isStreaming
                    ? 'bg-gray-100 text-gray-300 cursor-not-allowed'
                    : 'bg-gray-100 hover:bg-primary-50 hover:text-primary-600 text-gray-400'
              )}
            >
              {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
          )}

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className={clsx(
              'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all',
              input.trim() && !isStreaming
                ? 'bg-primary-600 hover:bg-primary-700 text-white shadow-sm'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            )}
          >
            {isStreaming ? (
              <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-1.5 text-center">
          {voiceSupported
            ? 'Enter to send · Shift+Enter newline · 🎤 speak your question'
            : 'Enter to send · Shift+Enter for newline'}
        </p>
      </div>
    </div>
  )
}
