import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { ArrowLeft, Send, Loader } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  searchMode?: string
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [searchMode, setSearchMode] = useState<'vector_only' | 'hybrid'>('vector_only')
  const [scalarFilters, setScalarFilters] = useState<Record<string, any>>({})
  const [showScalarInput, setShowScalarInput] = useState(false)
  const [timeRange, setTimeRange] = useState<{start_days?: number, end_days?: number}>({})
  const [showTimeRange, setShowTimeRange] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
    }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const requestData: any = {
        query: input,
        search_mode: searchMode,
        top_k: 5,
      }

      if (searchMode === 'hybrid' && Object.keys(scalarFilters).length > 0) {
        requestData.scalar_filters = scalarFilters
      }

      // 如果设置了时间范围，添加到请求中
      if (timeRange.start_days !== undefined || timeRange.end_days !== undefined) {
        requestData.time_range = {
          start_days: timeRange.start_days || 0,
          end_days: timeRange.end_days || 999999
        }
      }

      const response = await axios.post('/api/query', requestData)

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        searchMode: response.data.search_mode,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，查询失败：' + (error.response?.data?.detail || '未知错误'),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const addScalarFilter = () => {
    const key = prompt('请输入标量字段名（如：date, category等）：')
    if (!key) return

    const valueType = prompt('请输入值类型（number/string/range）：')
    if (!valueType) return

    let value: any
    if (valueType === 'number') {
      value = parseFloat(prompt('请输入数值：') || '0')
    } else if (valueType === 'range') {
      const min = prompt('请输入最小值：')
      const max = prompt('请输入最大值：')
      value = { $gte: parseFloat(min || '0'), $lte: parseFloat(max || '100') }
    } else {
      value = prompt('请输入字符串值：') || ''
    }

    setScalarFilters((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link
                to="/dashboard"
                className="text-gray-600 hover:text-gray-800"
              >
                <ArrowLeft size={20} />
              </Link>
              <h1 className="text-xl font-bold text-gray-800">智能问答</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* 检索模式选择 */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">检索模式：</label>
              <select
                value={searchMode}
                onChange={(e) => {
                  setSearchMode(e.target.value as 'vector_only' | 'hybrid')
                  // 当切换到混合检索时，显示时间范围设置
                  setShowTimeRange(e.target.value === 'hybrid')
                }}
                className="border border-gray-300 rounded-lg px-3 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="vector_only">纯向量检索</option>
                <option value="hybrid">向量标量混合检索</option>
              </select>
            </div>

            {/* 时间范围选择 - 只在混合检索模式下显示 */}
            {showTimeRange && (
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-700">起始天数：</label>
                <input
                  type="number"
                  placeholder="0"
                  value={timeRange.start_days || ''}
                  onChange={(e) => setTimeRange(prev => ({ ...prev, start_days: parseInt(e.target.value) || 0 }))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm w-20"
                />
                <label className="text-sm text-gray-700">结束天数：</label>
                <input
                  type="number"
                  placeholder="∞"
                  value={timeRange.end_days || ''}
                  onChange={(e) => setTimeRange(prev => ({ ...prev, end_days: parseInt(e.target.value) || undefined }))}
                  className="border border-gray-300 rounded px-2 py-1 text-sm w-20"
                />
                <span className="text-xs text-gray-500">基准: 2026年1月1日</span>
                {(timeRange.start_days !== undefined || timeRange.end_days !== undefined) && (
                  <button
                    onClick={() => setTimeRange({})}
                    className="text-xs text-red-600 hover:text-red-800"
                  >
                    清除
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-20">
            <p className="text-lg">开始提问吧！</p>
            <p className="text-sm mt-2">系统将基于您的知识库进行回答</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-lg p-4 ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-gray-800 shadow-md'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <div className="text-xs text-gray-500">
                        来源：{msg.sources.slice(0, 3).join(', ')}
                        {msg.sources.length > 3 && ` 等${msg.sources.length}个文档`}
                      </div>
                    </div>
                  )}
                  {msg.searchMode && (
                    <div className="mt-1 text-xs text-gray-500">
                      检索模式：{msg.searchMode === 'vector_only' ? '纯向量检索' : '混合检索'}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white rounded-lg p-4 shadow-md">
                  <Loader className="animate-spin text-indigo-600" size={20} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <div className="bg-white border-t shadow-lg">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-end space-x-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入您的问题..."
              rows={1}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              style={{ minHeight: '44px', maxHeight: '120px' }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-indigo-600 text-white p-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
