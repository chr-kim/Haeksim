import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import LoadingPage from './LoadingPage'; // 로딩 페이지 컴포넌트 임포트
import './PassageSettingsPage.css'; // 스타일 import

// 환경 변수에서 API 주소 불러오기
const API_URL = "https://unstylized-ineloquently-chiquita.ngrok-free.app";

const PassageSettingsPage = () => {
  const navigate = useNavigate();

  const [difficulty, setDifficulty] = useState('어려움');
  const [topic, setTopic] = useState('과학기술');
  const [features, setFeatures] = useState('지문요약 핵심파악');
  const [passageLength, setPassageLength] = useState(1000);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const difficultyOptions = ['기초', '보통', '어려움'];
  const topicOptions = ['과학기술', '인문', '사회', '예술/문화', '시사'];
  const featureOptions = ['선지 분석 & 논리 평가', '지문요약 핵심파악'];
  
  const minLength = 800;
  const maxLength = 1200;

  // **API로 설정값을 보내고 응답에 따라 페이지를 이동하는 함수**
  const handleCreatePassage = async () => {
    setIsLoading(true);
    setError(null);

    const requestData = {
      difficulty,
      topic,
      features,
      passageLength,
    };

    try {
      // API 엔드포인트는 백엔드에 따라 변경될 수 있습니다.
      const response = await axios.post(`${API_URL}/passages/generate`, requestData);

      console.log('지문 생성 요청 성공:', response.data);

      const responseData = response.data;

      if (features === '선지 분석 & 논리 평가') {
        // 실제 문제 풀이 데이터 형식: { passage: "...", choices: ["...", "...", ...] }
        // navigate의 state를 통해 다음 페이지로 데이터 전달
        navigate('/quiz-page', { state: { quizData: responseData } });
      } else if (features === '지문요약 핵심파악') {
        // 지문의 핵심 파악하기 데이터 형식: { passage: "..." }
        navigate('/summary-practice', { state: { passageData: responseData } });
      }
      
    } catch (err) {
      console.error('지문 생성 요청 실패:', err.response ? err.response.data : err);
      setError('지문 생성에 실패했습니다. 서버 상태를 확인해주세요.');
      setIsLoading(false);
    }
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  const renderOptionButtons = (options, selected, setter) => {
    return options.map(option => (
      <button
        key={option}
        className={`option-button ${selected === option ? 'selected' : ''}`}
        onClick={() => setter(option)}
      >
        {option}
      </button>
    ));
  };
  
  if (isLoading) {
    return <LoadingPage />;
  }

  return (
    <div className="passage-settings-container">
      <header className="settings-header">
        <div className="logo">Haeksim</div>
        <nav className="header-nav">
          <a href="/dashboard">대시보드</a>
          <a href="#" className="active">설정</a>
          <a href="#">리포트</a>
          <a href="/page1">로그아웃</a>
          <img src="path/to/profile-image.jpg" alt="Profile" className="profile-img" />
        </nav>
      </header>

      <main className="settings-main">
        <div className="settings-card">
          <h1 className="main-title">AI 맞춤형 학습 설정</h1>

          <section className="setting-section">
            <h2>학습 난이도 선택</h2>
            <div className="option-group">
              {renderOptionButtons(difficultyOptions, difficulty, setDifficulty)}
            </div>
          </section>
          
          <section className="setting-section">
            <h2>관심 주제 영역</h2>
            <div className="option-group">
              {renderOptionButtons(topicOptions, topic, setTopic)}
            </div>
          </section>

          <section className="setting-section">
            <h2>학습 방식 선택</h2>
            <div className="option-group">
              {renderOptionButtons(featureOptions, features, setFeatures)}
            </div>
          </section>

          <section className="setting-section">
            <h2>지문 길이 설정</h2>
            <div className="length-slider-container">
              <input
                type="range"
                min={minLength}
                max={maxLength}
                value={passageLength}
                onChange={(e) => setPassageLength(Number(e.target.value))}
                className="length-slider"
              />
            </div>
            <div className="current-length">
              현재 설정: {passageLength}자
            </div>
          </section>

          <div className="action-buttons">
            <button className="btn btn-back" onClick={handleGoBack}>
              뒤로 가기
            </button>
            <button className="btn btn-create" onClick={handleCreatePassage} disabled={isLoading}>
              {isLoading ? '생성 중...' : '생성 시작'}
            </button>
          </div>
          {error && <p className="error-message">{error}</p>}
        </div>
      </main>
    </div>
  );
};

export default PassageSettingsPage;