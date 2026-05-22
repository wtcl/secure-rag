import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { ArrowLeft, Upload, Trash2, FileText } from 'lucide-react'

interface Document {
  id: number
  filename: string
  file_size: number
  created_at: string
}

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await axios.get('/api/documents')
      setDocuments(response.data)
    } catch (err: any) {
      setError('加载文档列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post('/api/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      await fetchDocuments()
      alert('文档上传成功！')
    } catch (err: any) {
      setError(err.response?.data?.detail || '上传失败，请重试')
    } finally {
      setUploading(false)
      // 重置input
      e.target.value = ''
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个文档吗？')) return

    try {
      await axios.delete(`/api/documents/${id}`)
      await fetchDocuments()
      alert('文档已删除')
    } catch (err: any) {
      setError('删除失败，请重试')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  return (
    <div className="min-h-screen bg-gray-50">
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
              <h1 className="text-xl font-bold text-gray-800">知识库管理</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容区 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* 上传区域 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">上传文档</h2>
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 cursor-pointer transition-colors">
              <Upload size={20} />
              <span>{uploading ? '上传中...' : '选择文件'}</span>
              <input
                type="file"
                className="hidden"
                accept=".pdf,.txt,.doc,.docx"
                onChange={handleFileUpload}
                disabled={uploading}
              />
            </label>
            <span className="text-sm text-gray-600">支持 PDF、TXT、DOC、DOCX 格式</span>
          </div>
        </div>

        {/* 文档列表 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">文档列表</h2>
          
          {loading ? (
            <div className="text-center py-8 text-gray-600">加载中...</div>
          ) : documents.length === 0 ? (
            <div className="text-center py-8 text-gray-600">暂无文档，请上传文档</div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center space-x-3">
                    <FileText className="text-indigo-600" size={24} />
                    <div>
                      <div className="font-medium text-gray-800">{doc.filename}</div>
                      <div className="text-sm text-gray-500">
                        {formatFileSize(doc.file_size)} · {new Date(doc.created_at).toLocaleString('zh-CN')}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-red-600 hover:text-red-800 p-2"
                    title="删除"
                  >
                    <Trash2 size={20} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
