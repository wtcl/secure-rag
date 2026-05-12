import { useState, useEffect } from 'react';
import { api } from '../api';
import { useNavigate } from 'react-router-dom';

export default function Chat({ onLogout }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) navigate('/login');
  }, [navigate]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', content: input };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    try {
      const res = await api.post('/chat', { message: input });
      setMessages((m) => [...m, { role: 'assistant', content: res.data.answer }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: '出错了：' + (err.response?.data?.detail || err.message) },
      ]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      await api.post('/upload', formData);
      alert('知识库上传成功！');
      setFile(null);
    } catch (err) {
      alert('上传失败：' + (err.response?.data?.detail || '未知错误'));
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    onLogout();
    navigate('/login');
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white">
      <div className="p-4 border-b flex justify-between items-center">
        <h1 className="text-xl font-bold">🔒 Secure RAG Chat</h1>
        <button
          onClick={handleLogout}
          className="text-red-600 hover:underline text-sm"
        >
          退出登录
        </button>
      </div>

      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center">
          <input
            type="file"
            accept=".txt,.pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="text-sm"
          />
          <button
            onClick={handleUpload}
            disabled={!file}
            className={`ml-2 px-3 py-1 rounded text-white text-sm ${
              file ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            上传知识库
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-10">
            上传 PDF/TXT 知识库后，开始提问吧！
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`my-3 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}
          >
            <div
              className={`inline-block p-3 rounded-lg max-w-[80%] ${
                msg.role === 'user'
                  ? 'bg-blue-100 text-gray-800'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 border-t">
        <div className="flex">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            className="flex-1 border p-2 rounded-l focus:outline-none"
            placeholder="输入你的问题..."
          />
          <button
            onClick={handleSend}
            className="bg-blue-600 text-white px-4 rounded-r hover:bg-blue-700"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
}
