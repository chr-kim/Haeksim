import React from 'react';
import { useNavigate } from 'react-router-dom';
import './DashboardPage.css'; // Make sure to create this CSS file

const DashboardPage = () => {
  const navigate = useNavigate();

  // You would typically get this data from an API call
  const recentStudies = [
    { id: 1, title: "비문학 독해 연습 1", date: "2025년 9월 9일" },
    { id: 2, title: "비문학 독해 연습 1", date: "2025년 9월 8일" },
  ];

  const handleStartNewStudy = () => {
    // Logic to start a new study session
    navigate('/passage-settings');
    console.log("새 학습 시작 button clicked!");
    // navigate('/new-study-page');
  };

  const handleExtendSubscription = () => {
    // Logic to extend the subscription
    console.log("연장하기 button clicked!");
    // navigate('/subscription-page');
  };

  return (
    <div className="dashboard-container">
      {/* Header Section */}
      <header className="dashboard-header">
        <div className="logo">Haeksim</div>
        <nav className="header-nav">
          <a href="#" className="active">대시보드</a>
          <a href="#">설정</a>
          <a href="#">리포트</a>
          <a href="#">로그아웃</a>
          <img src="path/to/profile-image.jpg" alt="Profile" className="profile-img" />
        </nav>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">
        <h1>대시보드</h1>
        
        {/* Recent Study Section */}
        <section className="recent-study-section">
          <h2>최근 학습 기록</h2>
          <div className="recent-studies-grid">
            {recentStudies.map((study) => (
              <div key={study.id} className="card recent-study-card">
                <div className="card-content">
                  <h3>{study.title}</h3>
                  <p>{study.date}</p>
                  <a href="#">{study.title}</a>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Info Cards Grid */}
        <div className="info-cards-grid">
          {/* Weekly Goal Card */}
          <div className="card weekly-goal-card">
            <h2>이번 주 목표 달성률</h2>
            <div className="goal-content">
              <div className="progress-circle">
                <div className="progress-text">80%</div>
              </div>
              <p>주간 목표를 거의 달성했어요!</p>
              <p className="cheer-up">조금만 더 힘내세요!</p>
            </div>
          </div>

          {/* Recommended Study Card */}
          <div className="card recommended-study-card">
            <h2>추천 학습 설정</h2>
            <p>AI가 추천하는 설정으로 학습을 빠르게 시작해보세요.</p>
            <button className="btn btn-start-new" onClick={handleStartNewStudy}>
              새 학습 시작
            </button>
          </div>
        </div>

        {/* Subscription Status Section */}
        <section className="subscription-section">
          <h2>구독 현황</h2>
          <div className="subscription-card card">
            <p className="subscription-text">프리미엄 플랜 (2025년 9월 20일 까지)</p>
            <button className="btn btn-extend" onClick={handleExtendSubscription}>
              연장하기
            </button>
          </div>
        </section>

      </main>
    </div>
  );
};

export default DashboardPage;