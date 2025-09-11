# utils/parser.py
import fitz  # PyMuPDF
import re
import os

def parse_exam_pdf(file_path: str, problem_id: int = None, start_page: int = None, end_page: int = None) -> dict:
    """
    PDF 파일에서 특정 문제를 파싱하여 구조화된 데이터로 반환
    """
    
    # 파일 존재 여부 확인
    if not os.path.exists(file_path):
        print(f"Error: PDF file not found: {file_path}")
        return None
    
    try:
        doc = fitz.open(file_path)
        
        # 전체 텍스트 추출 (페이지 범위 지정 가능)
        full_text = ""
        start_page = start_page or 0
        end_page = end_page or len(doc)
        
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            full_text += f"\n--- Page {page_num + 1} ---\n"
            full_text += page.get_text("text")
        
        doc.close()
        
        # 현재는 첫 번째 문제의 Mock 데이터 반환 (실제 파싱 로직은 아래 단계에서)
        if problem_id == 101 or problem_id is None:
            return create_mock_data(full_text)
        
        # 실제 파싱 로직 (추후 구현)
        parsed_data = extract_problem_from_text(full_text, problem_id)
        return parsed_data
        
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
        return None

def create_mock_data(full_text: str) -> dict:
    """임시 Mock 데이터 생성 (PDF 텍스트 포함)"""
    # 실제 PDF에서 추출한 텍스트의 일부를 포함
    text_preview = full_text[:200] + "..." if len(full_text) > 200 else full_text
    
    return {
        "passage": f"[실제 PDF 텍스트 미리보기]\n{text_preview}",
        "question": "위 지문에 나타난 화자의 생각으로 가장 적절한 것은?",
        "choices": [
            {"id": 1, "text": "실용적 학문의 중요성"},
            {"id": 2, "text": "전통 문화의 보존"},
            {"id": 3, "text": "서양 문물의 수용"},
            {"id": 4, "text": "민족 정체성의 확립"},
            {"id": 5, "text": "사회 제도의 개혁"}
        ],
        "correct_answer_id": 1,
        "expert_explanation": "화자는 실학자로서 현실적이고 실용적인 학문의 필요성을 강조하고 있습니다. (실제 PDF 파싱 후 정확한 해설로 대체 예정)"
    }

def extract_problem_from_text(full_text: str, problem_id: int) -> dict:
    """실제 PDF 텍스트에서 문제를 추출 (추후 정규표현식으로 구현)"""
    
    # 문제 번호 패턴 찾기
    problem_pattern = rf"{problem_id}\.?\s*(.*?)(?=\d+\.|\Z)"
    
    # 선택지 패턴 (①②③④⑤ or 1.2.3.4.5. 형태)
    choice_pattern = r"[①②③④⑤]|[1-5]\."
    
    # 정답 및 해설 패턴
    answer_pattern = r"정답[:：]\s*([1-5①②③④⑤])"
    explanation_pattern = r"해설[:：]\s*(.*?)(?=\d+\.|\Z)"
    
    # TODO: 실제 정규표현식 파싱 로직 구현
    # 현재는 Mock 데이터 반환
    return create_mock_data(full_text)
