import React, { useState } from 'react';
import ChatPage from './ChatPage';
import { useNavigate } from 'react-router-dom';


const SummaryPracticePage = () => {
  const navigate = useNavigate();
  const [summaryText, setSummaryText] = useState('');
  const [fontSize, setFontSize] = useState(16);
  const [showChat, setShowChat] = useState(false);

  const passage = "The rapid advancement of artificial intelligence (AI) has revolutionized numerous sectors, from healthcare to finance. AI systems, powered by machine learning algorithms, can analyze vast datasets to identify patterns and make predictions with remarkable accuracy. This capability has led to the development of sophisticated tools for medical diagnosis, fraud detection, and personalized education. However, the increasing reliance on AI also raises ethical concerns, particularly regarding data privacy and algorithmic bias. As AI continues to evolve, it is crucial to establish clear guidelines and regulations to ensure its responsible and equitable deployment. (지문)";

  const handleFontSizeIncrease = () => {
    setFontSize(prevSize => Math.min(prevSize + 2, 24));
  };

  const handleFontSizeDecrease = () => {
    setFontSize(prevSize => Math.max(prevSize - 2, 12));
  };

  const handleSummaryChange = (e) => {
    setSummaryText(e.target.value);
  };

  const handleAskAI = () => {
    setShowChat((prev) => !prev);
  };

  const handleSubmit = () => {
    console.log("요약 제출 버튼 클릭!");
    console.log("작성된 요약:", summaryText);
    // Submit the summary to a server
    // navigate('/summary-results');
    // navigate Learning Analysis Page
    navigate('/learning-analysis');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="summary-page-container">
      {/* Header Section */}
      <header className="summary-header">
        <div className="logo">Haeksim</div>
        <nav className="header-nav">
          <a href="/dashboard">대시보드</a>
          <a href="#">설정</a>
          <a href="#">리포트</a>
          <a href="/page1">로그아웃</a>
          <img src="path/to/profile-image.jpg" alt="Profile" className="profile-img" />
        </nav>
      </header>

      {/* Main Content */}
      <main className="summary-main">
        <div className="passage-header">
          <h1 className="main-title">제목</h1>
          <div className="font-size-controls">
            <span>글자크기: {fontSize}pt</span>
            <button onClick={handleFontSizeIncrease} className="font-size-btn">+</button>
            <button onClick={handleFontSizeDecrease} className="font-size-btn">-</button>
          </div>
        </div>

        {/* Passage Section */}
        <div className="passage-content" style={{ fontSize: `${fontSize}pt` }}>
          {passage}
        </div>

        <h2 className="summary-title">여기에 요약문을 작성해 주세요.</h2>
        
        {/* Summary Input Section */}
        <div className="summary-input-container">
          <textarea
            className="summary-textarea"
            placeholder="요약문을 작성하세요..."
            value={summaryText}
            onChange={handleSummaryChange}
            maxLength={500}
            rows="10"
          />
          <div className="char-count">
            글자 수: {summaryText.length}/500
          </div>
        </div>

        <div className="ai-teacher-section">
          <button className="btn btn-ask-ai" onClick={handleAskAI}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            AI 선생님에게 질문하기
          </button>
        </div>

        {/* Action Buttons */}
        <div className="action-buttons-container">
          <button className="btn btn-back" onClick={handleGoBack}>뒤로가기</button>
          <button className="btn btn-submit" onClick={handleSubmit}>제출</button>
        </div>
      </main>
      {showChat && (
        <div className="chat-popup">
          <ChatPage isPopup={true} />
        </div>
      )}
    </div>
  );
};

export default SummaryPracticePage;