import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Page1.css';

const Page1 = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLoginClick = async () => {
    setError('');

    try {
      // FastAPI 서버의 로그인 API 엔드포인트로 POST 요청
      const response = await axios.post('http://192.168.45.219:8000/login', {
        username: email,
        password: password,
      });

      // 서버 응답 확인 (성공적으로 로그인된 경우)
      if (response.status === 200) {
        console.log("Login successful!", response.data);
        // 성공 시 대시보드 페이지로 이동
        navigate('/dashboard');
      }
    } catch (err) {
      // 에러 처리
      if (err.response) {
        console.error('Login failed:', err.response.data);
        setError(err.response.data.detail || '로그인 중 오류가 발생했습니다.');
      } else {
        console.error('Network error:', err);
        setError('네트워크 오류가 발생했습니다. 서버 상태를 확인해주세요.');
      }
    }
  };

  const handleKakaoLogin = () => {
    console.log("Kakao login button clicked!");
  };

  const handleGoogleLogin = () => {
    console.log("Google login button clicked!");
  };

  return (
    <div className="page1-container">
      <header className="page1-header">
        <h1 className="logo">Haeksim</h1>
      </header>

      <main className="login-main">
        <h2 className="login-title">시작하기</h2>
        <p className="login-subtitle">AI와 함께 실력을 향상시켜 보세요.</p>
        
        <form className="login-form" onSubmit={(e) => e.preventDefault()}>
          <input 
            type="text" 
            placeholder="Email or Username" 
            className="login-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="login-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          
          {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}

          <button 
            type="button" 
            className="login-button login-button-primary"
            onClick={handleLoginClick}
          >
            Login
          </button>
          
          <button 
            type="button" 
            className="login-button login-button-secondary"
            onClick={() => navigate('/sign-up')}
          >
            회원가입
          </button>
        </form>

        <div className="separator">
          ------------------ 또는 ------------------
        </div>

        <div className="social-login-buttons">
          <button 
            className="social-button google-button"
            onClick={handleGoogleLogin}
          >
            Google로 로그인
          </button>
          <button 
            className="social-button kakao-button"
            onClick={handleKakaoLogin}
          >
            카카오로 로그인
          </button>
        </div>
      </main>

      <footer className="login-footer">
        <p>By continuing, you agree to our Terms of Service and Privacy Policy</p>
      </footer>
    </div>
  );
};

export default Page1;