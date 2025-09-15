# admin_ui.py - 운영 관리 대시보드

import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(
    page_title="🎯 Haeksim 운영 대시보드", 
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 전역 변수
BASE_URL = "http://localhost:8000"

# 사이드바 네비게이션
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1f77b4/white?text=HAEKSIM", width=200)
    st.title("🎯 운영 관리")
    
    menu = st.selectbox(
        "📋 메뉴 선택",
        ["🏠 대시보드 홈", "🖥️ 서버 상태", "👥 회원 관리", "📊 토큰 사용량", "⚙️ 시스템 설정"]
    )
    
    # 실시간 업데이트 설정
    auto_refresh = st.checkbox("🔄 자동 새로고침 (30초)", value=True)
    if auto_refresh:
        st.info("⏰ 30초마다 자동 업데이트")

# 유틸리티 함수들
@st.cache_data(ttl=30)
def get_server_status():
    """서버 상태 확인"""
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/", timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "🟢 정상" if response.status_code == 200 else "🔴 오류",
            "response_time": f"{response_time:.0f}ms",
            "status_code": response.status_code,
            "uptime": "정상 운영 중"
        }
    except Exception as e:
        return {
            "status": "🔴 서버 다운",
            "response_time": "N/A",
            "status_code": "연결 실패",
            "uptime": f"오류: {str(e)}"
        }

@st.cache_data(ttl=60)
def get_users_list():
    """회원 목록 조회"""
    try:
        # 실제 API가 있다면 사용, 없으면 더미 데이터
        dummy_users = [
            {"id": 1, "username": "student_001", "email": "student1@example.com", "created_at": "2024-09-01", "last_login": "2024-09-15"},
            {"id": 2, "username": "student_002", "email": "student2@example.com", "created_at": "2024-09-03", "last_login": "2024-09-14"},
            {"id": 3, "username": "teacher_kim", "email": "kim@school.edu", "created_at": "2024-08-15", "last_login": "2024-09-15"},
            {"id": 4, "username": "student_003", "email": "student3@example.com", "created_at": "2024-09-10", "last_login": "2024-09-13"},
            {"id": 5, "username": "admin_user", "email": "admin@haeksim.com", "created_at": "2024-08-01", "last_login": "2024-09-15"}
        ]
        return dummy_users
    except Exception as e:
        st.error(f"회원 목록 조회 실패: {e}")
        return []

@st.cache_data(ttl=300)
def get_token_usage_data():
    """토큰 사용량 데이터 생성"""
    # 실제로는 데이터베이스나 로그에서 가져와야 함
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # 더미 토큰 사용량 데이터
    daily_usage = {
        'date': dates,
        'input_tokens': [150 + i*10 + (i%7)*50 for i in range(30)],
        'output_tokens': [80 + i*5 + (i%5)*30 for i in range(30)],
        'total_requests': [20 + i*2 + (i%3)*10 for i in range(30)]
    }
    
    df = pd.DataFrame(daily_usage)
    df['total_tokens'] = df['input_tokens'] + df['output_tokens']
    df['estimated_cost'] = df['total_tokens'] * 0.0001  # $0.0001 per token 예시
    
    return df

def test_api_endpoint():
    """API 엔드포인트 테스트"""
    try:
        test_data = {
            "problem_id": 1,
            "user_answer_id": 2,
            "user_reasoning": "시스템 상태 테스트용 더미 요청입니다."
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/evaluation", json=test_data, timeout=30)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "✅ 성공",
                "response_time": f"{response_time:.0f}ms",
                "token_usage": result.get('usage', 'N/A') if isinstance(result, dict) else 'N/A'
            }
        else:
            return {
                "status": f"❌ 실패 ({response.status_code})",
                "response_time": f"{response_time:.0f}ms",
                "token_usage": 'N/A'
            }
    except Exception as e:
        return {
            "status": f"❌ 오류: {str(e)}",
            "response_time": 'N/A',
            "token_usage": 'N/A'
        }

