import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatPage from "./ChatPage";
import './QuizPage.css'; // Import the CSS file

const QuizPage = () => {
  const navigate = useNavigate();
  
  // State for the selected multiple-choice answer
  const [selectedAnswer, setSelectedAnswer] = useState(null);

  const [showChat, setShowChat] = useState(false);
  
  // State for the text inputs
  const [answers, setAnswers] = useState(['', '', '', '', '']);

  const handleInputChange = (index, event) => {
    const newAnswers = [...answers];
    newAnswers[index] = event.target.value;
    setAnswers(newAnswers);
  };

  const handleSubmit = () => {
    console.log("문제 제출 버튼 클릭!");
    console.log("선택된 정답:", selectedAnswer);
    console.log("서술형 답안:", answers);
    // You would typically send this data to a server
    // navigate('/results-page');
    // quiz 결과 페이지로 이동
    navigate('/quiz-results');
  };

  const handleGoBack = () => {
    navigate(-1); // Go back to the previous page
  };

  const handleAskAI = () => {
    console.log("AI 선생님에게 질문하기 버튼 클릭!");
    // Implement chat or query functionality
    setShowChat((prev) => !prev); // 토글 방식으로 챗창 켜기/끄기
  };

  const handleStartNew = () => {
    // Reset all state for a new problem
    setSelectedAnswer(null);
    setAnswers(['', '', '', '', '']);
    console.log("새 문제 생성 버튼 클릭!");
    // You might also navigate to a settings page here
    // navigate('/passage-settings');
  };

  return (
    <div className="quiz-container">
      {/* Header Section */}
      <header className="quiz-header">
        <div className="logo">Haeksim</div>
        <nav className="header-nav">
          <a href="/dashboard">대시보드</a>
          <a href="#" className="active">설정</a>
          <a href="#">리포트</a>
          <a href="/">로그아웃</a>
          <img src="path/to/profile-image.jpg" alt="Profile" className="profile-img" />
        </nav>
      </header>

      {/* Main Content */}
      <main className="quiz-main">
        <h1 className="main-title">The Impact of AI on Education</h1>
        
        {/* Passage Section */}
        <section className="passage-section">
          <p>
            Artificial intelligence (AI) is rapidly transforming various sectors, and education is no exception. AI-powered tools are being
            integrated into classrooms to personalize learning experiences, automate administrative tasks, and provide data-driven insights.
            This essay explores the potential benefits and challenges of integrating AI into education, focusing on its impact on
            student learning, teaching practices, and institutional management. One of the primary benefits is the ability to
            offer personalized learning pathways. AI can analyze a student's performance and learning style to provide tailored
            content, suggesting resources, and adjusting the pace and content of instruction accordingly. This personalized approach can lead to improved
            learning outcomes and increased engagement, especially for students who may struggle with traditional teaching methods.
            For example, AI-powered tutoring systems can provide targeted feedback and support, helping students master concepts
            at their own pace. Furthermore, AI can assist teachers with time-consuming tasks such as grading assignments and tracking
            student progress. This allows teachers to focus more on interacting with students, designing innovative lessons, and providing
            one-on-one support. From an administrative perspective, AI can streamline processes such
            as scheduling, enrollment, and resource allocation, making educational institutions more efficient. However, the integration of AI in
            education also presents significant challenges. One concern is the potential for bias in AI algorithms, which could perpetuate
            and even amplify existing educational inequalities. If AI systems are trained on biased data, they may lead to inaccurate
            or unfair assessments of student performance, leading to unequal access to resources and opportunities. Another challenge
            is the ethical use of student data. As AI systems collect vast amounts of personal information, ensuring
            data privacy and security is paramount. Educators and institutions must also receive adequate professional development programs
            are essential to ensure that teachers can leverage the benefits of AI while mitigating its risks. The human element
            in education cannot be replaced by technology. The role of the teacher as a mentor, facilitator, and
            emotional supporter remains crucial. Effective implementation of AI requires a collaborative approach that prioritizes the
            responsible use of AI technologies. In conclusion, AI has the potential to revolutionize education by personalizing learning,
            automating tasks, and streamlining management. However, its successful integration depends on addressing critical ethical
            implications, bias mitigation, and teacher training to ensure that AI is implemented in a way that promotes equity
            and enhances the human-centered nature of education.
          </p>
        </section>

        <p className="question-prompt">
          위 글은 다음 질문을 깊이 있게 다룬 내용이다. 이 글의 주제에 가장 부합하는 것을 고르시오.
        </p>

        {/* Multiple Choice Question */}
        <section className="multiple-choice-section">
          <div className="mc-prompt">이 지문의 주제에 대해 올바른 답을 고르시오.</div>
          <div className="option-group">
            <div 
              className={`mc-option ${selectedAnswer === 1 ? 'selected' : ''}`}
              onClick={() => setSelectedAnswer(1)}
            >
              <div className="mc-radio-button"></div>
              <label>① AI를 교육에 적용하면 어떤 위험이 발생할 수 있는지에 대해 중점적으로 다루는 글이다.</label>
            </div>
            <div 
              className={`mc-option ${selectedAnswer === 2 ? 'selected' : ''}`}
              onClick={() => setSelectedAnswer(2)}
            >
              <div className="mc-radio-button"></div>
              <label>② AI는 교육을 완전히 변화시켜서 교사의 역할은 중요하지 않다고 주장하는 글이다.</label>
            </div>
            <div 
              className={`mc-option ${selectedAnswer === 3 ? 'selected' : ''}`}
              onClick={() => setSelectedAnswer(3)}
            >
              <div className="mc-radio-button"></div>
              <label>③ AI가 교육에 가져올 긍정적인 효과와 부정적인 측면을 모두 균형 있게 다루는 글이다.</label>
            </div>
            <div 
              className={`mc-option ${selectedAnswer === 4 ? 'selected' : ''}`}
              onClick={() => setSelectedAnswer(4)}
            >
              <div className="mc-radio-button"></div>
              <label>④ AI를 교육에 도입할 때 필요한 기술적 준비에 대해 자세히 설명하는 글이다.</label>
            </div>
            <div 
              className={`mc-option ${selectedAnswer === 5 ? 'selected' : ''}`}
              onClick={() => setSelectedAnswer(5)}
            >
              <div className="mc-radio-button"></div>
              <label>⑤ AI가 교육에 가져올 긍정적인 효과만을 강조하며 도입을 촉구하는 글이다.</label>
            </div>
          </div>
        </section>

        {/* Short Answer Section */}
        <section className="short-answer-section">
          {[1, 2, 3, 4, 5].map((num, index) => (
            <div key={num} className="sa-input-group">
              <label>{num} 서술 작성</label>
              <textarea
                value={answers[index]}
                onChange={(e) => handleInputChange(index, e)}
                rows="5"
              ></textarea>
            </div>
          ))}
        </section>

        <div className="char-count">총 작성 글자 수: {answers.join('').length}자</div>

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

        {/* Action Buttons */}
        <div className="action-buttons-container">
          <button className="btn btn-back" onClick={handleGoBack}>뒤로가기</button>
          <button className="btn btn-submit" onClick={handleSubmit}>제출하기</button>
          <button className="btn btn-new-problem" onClick={handleStartNew}>새 문제 생성</button>
        </div>
      </main>
    </div>
  );
};

export default QuizPage;