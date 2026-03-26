import React from 'react'
import { Bot, User } from 'lucide-react'
import clsx from 'clsx'

/**
 * Parse markdown-like text: **bold** and line breaks
 */
function parseContent(text) {
  if (!text) return []

  const lines = text.split('\n')
  return lines.map((line, lineIdx) => {
    // Parse **bold**
    const parts = []
    const boldRegex = /\*\*(.+?)\*\*/g
    let lastIndex = 0
    let match

    while ((match = boldRegex.exec(line)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ type: 'text', content: line.slice(lastIndex, match.index) })
      }
      parts.push({ type: 'bold', content: match[1] })
      lastIndex = match.index + match[0].length
    }

    if (lastIndex < line.length) {
      parts.push({ type: 'text', content: line.slice(lastIndex) })
    }

    return { lineIdx, parts }
  })
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  const isError = message.isError

  const lines = parseContent(message.content)

  return (
    <div
      className={clsx(
        'flex gap-2.5 mb-3',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          'w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5',
          isUser ? 'bg-primary-600' : 'bg-gray-200'
        )}
      >
        {isUser ? (
          <User className="w-3.5 h-3.5 text-white" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-gray-600" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={clsx(
          'max-w-[82%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-primary-600 text-white rounded-tr-sm'
            : isError
            ? 'bg-red-50 text-red-700 border border-red-200 rounded-tl-sm'
            : 'bg-white text-gray-800 border border-gray-200 shadow-card rounded-tl-sm'
        )}
      >
        {message.content === '' && !isUser ? (
          <span className="flex items-center gap-2 text-gray-400 text-xs">
            <span className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </span>
            Thinking...
          </span>
        ) : (
          <div>
            {lines.map(({ lineIdx, parts }, idx) => (
              <React.Fragment key={lineIdx}>
                {idx > 0 && <br />}
                {parts.map((part, pIdx) =>
                  part.type === 'bold' ? (
                    <strong key={pIdx} className={isUser ? 'text-white' : 'text-gray-900'}>
                      {part.content}
                    </strong>
                  ) : (
                    <span key={pIdx}>{part.content}</span>
                  )
                )}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
