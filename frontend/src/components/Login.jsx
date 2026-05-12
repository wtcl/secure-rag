import { useState } from 'react';
import { api, setAuthToken } from '../api';
import { useNavigate } from 'react-router-dom';

export default function Login({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const nav = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isLogin) {
        const res = await api.post('/token', new URLSearchParams({ username, password }));
        localStorage.setItem('token', res.data.access_token);
        setAuthToken(res.data.access_token);
        onLogin();
        nav('/chat');
      } else {
        await api.post('/register', new URLSearchParams({ username, password }));
        alert('注册成功，请登录');
        setIsLogin(true);
      }
    } catch (err) {
      alert(err.response?.data?.detail || '操作失败');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded shadow-md w-96">
        <h2 className="text-2xl mb-4 font-bold">{isLogin ? '登录' : '注册'}</h2>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-2 border mb-3 rounded"
          placeholder="用户名"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-2 border mb-3 rounded"
          placeholder="密码"
          required
        />
        <button
          type="submit"
          className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700"
        >
          {isLogin ? '登录' : '注册'}
        </button>
        <button
          type="button"
          onClick={() => setIsLogin(!isLogin)}
          className="mt-3 text-blue-600 underline w-full"
        >
          {isLogin ? '没有账号？去注册' : '已有账号？去登录'}
        </button>
      </form>
    </div>
  );
}
