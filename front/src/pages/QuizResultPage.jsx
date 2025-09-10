import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './QuizResultPage.css';

const QuizResultPage = () => {
  const navigate = useNavigate();
  const [expandedOption, setExpandedOption] = useState(null);

  const toggleExpansion = (optionNumber) => {
    setExpandedOption(expandedOption === optionNumber ? null : optionNumber);
  };

  const optionData = [
    { number: 1, analysis: "AI 평가: 높음", userAnswer: "오답 원인: ~~~" },
    { number: 2, analysis: "AI 평가: 낮음", userAnswer: "오답 원인: ~~~" },
    { number: 3, analysis: "AI 평가: 높음", userAnswer: "정답" },
    { number: 4, analysis: "AI 평가: 낮음", userAnswer: "오답 원인: ~~~" },
    { number: 5, analysis: "AI 평가: 낮음", userAnswer: "오답 원인: ~~~" },
  ];

  const handleNewProblem = () => {
    console.log("새 문제 풀기 버튼 클릭!");
    // Navigate to a new problem or settings page
    // navigate('/passage-settings'); 
  };
  
  const handleMainDashboard = () => {
    console.log("메인 대시보드 버튼 클릭!");
    navigate('/dashboard');
  };
  
  const handleAskAI = () => {
    console.log("AI 선생님에게 질문하기 버튼 클릭!");
    // Implement chat or query functionality
  };
  
  const handleSummaryPractice = () => {
    console.log("요약 연습하기 버튼 클릭!");
    // Navigate to a summary practice page
    navigate('/summary-practice');
  };

  return (
    <div className="quiz-result-container">
      {/* Header Section */}
      <header className="result-header">
        <div className="logo">Haeksim</div>
        <nav className="header-nav">
          <a href="#">대시보드</a>
          <a href="#" className="active">설정</a>
          <a href="#">리포트</a>
          <a href="#">로그아웃</a>
          <img src="path/to/profile-image.jpg" alt="Profile" className="profile-img" />
        </nav>
      </header>

      {/* Main Content */}
      <main className="result-main">
        <h1>문제 풀이 분석 결과</h1>

        {/* Correct Answer Section */}
        <section className="analysis-section correct-answer-box">
          <h2>정답 분석</h2>
          <div className="correct-answer-content">
            <span className="checkmark">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </span>
            <div className="answer-text">
              <p>글을 읽고 이해하는 능력을 향상시키는 것이 중요하다.</p>
              <span className="status">정답</span>
            </div>
          </div>
        </section>

        {/* Option-by-Option Analysis Section */}
        <section className="analysis-section option-analysis-section">
          <h2>선지별 과거 분석</h2>
          <div className="option-list">
            {optionData.map(option => (
              <div 
                key={option.number} 
                className="option-item"
                onClick={() => toggleExpansion(option.number)}
              >
                <div className="option-header">
                  <div className="option-number">{option.number}</div>
                  <div className={`dropdown-icon ${expandedOption === option.number ? 'expanded' : ''}`}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </div>
                </div>
                {expandedOption === option.number && (
                  <div className="option-details">
                    <p>{option.analysis}</p>
                    <p>{option.userAnswer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Summary Scores Section */}
        <section className="analysis-section summary-scores">
          <h2>종합 분석 점수</h2>
          <div className="scores-grid">
            <div className="score-card">
              <div className="score-value">80%</div>
              <div className="score-label">정답 정확도</div>
            </div>
            <div className="score-card">
              <div className="score-value">70%</div>
              <div className="score-label">과거 논리성</div>
            </div>
            <div className="score-card">
              <div className="score-value">60%</div>
              <div className="score-label">오답 분석력</div>
            </div>
            <div className="score-card">
              <div className="score-value">70%</div>
              <div className="score-label">종합 사고력</div>
            </div>
          </div>
        </section>

        {/* Action Buttons Section */}
        <div className="action-buttons">
          <button className="btn btn-new-problem" onClick={handleNewProblem}>새 문제 풀기</button>
          <button className="btn btn-main-dashboard" onClick={handleMainDashboard}>메인 대시보드</button>
          <button className="btn btn-ask-ai" onClick={handleAskAI}>AI 선생님에게 질문하기</button>
          <button className="btn btn-summary-practice" onClick={handleSummaryPractice}>요약 연습하기</button>
        </div>
      </main>
    </div>
  );
};

export default QuizResultPage;