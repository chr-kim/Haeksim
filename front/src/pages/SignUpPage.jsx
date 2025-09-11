import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignUpPage.css';

const SignUpPage = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const handleSignUp = (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    // 실제 회원가입 로직 (API 호출 등)을 여기에 구현합니다.
    // 현재는 더미 로직으로 성공 메시지를 띄우고 페이지를 이동합니다.
    console.log('회원가입 정보:', { email, password });
    alert('회원가입이 완료되었습니다!');
    navigate('/');
  };

  return (
    <div className="signup-container">
      <header className="signup-header">
        <div className="logo">Haeksim</div>
      </header>

      <div className="signup-card">
        <h1 className="signup-title">회원가입</h1>
        <form onSubmit={handleSignUp} className="signup-form">
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

          <button type="submit" className="signup-btn signup-btn-primary">
            회원가입
          </button>
          <button type="button" className="signup-btn signup-btn-secondary">
            이메일로 가입하기
          </button>
          <button type="button" className="signup-btn signup-btn-kakao">
            카카오로 가입하기
          </button>
        </form>

        <p className="signup-link-text">
          기본 계정이 있으신가요? <a href="/">로그인 페이지로</a>
        </p>
      </div>

    </div>
  );
};

export default SignUpPage;
