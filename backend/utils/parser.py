# utils/parser.py (전체 파일)
import fitz  # PyMuPDF
import re
import os

def debug_pdf_content(file_path: str):
    """PDF 내용 디버깅용 함수"""
    try:
        print(f"=== PDF Debug Info for: {file_path} ===")
        
        # 파일 존재 및 크기 확인
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        file_size = os.path.getsize(file_path)
        print(f"📁 File size: {file_size:,} bytes")
        
        doc = fitz.open(file_path)
        print(f"📄 Total pages: {len(doc)}")
        
        # 첫 3페이지의 텍스트 미리보기
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            page_text = page.get_text("text")
            print(f"\n--- Page {page_num + 1} (first 300 chars) ---")
            print(page_text[:300])
            print("...")
        
        doc.close()
        print("=== Debug Complete ===")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")

def find_problems_in_text(text: str) -> list:
    """텍스트에서 모든 문제 번호 찾기"""
    
    # 다양한 문제 번호 패턴 시도
    patterns = [
        r"\d{1,3}\.?\s*\[",      # "1. [" 형태
        r"\d{1,3}\.?\s*다음",     # "1. 다음" 형태  
        r"\d{1,3}\.?\s*위",      # "1. 위" 형태
        r"\d{1,3}\.?\s*글",      # "1. 글" 형태
        r"\d{1,3}\.\s*.*?다음",   # "1. ... 다음" 형태
    ]
    
    found_problems = []
    for i, pattern in enumerate(patterns):
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # 문제 번호 추출
            number_match = re.search(r"\d{1,3}", match.group())
            if number_match:
                problem_number = int(number_match.group())
                found_problems.append({
                    'number': problem_number,
                    'pattern_type': i,
                    'position': match.start(),
                    'matched_text': match.group(),
                    'context': text[match.start():match.start()+100]
                })
    
    # 문제 번호로 정렬하고 중복 제거
    unique_problems = {}
    for problem in found_problems:
        num = problem['number']
        if num not in unique_problems:
            unique_problems[num] = problem
    
    return sorted(unique_problems.values(), key=lambda x: x['number'])

def parse_exam_pdf(file_path: str, problem_id: int = None, start_page: int = None, end_page: int = None) -> dict:
    try:
        doc = fitz.open(file_path)
        
        # 텍스트 추출 방식 개선
        full_text = ""
        for page_num in range(start_page, min(end_page, len(doc))):
            page = doc[page_num]
            # 다양한 텍스트 추출 방식 시도
            try:
                # 기본 텍스트 추출
                page_text = page.get_text("text")
                # 만약 텍스트가 너무 적거나 깨진 것 같으면 다른 방식 시도
                if len(page_text.strip()) < 50:
                    page_text = page.get_text("dict")  # 더 상세한 정보 추출
                    # dict에서 텍스트만 추출하는 로직 추가 가능
                
                full_text += f"\n--- Page {page_num + 1} ---\n"
                full_text += page_text
            except Exception as e:
                print(f"Warning: Failed to extract text from page {page_num + 1}: {e}")
        
        doc.close()
        
        # 📊 디버깅: PDF 내용 분석
        print(f"📊 Total extracted text length: {len(full_text)} characters")
        
        # 📊 문제 번호들 찾기
        found_problems = find_problems_in_text(full_text)
        print(f"🔍 Found {len(found_problems)} potential problems:")
        for prob in found_problems[:5]:  # 처음 5개만 출력
            print(f"   Problem {prob['number']}: {prob['matched_text']}")
        
        # problem_id가 101이거나 None이면 Mock 데이터 + 실제 텍스트 미리보기
        if problem_id == 101 or problem_id is None:
            return create_mock_data_with_preview(full_text, found_problems)
        
        # 실제 문제 추출 시도 (아직 구현 중)
        parsed_data = extract_specific_problem(full_text, problem_id, found_problems)
        return parsed_data if parsed_data else create_mock_data_with_preview(full_text, found_problems)
        
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
        return None

def create_mock_data_with_preview(full_text: str, found_problems: list) -> dict:
    """실제 PDF 내용을 포함한 Mock 데이터 생성"""
    
    # 실제 PDF에서 추출한 텍스트의 일부를 포함
    text_preview = full_text[:500] + "..." if len(full_text) > 500 else full_text
    
    # 발견된 문제 번호들 정보 
    problems_info = ", ".join([str(p['number']) for p in found_problems[:10]])
    
    return {
        "passage": f"[실제 PDF에서 추출된 텍스트 미리보기]\n\n{text_preview}",
        "question": f"위 지문에 나타난 내용으로 가장 적절한 것은? (발견된 문제들: {problems_info})",
        "choices": [
            {"id": 1, "text": "실용적 학문의 중요성"},
            {"id": 2, "text": "전통 문화의 보존"},
            {"id": 3, "text": "서양 문물의 수용"},
            {"id": 4, "text": "민족 정체성의 확립"},
            {"id": 5, "text": "사회 제도의 개혁"}
        ],
        "correct_answer_id": 1,
        "expert_explanation": f"실제 PDF 파싱 결과입니다. 전체 텍스트 길이: {len(full_text)}자, 발견된 문제 개수: {len(found_problems)}개"
    }

def extract_specific_problem(full_text: str, problem_id: int, found_problems: list) -> dict:
    """특정 문제 번호의 내용을 추출 (향후 구현)"""
    
    # 해당 problem_id가 발견된 문제 목록에 있는지 확인
    target_problem = None
    for prob in found_problems:
        if prob['number'] == problem_id:
            target_problem = prob
            break
    
    if not target_problem:
        print(f"❌ Problem {problem_id} not found in PDF")
        return None
    
    print(f"🎯 Found target problem {problem_id} at position {target_problem['position']}")
    
    # TODO: 실제 문제 텍스트 추출 로직 구현
    # 현재는 None 반환하여 Mock 데이터 사용
    return None
