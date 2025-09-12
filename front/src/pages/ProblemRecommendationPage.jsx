import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // API 통신을 위해 axios를 임포트합니다.

// API 주소는 환경 변수에서 가져오는 것이 좋습니다.
// const API_URL = process.env.REACT_APP_API_URL;

const ProblemRecommendationPage = () => {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [isFinding, setIsFinding] = useState(false);
  const [error, setError] = useState('');

  // '문제 찾기' 버튼을 눌렀을 때 실행될 함수
  const handleFindProblems = async () => {
    if (input.trim() === '') {
      setError('요청 내용을 입력해주세요.');
      return;
    }

    setError('');
    setIsFinding(true); // 로딩 상태 시작

    try {
      // 1. 여기에 AI에게 요청을 보내는 API 통신 로직을 작성합니다.
      // 예시: axios.post(`${API_URL}/find-problems`, { prompt: input });
      
      // 실제 API 호출 대신, 2초간의 로딩을 시뮬레이션합니다.
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      console.log('문제 찾기 요청:', input);
      
      // 2. 요청이 성공하면 다음 페이지로 이동합니다.
      // 예시: navigate('/problem-solving-page', { state: { problems: response.data.problems } });
      navigate('/problems');
      
    } catch (err) {
      // 3. 에러 발생 시 처리
      console.error('문제 찾기 실패:', err);
      setError('문제 추천 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setIsFinding(false); // 로딩 상태 종료
    }
  };

  const handleKeyPress = (e) => {
    // Shift + Enter로 줄바꿈을 허용하고, Enter 키만 눌렀을 때 전송
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // 기본 Enter 동작(줄바꿈) 방지
      handleFindProblems();
    }
  };

  return (
    <div className="pr-container">
      <header className="pr-header">
        <h1 className="pr-title">어떤 유형의 문제를 더 풀어보고 싶나요?</h1>
        <p className="pr-subtitle">원하는 주제나 난이도를 자유롭게 말씀해주세요</p>
      </header>
      
      <main className="pr-main">
        <div className="pr-examples">
          <p className="pr-tip">💡 자세할수록 좋아요!</p>
          <p className="pr-tip-emoji">✍️ 예시:</p>
          <ul>
            <li>"방금 푼 것과 비슷한 주제로 더 어렵게"</li>
            <li>"과학 기술 관련 중급 난이도로"</li>
            <li>"경제 지문으로 요약 연습하고 싶어"</li>
          </ul>
        </div>
        
        <div className="pr-textarea-container">
          <textarea
            className="pr-textarea"
            placeholder="텍스트필드"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
          ></textarea>
        </div>
      </main>

      <footer className="pr-footer">
        <div className="pr-input-area">
          <input 
            type="text" 
            placeholder="Type your response here..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button 
            onClick={handleFindProblems} 
            disabled={isFinding}
            className="pr-submit-btn"
          >
            {isFinding ? '문제 찾는 중...' : '문제 찾기'}
          </button>
        </div>
      </footer>
    </div>
  );
};

export default ProblemRecommendationPage;