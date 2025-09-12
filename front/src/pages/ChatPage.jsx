import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';


const ChatPage = ({ isPopup = false }) => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    { text: '안녕하세요, 무엇을 도와드릴까요?', sender: 'AI Tutor', avatar: 'path/to/ai-avatar-1.jpg' },
    { text: '핵심어 정확도가 왜 90% 인가요?', sender: 'Student', avatar: 'path/to/student-avatar.jpg' },
    { text: '사용하신 핵심어들이 지문의 주요 내용을 잘 반영하고 있습니다.', sender: 'AI Tutor', avatar: 'path/to/ai-avatar-2.jpg' },
  ]);
  const [input, setInput] = useState('');

  const handleSendMessage = () => {
    if (input.trim() === '') return;

    // Simulate sending a message
    const newMessage = { text: input, sender: 'Student', avatar: 'path/to/student-avatar.jpg' };
    setMessages([...messages, newMessage]);
    setInput('');

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = { text: '잠시만요...', sender: 'AI Tutor', avatar: 'path/to/ai-avatar-1.jpg' };
      setMessages(prevMessages => [...prevMessages, aiResponse]);
    }, 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      {!isPopup && (
        <header className="chat-header">
          <h1 className="main-title">인공지능 선생님</h1>
          <nav className="header-nav">
            <a href="#">대시보드</a>
            <a href="#">설정</a>
            <a href="#">리포트</a>
            <a href="#">로그아웃</a>
            <img src="path/to/student-avatar.jpg" alt="Profile" className="profile-img" />
          </nav>
        </header>
      )}

      <main className="chat-main">
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div 
              key={index} 
              className={`message-bubble-container ${msg.sender === 'Student' ? 'student-message' : 'ai-message'}`}
            >
              <img src={msg.avatar} alt={`${msg.sender} avatar`} className="avatar" />
              <div className="message-bubble">
                <div className="message-text">{msg.text}</div>
              </div>
            </div>
          ))}
        </div>
      </main>

      <div className="chat-input-area">
        <input 
          type="text" 
          placeholder="Type your response here..." 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <button onClick={handleSendMessage}>전송</button>
      </div>
    </div>
  );
};

export default ChatPage;
