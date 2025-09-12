import logo from './logo.svg';

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Page1 from './pages/Page1'; 
import DashboardPage from './pages/DashboardPage';
import PassageSettingsPage from './pages/PassageSettingsPage';
import QuizPage from './pages/QuizPage';
import QuizResultPage from './pages/QuizResultPage';
import SummaryPracticePage from './pages/SummaryPracticePage';
import LearningAnalysisPage from './pages/LearningAnalysisPage';
import SignUpPage from './pages/SignUpPage';
import HomePage from './pages/HomePage';

const App = () => {
  return (
    <div className="App">
      <Routes>
        <Route path="/dashboard" element={<DashboardPage />} /> {/* 대시보드 화면 */}
        <Route path="/page1" element={<Page1 />} /> {/* 로그인 화면 */}
        <Route path="/" element={<HomePage />} /> {/* 온보딩 화면 */}
        <Route path="/passage-settings" element={<PassageSettingsPage />} /> {/* 지문 설정 화면 */}
        <Route path="/quiz-page" element={<QuizPage />} /> {/* 퀴즈 페이지 화면 */}
        <Route path="/summary-practice" element={<SummaryPracticePage />} /> {/* 요약 연습하기 화면 */}
        <Route path="/quiz-results" element={<QuizResultPage />} /> {/* 퀴즈 결과 페이지 화면 */}
        <Route path="/learning-analysis" element={<LearningAnalysisPage />} /> {/* 학습 분석 페이지 화면 */}
        <Route path="/sign-up" element={<SignUpPage />} /> {/* 회원가입 페이지 화면 */}
      </Routes>
    </div>
  );
};

export default App;