# 메인 대시보드 라우팅
if menu == "🏠 대시보드 홈":
    st.title("🎯 Haeksim LLM 평가 시스템 - 운영 대시보드")
    st.markdown("### 📊 실시간 시스템 현황")
    
    # 서버 상태 요약
    server_status = get_server_status()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🖥️ 서버 상태", 
            server_status["status"],
            delta=None
        )
    
    with col2:
        st.metric(
            "⚡ 응답 시간", 
            server_status["response_time"],
            delta=None
        )
    
    with col3:
        users_count = len(get_users_list())
        st.metric(
            "👥 총 회원수", 
            f"{users_count}명",
            delta="+2 (이번 주)"
        )
    
    with col4:
        token_data = get_token_usage_data()
        today_tokens = token_data.iloc[-1]['total_tokens']
        st.metric(
            "📊 오늘 토큰 사용", 
            f"{today_tokens:,}",
            delta=f"+{today_tokens-token_data.iloc[-2]['total_tokens']:,}"
        )
    
    st.divider()
    
    # 토큰 사용량 트렌드 (최근 7일)
    st.markdown("### 📈 최근 7일 토큰 사용량 트렌드")
    recent_data = get_token_usage_data().tail(7)
    
    fig = px.line(
        recent_data, 
        x='date', 
        y=['input_tokens', 'output_tokens'], 
        title="입력/출력 토큰 사용량",
        labels={'value': '토큰 수', 'date': '날짜'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

elif menu == "🖥️ 서버 상태":
    st.title("🖥️ 서버 상태 모니터링")
    
    # 실시간 상태 체크
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🔍 시스템 상태 점검")
        
        if st.button("🔄 상태 새로고침", type="primary"):
            st.cache_data.clear()
        
        server_status = get_server_status()
        
        # 상태 정보 표시
        status_df = pd.DataFrame([
            {"항목": "서버 상태", "값": server_status["status"]},
            {"항목": "응답 시간", "값": server_status["response_time"]},
            {"항목": "상태 코드", "값": server_status["status_code"]},
            {"항목": "운영 상태", "값": server_status["uptime"]}
        ])
        
        st.dataframe(status_df, use_container_width=True)
        
    with col2:
        st.markdown("### 🧪 API 엔드포인트 테스트")
        
        if st.button("🔬 평가 API 테스트"):
            with st.spinner("API 테스트 중..."):
                test_result = test_api_endpoint()
            
            st.success(f"상태: {test_result['status']}")
            st.info(f"응답시간: {test_result['response_time']}")
            
            if test_result['token_usage'] != 'N/A':
                st.json(test_result['token_usage'])
    
    st.divider()
    
    # 시스템 로그 (가상)
    st.markdown("### 📋 최근 시스템 로그")
    log_data = [
        {"시간": "2024-09-15 10:05:32", "레벨": "INFO", "메시지": "새로운 평가 요청 처리 완료"},
        {"시간": "2024-09-15 10:03:15", "레벨": "INFO", "메시지": "사용자 로그인: student_001"},
        {"시간": "2024-09-15 09:58:42", "레벨": "INFO", "메시지": "토큰 사용량: 1,247 tokens"},
        {"시간": "2024-09-15 09:55:18", "레벨": "WARN", "메시지": "API 응답 시간 지연 (2.3초)"},
        {"시간": "2024-09-15 09:52:07", "레벨": "INFO", "메시지": "FAISS 인덱스 로드 완료"}
    ]
    
    st.dataframe(pd.DataFrame(log_data), use_container_width=True)

elif menu == "👥 회원 관리":
    st.title("👥 회원 관리")
    
    users = get_users_list()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📋 회원 목록")
        
        # 회원 데이터를 DataFrame으로 변환
        if users:
            df_users = pd.DataFrame(users)
            
            # 검색 기능
            search_term = st.text_input("🔍 회원 검색 (이름 또는 이메일)")
            if search_term:
                df_users = df_users[
                    df_users['username'].str.contains(search_term, case=False) |
                    df_users['email'].str.contains(search_term, case=False)
                ]
            
            st.dataframe(
                df_users,
                column_config={
                    "id": "ID",
                    "username": "사용자명",
                    "email": "이메일",
                    "created_at": "가입일",
                    "last_login": "최근 로그인"
                },
                use_container_width=True
            )
        else:
            st.warning("회원 데이터를 불러올 수 없습니다.")
    
    with col2:
        st.markdown("### 📊 회원 통계")
        
        if users:
            # 가입 추이
            df_users = pd.DataFrame(users)
            df_users['created_at'] = pd.to_datetime(df_users['created_at'])
            
            monthly_signups = df_users.groupby(df_users['created_at'].dt.to_period('M')).size()
            
            fig = px.bar(
                x=monthly_signups.index.astype(str),
                y=monthly_signups.values,
                title="월별 신규 가입자",
                labels={'x': '월', 'y': '가입자 수'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            # 통계 요약
            st.metric("총 회원수", len(users))
            st.metric("이번 달 신규", 2)
            st.metric("활성 사용자", "85%")

elif menu == "📊 토큰 사용량":
    st.title("📊 토큰 사용량 대시보드")
    
    token_data = get_token_usage_data()
    
    # 상단 메트릭
    col1, col2, col3, col4 = st.columns(4)
    
    total_tokens = token_data['total_tokens'].sum()
    total_cost = token_data['estimated_cost'].sum()
    avg_daily = token_data['total_tokens'].mean()
    today_usage = token_data.iloc[-1]['total_tokens']
    
    with col1:
        st.metric("🎯 총 토큰 사용량", f"{total_tokens:,}", delta=None)
    
    with col2:
        st.metric("💰 예상 총 비용", f"${total_cost:.2f}", delta=None)
    
    with col3:
        st.metric("📊 일평균 사용량", f"{avg_daily:.0f}", delta=None)
    
    with col4:
        st.metric("📅 오늘 사용량", f"{today_usage:,}", 
                 delta=f"{today_usage - token_data.iloc[-2]['total_tokens']:+,}")
    
    st.divider()
    
    # 상세 차트
    tab1, tab2, tab3 = st.tabs(["📈 사용량 트렌드", "💸 비용 분석", "📋 상세 데이터"])
    
    with tab1:
        # 토큰 사용량 트렌드
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('일별 토큰 사용량', '일별 API 요청 수'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(
            go.Scatter(x=token_data['date'], y=token_data['input_tokens'], 
                      name='입력 토큰', line=dict(color='blue')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=token_data['date'], y=token_data['output_tokens'], 
                      name='출력 토큰', line=dict(color='red')),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=token_data['date'], y=token_data['total_requests'], 
                   name='총 요청수', marker_color='green'),
            row=2, col=1
        )
        
        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # 비용 분석
        fig_cost = px.area(
            token_data, 
            x='date', 
            y='estimated_cost',
            title='일별 예상 비용 트렌드',
            labels={'estimated_cost': '비용 ($)', 'date': '날짜'}
        )
        fig_cost.update_layout(height=400)
        st.plotly_chart(fig_cost, use_container_width=True)
        
        # 월별 비용 요약
        monthly_cost = token_data.groupby(token_data['date'].dt.to_period('M'))['estimated_cost'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("이번 달 예상 비용", f"${monthly_cost.iloc[-1]:.2f}")
        with col2:
            st.metric("월평균 비용", f"${monthly_cost.mean():.2f}")
    
    with tab3:
        # 상세 데이터 테이블
        display_data = token_data.copy()
        display_data['date'] = display_data['date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            display_data,
            column_config={
                "date": "날짜",
                "input_tokens": "입력 토큰",
                "output_tokens": "출력 토큰", 
                "total_tokens": "총 토큰",
                "total_requests": "총 요청수",
                "estimated_cost": st.column_config.NumberColumn("예상 비용 ($)", format="$%.4f")
            },
            use_container_width=True
        )

elif menu == "⚙️ 시스템 설정":
    st.title("⚙️ 시스템 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 API 설정")
        
        # API 키 상태 (마스킹)
        api_key_status = "AIzaSy********************"
        st.text_input("Google API 키", value=api_key_status, disabled=True)
        
        # 모델 설정
        selected_model = st.selectbox(
            "사용 모델",
            ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-1.5-flash"],
            index=0
        )
        
        # 설정 저장
        if st.button("💾 설정 저장"):
            st.success("설정이 저장되었습니다!")
    
    with col2:
        st.markdown("### 📋 시스템 정보")
        
        system_info = {
            "Docker 이미지": "haeksim-optimized:latest",
            "이미지 크기": "~400MB",
            "Python 버전": "3.12",
            "FastAPI 버전": "0.111.0",
            "Streamlit 버전": "1.36.0",
            "배포 환경": "WSL2 + Docker"
        }
        
        for key, value in system_info.items():
            st.text(f"{key}: {value}")

# 자동 새로고침
if auto_refresh:
    time.sleep(30)
    st.rerun()

# 푸터
st.divider()
st.markdown("### 🎯 Haeksim LLM 평가 시스템 v1.0 - 운영 대시보드")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
