import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './PassageSettingsPage.css';
import LoadingPage from './LoadingPage'; // 로딩 페이지 컴포넌트 임포트

const PassageSettingsPage = () => {
  const navigate = useNavigate();

  // 기존 상태들
  const [difficulty, setDifficulty] = useState('어려움');
  const [topic, setTopic] = useState('과학기술');
  const [features, setFeatures] = useState('지문의 핵심 파악하기');
  const [passageLength, setPassageLength] = useState(1000);

  // **새로운 로딩 상태 추가**
  const [isLoading, setIsLoading] = useState(false);

  const difficultyOptions = ['기초', '보통', '어려움'];
  const topicOptions = ['과학기술', '인문', '사회', '예술/문화', '시사'];
  const featureOptions = ['실제 문제 풀이', '지문의 핵심 파악하기'];
  
  const minLength = 800;
  const maxLength = 1200;

  const handleCreatePassage = () => {
    // 1. features가 '실제 문제 풀이'일 때
    if (features === '실제 문제 풀이') {
      // 2. 로딩 상태를 true로 설정하여 로딩 페이지를 화면에 띄웁니다.
      setIsLoading(true);

      // 3. 2초 후 로딩 상태를 false로 바꾸고 페이지를 이동합니다.
      setTimeout(() => {
        setIsLoading(false);
        navigate('/quiz-page');
      }, 2000); // 2초는 API 요청 시간이나 데이터 처리 시간을 가정합니다.

    } else if(features === '지문의 핵심 파악하기') {
      // 2. 로딩 상태를 true로 설정하여 로딩 페이지를 화면에 띄웁니다.
      setIsLoading(true);

      // 3. 2초 후 로딩 상태를 false로 바꾸고 페이지를 이동합니다.
      setTimeout(() => {
        setIsLoading(false);
        navigate('/summary-practice');
      }, 2000); // 2초는 API 요청 시간이나 데이터 처리 시간을 가정합니다.
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
  
  // **로딩 중이면 LoadingPage를 렌더링**
  if (isLoading) {
    return <LoadingPage />;
  }

  return (
    <div className="passage-settings-container">
      {/* Header Section (reused from Dashboard) */}
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

      {/* Main Content */}
      <main className="settings-main">
        <h1 className="main-title">지문 설정</h1>

        {/* Difficulty Section */}
        <section className="setting-section">
          <h2>지문 난이도 설정</h2>
          <div className="option-group">
            {renderOptionButtons(difficultyOptions, difficulty, setDifficulty)}
          </div>
        </section>
        
        {/* Topic Section */}
        <section className="setting-section">
          <h2>주제 선택</h2>
          <div className="option-group">
            {renderOptionButtons(topicOptions, topic, setTopic)}
          </div>
        </section>

        {/* Feature Section */}
        <section className="setting-section">
          <h2>기능 선택</h2>
          <div className="option-group">
            {renderOptionButtons(featureOptions, features, setFeatures)}
          </div>
        </section>

        {/* Length Slider Section */}
        <section className="setting-section">
          <h2>지문 길이 설정</h2>
          <div className="length-slider-container">
            <span>{minLength}자</span>
            <input
              type="range"
              min={minLength}
              max={maxLength}
              value={passageLength}
              onChange={(e) => setPassageLength(Number(e.target.value))}
              className="length-slider"
            />
            <span>{maxLength}자</span>
          </div>
          <div className="current-length">
            현재 설정: {passageLength}자
          </div>
        </section>

        {/* Action Buttons */}
        <div className="action-buttons">
          <button className="btn btn-back" onClick={handleGoBack}>
            뒤로 가기
          </button>
          <button className="btn btn-create" onClick={handleCreatePassage}>
            생성 시작
          </button>
        </div>

      </main>
    </div>
  );
};

export default PassageSettingsPage;