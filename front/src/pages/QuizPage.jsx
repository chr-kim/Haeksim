import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom'; // useLocation 추가
import ChatPage from "./ChatPage";
import './QuizPage.css';

const QuizPage = () => {
  const navigate = useNavigate();
  const location = useLocation(); // location 객체 가져오기

  // location.state에서 quizData 추출
  const quizData = location.state?.quizData;

  // State for the passage, title and options
  const [title, setTitle] = useState('');
  const [passage, setPassage] = useState('');
  const [options, setOptions] = useState([]);
  
  const option_numbers = ['①', '②', '③', '④', '⑤'];

  // State for the selected multiple-choice answer
  const [selectedAnswer, setSelectedAnswer] = useState(null);

  const [showChat, setShowChat] = useState(false);

  // State for the text inputs
  const [answers, setAnswers] = useState(['', '', '', '', '']);

  // State for checking if all answers are filled out
  const [isSubmitEnabled, setIsSubmitEnabled] = useState(false);
  
  // State to track completed questions for progress bar
  const [completedQuestions, setCompletedQuestions] = useState(0);

  // Set data from location state when component mounts
  useEffect(() => {
    if (quizData) {
      // API 응답 형식에 맞게 데이터 설정
      setTitle(quizData.title || '제목 없음');
      setPassage(quizData.passage || '내용 없음');
      setOptions(quizData.choices || []);
      setAnswers(new Array(quizData.choices?.length || 5).fill(''));
    } else {
      // quizData가 없을 경우 (예: 페이지 직접 접근)
      setTitle('오류');
      setPassage('퀴즈 데이터를 불러올 수 없습니다. 설정 페이지에서 다시 시도해주세요.');
      setOptions([]);
    }
  }, [quizData]);


  // Check if all answers are filled whenever `answers` state changes
  useEffect(() => {
    if (!answers.length) return;
    // 모든 서술형 답안과 객관식 답안이 모두 채워졌는지 확인
    const allShortAnswersFilled = answers.every(answer => answer.trim() !== '');
    const isMultipleChoiceSelected = selectedAnswer !== null;

    if (allShortAnswersFilled && isMultipleChoiceSelected) {
      setIsSubmitEnabled(true);
    } else {
      setIsSubmitEnabled(false);
    }
    
    // Calculate completed questions for progress bar
    const shortAnswersCompleted = answers.filter(answer => answer.trim() !== '').length;
    const multipleChoiceCompleted = selectedAnswer !== null ? 1 : 0;
    setCompletedQuestions(shortAnswersCompleted + multipleChoiceCompleted);
  }, [answers, selectedAnswer]); // answers와 selectedAnswer가 바뀔 때마다 실행

  const handleInputChange = (index, event) => {
    const newAnswers = [...answers];
    newAnswers[index] = event.target.value;
    setAnswers(newAnswers);
  };

  const handleMultipleChoiceClick = (option) => {
    setSelectedAnswer(option);
  };

  const handleSubmit = () => {
    if (!isSubmitEnabled) {
      alert("모든 문제를 풀어야 제출할 수 있습니다.");
      return;
    }
    
    console.log("문제 제출 버튼 클릭!");
    console.log("선택된 정답:", selectedAnswer);
    console.log("서술형 답안:", answers);
    // You would typically send this data to a server
    navigate('/quiz-results');
  };

  const handleGoBack = () => {
    navigate(-1); // Go back to the previous page
  };

  const handleAskAI = () => {
    console.log("AI 선생님에게 질문하기 버튼 클릭!");
    setShowChat((prev) => !prev);
  };

  const totalQuestions = (options?.length || 0) + 1; // short answers + 1 multiple choice

  return (
    <div className="quiz-container">
      {/* Header Section */}
      <header className="quiz-header">
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
      <main className="quiz-main">
        <div className="quiz-content-grid">
          <div className="quiz-problem-panel">
            <h1 className="main-title">{title}</h1>
            

            {/* Passage Section */}
            <section className="passage-section">
              <p>
                {passage}
              </p>
            </section>

            <p className="question-prompt">
              위 글은 다음 질문을 깊이 있게 다룬 내용이다. 이 글의 주제에 가장 부합하는 것을 고르시오.
            </p>

            {/* Multiple Choice Question */}
            <section className="multiple-choice-section">
              <div className="mc-prompt">이 지문의 주제에 대해 올바른 답을 고르시오.</div>
              <div className="option-group">
                {options.map((option, index) => (
                  <div 
                    key={index + 1}
                    className={`mc-option ${selectedAnswer === index + 1 ? 'selected' : ''}`}
                    onClick={() => handleMultipleChoiceClick(index + 1)}
                  >
                    <label>
                      {`${option_numbers[index]} ${option}`}
                    </label>
                  </div>
                ))}
              </div>
            </section>
          </div>
          <div className="quiz-answer-panel">
            {/* Short Answer Section */}
            <section className="short-answer-section">
              <div className="short-answer-title">선택지별 근거 작성</div>
              <div className="short-answer-description">
                각 선택지에 대한 근거를 서술하세요. ({options.length}문제)
              </div>
              {options.map((option, index) => (
                <div key={index + 1} className="sa-input-group-container">
                  <div className="sa-input-group">
                    <label><strong>{`${option_numbers[index]} ${option}`}</strong>에 대한 근거</label>
                    <textarea
                      placeholder="이 선택지를 고른 이유(근거)를 지문에서 찾아 작성해주세요."
                      value={answers[index] || ''}
                      onChange={(e) => handleInputChange(index, e)}
                      rows="5"
                    ></textarea>
                  </div>
                  <div className="char-count">작성 글자 수: {answers[index]?.length || 0}자</div>
                </div>
              ))} 
            </section>

            <div className="char-count total-char-count">총 작성 글자 수: {answers.join('').length}자</div>

            <div className="ai-teacher-section">
              <button className="btn btn-ask-ai" onClick={handleAskAI}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                AI 선생님에게 질문하기
              </button>
            </div>
            {showChat && (
            <div className="chat-popup">
              <ChatPage isPopup={true} />
            </div>
            )}

            {/* Progress Bar Section */}
            <section className="progress-section">
              <div className="progress-text">{completedQuestions} / {totalQuestions} 완료</div>
              <progress className="progress-bar" value={completedQuestions} max={totalQuestions}></progress>
            </section>

            {/* Action Buttons */}
            <div className="action-buttons-container">
              <button className="btn btn-back" onClick={handleGoBack}>뒤로가기</button>
              <button className="btn btn-submit" onClick={handleSubmit} disabled={!isSubmitEnabled}>
                제출하기
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default QuizPage;
