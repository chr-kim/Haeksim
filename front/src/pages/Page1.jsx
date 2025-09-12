import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// 환경 변수에서 API 주소 불러오기
const API_URL = "https://unstylized-ineloquently-chiquita.ngrok-free.app";

// axios 인스턴스에 interceptor를 설정하여 모든 요청에 Authorization 헤더를 자동으로 추가
// 이 부분은 인증이 필요한 API를 호출할 때마다 코드를 반복해서 작성할 필요 없게 해줍니다.
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);


const Page1 = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLoginClick = async () => {
    setError('');

    try {
      // 폼 데이터로 변환 (백엔드 요구사항: x-www-form-urlencoded)
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      // API 요청 시 폼 데이터 전송
      const response = await axios.post(`${API_URL}/auth/login`, formData);

      // 2. 인증 토큰(JWT) 수신 및 localStorage에 저장
      if (response.status === 200 && response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        console.log("Login successful! Token saved.");
        navigate('/dashboard'); // 로그인 성공 시 대시보드 페이지로 이동
      } else {
        // 토큰이 없는 경우 에러 처리
        setError('로그인에 성공했지만, 토큰을 받지 못했습니다.');
      }
    } catch (err) {
      // 에러 처리
      if (err.response) {
        console.error('Login failed:', err.response.data);
        
        // 백엔드 응답 형식에 따라 에러 메시지 처리
        if (Array.isArray(err.response.data.detail)) {
          // '422 Unprocessable Entity'처럼 에러 메시지가 배열일 경우
          const errorMessage = err.response.data.detail.map(item => item.msg).join('; ');
          setError(errorMessage);
        } else if (err.response.data.detail) {
          // 에러 메시지가 객체일 경우
          setError(err.response.data.detail);
        } else {
          // 기타 오류
          setError('로그인 중 알 수 없는 오류가 발생했습니다.');
        }
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
            placeholder="Username" 
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