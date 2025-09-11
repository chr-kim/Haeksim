import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // axios 임포트
import './SignUpPage.css';

const SignUpPage = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState(''); // 성공 메시지 상태 추가

  const handleSignUp = async (e) => { // async 키워드 추가
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    try {
      // 1. FastAPI 서버의 회원가입 API 엔드포인트로 POST 요청
      const response = await axios.post('http://192.168.45.219:8000/signup', {
        username: email, // FastAPI에서 username을 사용하므로 email을 username으로 보냄
        password: password,
      });

      // 2. 서버 응답 확인
      if (response.status === 200) {
        setSuccessMessage('회원가입이 완료되었습니다!');
        console.log('회원가입 성공:', response.data);
        // 회원가입 성공 후 2초 뒤 로그인 페이지로 이동
        setTimeout(() => {
          navigate('/');
        }, 2000);
      }
    } catch (err) {
      // 3. 에러 처리
      if (err.response) {
        // 서버에서 보낸 에러 메시지 처리
        console.error('회원가입 실패:', err.response.data);
        setError(err.response.data.detail || '회원가입 중 오류가 발생했습니다.');
      } else {
        // 네트워크 또는 기타 오류
        console.error('네트워크 오류:', err);
        setError('네트워크 오류가 발생했습니다. 서버 상태를 확인해주세요.');
      }
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
          {successMessage && <p className="signup-success">{successMessage}</p>} {/* 성공 메시지 출력 */}

          <button type="submit" className="signup-btn signup-btn-primary">
            회원가입
          </button>
          
          {/* 다른 버튼들은 그대로 유지 */}
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