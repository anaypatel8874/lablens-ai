import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import api from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export default function Chatbot({ reportId, language }: { reportId: number, language: string }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I can help you understand your report. What would you like to know?', timestamp: new Date().toISOString() }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg: Message = { role: 'user', content: input, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    try {
      const res = await api.post('/chat/ask', {
        report_id: reportId,
        message: userMsg.content,
        language,
        history: messages.slice(-10),
      })
      const assistantMsg: Message = {
        role: 'assistant',
        content: res.data.message,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card h-[600px] flex flex-col">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-gray-200">
        <Bot className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold text-gray-900">Ask My Report</h3>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && <Bot className="w-6 h-6 text-gray-400 shrink-0" />}
            <div className={`max-w-[80%] p-3 rounded-lg text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
              {msg.content}
            </div>
            {msg.role === 'user' && <User className="w-6 h-6 text-gray-400 shrink-0" />}
          </div>
        ))}
        {loading && <div className="text-sm text-gray-500 italic">Analyzing...</div>}
      </div>
      <div className="flex gap-2 pt-3 border-t border-gray-200">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about your report..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <button onClick={sendMessage} disabled={loading} className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
