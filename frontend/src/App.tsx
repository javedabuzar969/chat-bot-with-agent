import { useMemo, useRef, useState } from 'react'
import './App.css'

type Message = {
  id: string
  sender: 'user' | 'assistant'
  text: string
  actionUrl?: string   // if present, shows a clickable link button in the bubble
}

const apiUrl = import.meta.env.VITE_API_URL || ''

function App() {
  const [sessionId, setSessionId] = useState('default')
  const [apiKey, setApiKey] = useState('')
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [currentReply, setCurrentReply] = useState('')
  const [status, setStatus] = useState<'idle' | 'streaming' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const endpoint = useMemo(() => `${apiUrl}/api/chat`, [])

  const appendMessage = (message: Message) => {
    setMessages((prev) => [...prev, message])
  }

  const sendChat = async () => {
    if (!message.trim()) return
    setError(null)
    setStatus('streaming')
    appendMessage({ id: crypto.randomUUID(), sender: 'user', text: message.trim() })
    setMessage('')
    setCurrentReply('')

    const controller = new AbortController()
    abortControllerRef.current = controller

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (apiKey.trim()) {
      headers['X-API-Key'] = apiKey.trim()
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify({ session_id: sessionId, message: message.trim() }),
        signal: controller.signal,
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || `${response.status} ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No streaming body available from backend.')
      }

      let buffer = ''
      let replyText = ''

      const decoder = new TextDecoder()
      const processLine = (line: string, eventType: string) => {
        if (eventType === 'token') {
          replyText += line
          setCurrentReply(replyText)
        } else if (eventType === 'open_url') {
          // Show a clickable link in the chat (handles popup-blocker situation)
          appendMessage({
            id: crypto.randomUUID(),
            sender: 'assistant',
            text: `Opening: ${line}`,
            actionUrl: line,
          })
          // Also try to open directly — browser may allow or block it
          window.open(line, '_blank', 'noopener,noreferrer')
        } else if (eventType === 'error') {
          throw new Error(line)
        }
      }

      let eventType = ''
      let dataLines: string[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        let newlineIndex = buffer.indexOf('\n')
        while (newlineIndex !== -1) {
          const rawLine = buffer.slice(0, newlineIndex).replace(/\r$/, '')
          buffer = buffer.slice(newlineIndex + 1)
          newlineIndex = buffer.indexOf('\n')

          if (rawLine === '') {
            if (eventType && dataLines.length > 0) {
              const data = dataLines.join('\n')
              processLine(data, eventType)
            }
            eventType = ''
            dataLines = []
            continue
          }

          if (rawLine.startsWith('event:')) {
            eventType = rawLine.slice(6).trim()
            continue
          }
          if (rawLine.startsWith('data:')) {
            dataLines.push(rawLine.slice(5).trim())
          }
        }
      }

      if (currentReply || replyText) {
        appendMessage({ id: crypto.randomUUID(), sender: 'assistant', text: replyText })
      }
      setCurrentReply('')
      setStatus('idle')
    } catch (err) {
      const messageText = err instanceof Error ? err.message : 'Unknown error'
      setError(messageText)
      setStatus('error')
    } finally {
      abortControllerRef.current = null
    }
  }

  const cancelStream = () => {
    abortControllerRef.current?.abort()
    setStatus('idle')
    setCurrentReply('')
  }

  const canSend = message.trim().length > 0 && status !== 'streaming'

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Jarvis Frontend</p>
          <h1>Talk to Jarvis</h1>
          <p>Send a prompt and receive a token-streamed reply from the backend.</p>
        </div>
        <div className="settings-panel">
          <label>
            Session ID
            <input
              value={sessionId}
              onChange={(event) => setSessionId(event.target.value)}
              placeholder="default"
            />
          </label>
          <label>
            API Key (optional)
            <input
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="X-API-Key header"
            />
          </label>
        </div>
      </header>

      <main className="chat-panel">
        <section className="chat-window" aria-label="Jarvis chat history">
          {messages.length === 0 && !currentReply ? (
            <div className="empty-state">Start the conversation by typing a message below.</div>
          ) : (
            messages.map((messageItem) => (
              <div
                key={messageItem.id}
                className={`bubble ${messageItem.sender === 'assistant' ? 'assistant' : 'user'}`}
              >
                <span className="sender-label">
                  {messageItem.sender === 'assistant' ? 'Jarvis' : 'You'}
                </span>
                <p>{messageItem.text}</p>
                {messageItem.actionUrl && (
                  <a
                    href={messageItem.actionUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="action-link"
                  >
                    🔗 Click here to open
                  </a>
                )}
              </div>
            ))
          )}
          {currentReply ? (
            <div className="bubble assistant streaming">
              <span className="sender-label">Jarvis</span>
              <p>{currentReply}</p>
            </div>
          ) : null}
        </section>

        <section className="composer">
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Ask Jarvis anything..."
            rows={4}
            aria-label="Message to Jarvis"
          />
          <div className="composer-actions">
            <button type="button" onClick={sendChat} disabled={!canSend}>
              {status === 'streaming' ? 'Streaming…' : 'Send'}
            </button>
            {status === 'streaming' ? (
              <button type="button" className="secondary" onClick={cancelStream}>
                Cancel
              </button>
            ) : null}
          </div>
          {status === 'error' && error ? <p className="error-text">{error}</p> : null}
        </section>
      </main>
    </div>
  )
}

export default App
