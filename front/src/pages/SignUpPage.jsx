import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// 환경 변수에서 API 주소 불러오기 (예: .env 파일에 REACT_APP_API_URL=http://192.168.45.219:8000)
const API_URL = "https://unstylized-ineloquently-chiquita.ngrok-free.app"

const SignUpPage = () => {
  const navigate = useNavigate();

  // username 상태 추가
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false); // 로딩 상태 추가

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setIsLoading(true); // 로딩 시작

    // 1. 비밀번호 일치 여부 확인
  if (password !== confirmPassword) {
    setError('비밀번호가 일치하지 않습니다.');
    setIsLoading(false);
    return;
  }

  // 2. 대문자 포함 여부 확인 (추가된 부분)
  const hasUpperCase = /[A-Z]/.test(password);
  if (!hasUpperCase) {
    setError('비밀번호는 최소 하나의 대문자를 포함해야 합니다.');
    setIsLoading(false);
    return;
  }

    try {
      // API 명세에 맞춰 username, email, password 모두 전송
      const response = await axios.post(`${API_URL}/auth/signup`, {
        username: username,
        email: email,
        password: password,
      });

      if (response.status === 200 || response.status === 201) { // 201 Created도 성공 응답
        setSuccessMessage('회원가입이 완료되었습니다!');
        console.log('회원가입 성공:', response.data);
        setTimeout(() => {
          navigate('/page1');
        }, 2000);
      }
    } catch (err) {
      if (err.response) {
        console.error('회원가입 실패:', err.response.data);
        setError(err.response.data.detail || '회원가입 중 오류가 발생했습니다.');
      } else {
        console.error('네트워크 오류:', err);
        setError('네트워크 오류가 발생했습니다. 서버 상태를 확인해주세요.');
      }
    } finally {
      setIsLoading(false); // 요청 완료 후 로딩 종료
    }
  };

  return (
    <div className="signup-container">
      <header className="signup-header">
        <div className="logo">Haeksim</div>
      </header>

      <div className="signup-card">
        <h1 className="signup-title">회원가입</h1>
        <form onSubmit={handleSignUp} className="signup-form">
          {/* 사용자 이름 입력 필드 추가 */}
          <input
            type="text"
            placeholder="사용자 이름"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="signup-input"
          />
          <input
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="signup-input"
          />
          <input
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="signup-input"
          />
          <input
            type="password"
            placeholder="비밀번호 확인"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            className="signup-input"
          />

          {error && <p className="signup-error">{error}</p>}
          {successMessage && <p className="signup-success">{successMessage}</p>}

          <button
            type="submit"
            className="signup-btn signup-btn-primary"
            disabled={isLoading} // 로딩 중 버튼 비활성화
          >
            {isLoading ? '가입 중...' : '회원가입'}
          </button>
          
          <button type="button" className="signup-btn signup-btn-kakao">
            카카오로 가입하기
          </button>
        </form>

        <p className="signup-link-text">
          기본 계정이 있으신가요? <a href="/page1">로그인 페이지로</a>
        </p>
      </div>
    </div>
  );
};

export default SignUpPage;