import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LearningAnalysisPage.css';

const LearningAnalysisPage = () => {
  const navigate = useNavigate();

  const handleTryAgain = () => {
    console.log("다시 하기 버튼 클릭!");
    // Navigate back to the summary practice page
    navigate(-1);
  };

  const handleSave = () => {
    console.log("저장 버튼 클릭!");
    // Implement logic to save the results to the user's profile
  };

  return (
    <div className="analysis-container">
      {/* Header Section */}
      <header className="analysis-header">
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
      <main className="analysis-main">
        <h1>학습 분석 결과</h1>

        {/* AI Analysis Scores */}
        <section className="analysis-section ai-scores-section">
          <h2>AI 분석 점수</h2>
          <div className="score-item">
            <span className="score-label">완성도</span>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: '85%' }}></div>
            </div>
            <span className="score-value">85%</span>
          </div>
          <div className="score-item">
            <span className="score-label">논리성</span>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: '70%' }}></div>
            </div>
            <span className="score-value">70%</span>
          </div>
          <div className="score-item">
            <span className="score-label">핵심어 정확도</span>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: '90%' }}></div>
            </div>
            <span className="score-value">90%</span>
          </div>
        </section>

        {/* Detailed Feedback Section */}
        <section className="analysis-section detailed-feedback-section">
          <h2>상세 피드백</h2>
          <div className="feedback-box">
            <div className="feedback-item">
              <span className="feedback-label">강점</span>
              <span className="feedback-text">강점 서술</span>
            </div>
            <div className="feedback-item">
              <span className="feedback-label">약점</span>
              <span className="feedback-text">약점 서술</span>
            </div>
            <div className="feedback-item">
              <span className="feedback-label">개선점</span>
              <span className="feedback-text">개선점 서술</span>
            </div>
          </div>
        </section>

        {/* Key Points and Model Example Section */}
        <section className="analysis-section tips-section">
          <div className="tips-content">
            <h2 className="section-title">개선 포인트</h2>
            <p className="section-text">
              To improve your non-fiction reading comprehension, focus on identifying the core arguments and supporting evidence in the
              text. Practice summarizing complex information in a clear and concise manner, emphasizing the logical connections between
              ideas.
            </p>
          </div>
          <div className="tips-content">
            <h2 className="section-title">모범 요약 예시</h2>
            <p className="section-text">
              The text discusses the impact of climate change on global ecosystems, highlighting the importance of sustainable practices
              to mitigate its effects. It emphasizes the need for international cooperation and individual responsibility in addressing this
              critical issue.
            </p>
          </div>
        </section>

        {/* Action Buttons */}
        <div className="action-buttons-container">
          <button className="btn btn-try-again" onClick={handleTryAgain}>다시 하기</button>
          <button className="btn btn-save" onClick={handleSave}>저장</button>
        </div>
      </main>
    </div>
  );
};

export default LearningAnalysisPage;