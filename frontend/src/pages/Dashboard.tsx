import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { MessageSquare, Database, LogOut } from 'lucide-react'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-800">安全加密向量RAG系统</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">欢迎，{user?.username}</span>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 text-gray-600 hover:text-gray-800"
              >
                <LogOut size={18} />
                <span>退出</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容区 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 知识库管理卡片 */}
          <Link
            to="/knowledge-base"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-indigo-100 p-3 rounded-lg">
                <Database className="text-indigo-600" size={32} />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-800">知识库管理</h2>
                <p className="text-gray-600 mt-1">上传和管理您的文档</p>
              </div>
            </div>
          </Link>

          {/* 问答界面卡片 */}
          <Link
            to="/chat"
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-green-100 p-3 rounded-lg">
                <MessageSquare className="text-green-600" size={32} />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-800">智能问答</h2>
                <p className="text-gray-600 mt-1">基于知识库进行问答</p>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}
