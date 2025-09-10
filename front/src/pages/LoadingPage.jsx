import React from 'react';
import './LoadingPage.css';

const LoadingPage = () => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>데이터를 불러오는 중입니다...</p>
    </div>
  );
};

export default LoadingPage;