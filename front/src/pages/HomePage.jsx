import React from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css'; // 새로 생성될 CSS 파일 임포트

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="home-container">

      {/* 헤더 */}
      <header className="home-header">
        <h1 className="logo">Haeksim</h1>
        <nav>
          <a href="#" className="nav-link mr-4">로그인</a>
          <a href="#" className="nav-link">회원가입</a>
        </nav>
      </header>

      {/* 메인 섹션 */}
      <main className="main-content">
        {/* 첫 번째 섹션: 환영 메시지 및 이미지 */}
        <section className="section-welcome">
          <h2 className="title-welcome">
            <span>Haeksim</span>에 오신 것을 환영합니다!
          </h2>
          <p className="subtitle-welcome">
            AI 기반 학습 도우미 Haeksim과 함께 효과적인 학습을 시작해 보세요.
          </p>
          <div className="hero-image-container">
            <img src="https://placehold.co/800x600/F5F5DC/333333?text=Haeksim+Hero+Image" alt="AI Tutoring Illustration" className="hero-image" />
          </div>
        </section>

        <div className="separator-arrow">
          <div className="arrow-icon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="icon">
              <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
          </div>
        </div>

        {/* 두 번째 섹션: 핵심 기능 소개 */}
        <section className="section-features">
          <div className="feature-grid">
            <div className="feature-card">
              <h3 className="feature-title">실시간 피드백</h3>
              <p className="feature-text">학생의 답변을 실시간으로 평가해 피드백을 드려요. 문제를 통해 선택지별 근거를 작성해 이해도를 높여요.</p>
            </div>
            <div className="feature-card">
              <h3 className="feature-title">AI 선배 튜터</h3>
              <p className="feature-text">모르는 문제나 이해하기 어려운 문제는 AI 선배를 통해 질문하세요!</p>
            </div>
            <div className="feature-card">
              <h3 className="feature-title">맞춤형 커리큘럼</h3>
              <p className="feature-text">학생 수준에 맞는 문제를 추천해 효과적인 학습을 지원합니다. AI가 교육의 균형을 맞춰줍니다.</p>
            </div>
          </div>
        </section>

        {/* 세 번째 섹션: 서비스 특징 */}
        <section className="section-highlights">
          <h3 className="highlights-title">실력 향상에 필요한 모든 것</h3>
          <p className="highlights-subtitle">
            문제 풀이부터 오답 노트, 그리고 요약까지, Haeksim이 모든 것을 도와드립니다.
          </p>
          <div className="highlights-grid">
            <div className="highlight-card">
              <h4 className="highlight-title">난이도별 맞춤 문제</h4>
              <p className="highlight-text">학생의 난이도와 원하는 실력의 지문을 기반으로 개인에게 맞는 문제를 추천해 드려요.</p>
            </div>
            <div className="highlight-card">
              <h4 className="highlight-title">오답 노트 자동 생성</h4>
              <p className="highlight-text">문제를 푼 후 바로 나의 약점을 체크해 보세요! 문제 풀이뿐만 아니라 지문 요약을 통해 본인의 이해도를 체크할 수 있어요!</p>
            </div>
          </div>
        </section>

        {/* 네 번째 섹션: CTA */}
        <section className="section-cta">
          <h3 className="cta-title">AI 선생님과 함께, 맞춤 학습으로 성적 업그레이드!</h3>
          <p className="cta-text">
            지금 시작해 잠재력을 드러내세요!
          </p>
          <button
            className="cta-button"
            onClick={() => navigate('/page1')} // 함수를 감싸서 전달
          >
            지금 바로 시작하기
          </button>
        </section>
      </main>

      {/* 푸터 */}
      <footer className="home-footer">
        <p>&copy; 2025 Haeksim. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Home;
