import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Page1.css'; // Make sure to import the CSS file

const Page1 = () => {
  const navigate = useNavigate();

  const handleLoginClick = () => {
    // Implement your login logic here
    // Dashboard page navigation after login
    navigate('/dashboard');
    // For now, let's just log a message
    console.log("Login button clicked!");
    // You can add navigation to another page after a successful login
    // navigate('/dashboard'); 
  };

  const handleKakaoLogin = () => {
    // Logic for Kakao login
    console.log("Kakao login button clicked!");
  };

  const handleGoogleLogin = () => {
    // Logic for Google login
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
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="login-input" 
          />
          
          <button 
            type="submit" 
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