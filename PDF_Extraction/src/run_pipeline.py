"""ESG 보고서 파이프라인 전체 실행 스크립트.

순차 실행 단계
1. PDF 인코딩 보정 여부 체크 (자동)
2. Docling 구조화 추출 (실패 페이지는 GPT Vision Fallback)
3. 표 텍스트 추출(OCR/PyMuPDF)
4. 그림 GPT 설명 (옵션으로 skip 가능: --skip-gpt 플래그)
5. 표 숫자 검증(diff 체크)
6. MySQL 적재 (옵션 --load-db 플래그)
7. 벡터 DB 구축 (옵션 --build-vector-db 플래그)
8. 벡터 검색 테스트 (옵션  --search-queries 플래그)

예시: 실행 파일 이름 명시해줘야함 
    python src/run_pipeline.py --pdf data/input/2024_Samsung_Report.pdf --doc-name Samsung2024 \
        --load-db --build-vector-db --search-queries "hybrid::탄소 배출" "semantic::재생에너지 계획"
"""

import argparse
import subprocess
import sys
from pathlib import Path

import pypdfium2 as pdfium
import os
from dotenv import load_dotenv

load_dotenv()

# 실행할 개별 스크립트 경로 정의
SRC_DIR = Path(__file__).parent.resolve()
SCRIPT_PDF_EXTRACTOR = SRC_DIR / "pdf_text_extractor.py"
SCRIPT_STRUCTURED = SRC_DIR / "structured_extract.py"
SCRIPT_TABLE_OCR = SRC_DIR / "table_ocr.py"
SCRIPT_FIGURE_OCR = SRC_DIR / "figure_ocr.py"
SCRIPT_TABLE_DIFF = SRC_DIR / "table_diff.py"
SCRIPT_LOAD_DB = SRC_DIR / "load_to_db.py"
SCRIPT_BUILD_VECTOR = SRC_DIR / "build_vector_db.py"
SCRIPT_SEARCH_VECTOR = SRC_DIR / "search_vector_db.py"


def run_command(cmd: list[str], description: str):
    """하위 스크립트를 공통 포맷으로 실행."""
    print(f"\n{'='*60}")
    print(f"🚀 [Pipeline] Starting: {description}")
    print(f"   Command: {' '.join(str(c) for c in cmd)}")
    print(f"{'='*60}\n")
    
    try:
        # Stream output to stdout
        result = subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ [Pipeline] Failed at step: {description}")
        print(f"   Exit Code: {e.returncode}")
        print("   Aborting pipeline.")
        sys.exit(e.returncode)
    
    print(f"\n✅ [Pipeline] Completed: {description}\n")


def main():
    parser = argparse.ArgumentParser(description="ESG 전체 파이프라인 실행기")
    parser.add_argument("--pdf", type=Path, required=True, help="입력 PDF 경로")
    parser.add_argument("--pages", type=str, default=None, help="처리할 페이지 범위 (예: 1-10, 25)")
    parser.add_argument("--doc-name", type=str, default=None, help="결과 폴더/DB에 사용할 문서 이름 (기본: PDF 파일명(stem))")
    
    # Feature Flags
    parser.add_argument("--skip-sanitize", action="store_true", help="Skip the PDF sanitization check step")
    parser.add_argument("--skip-gpt", action="store_true", help="Skip GPT-based figure description")
    parser.add_argument("--load-db", action="store_true", help="Load results into MySQL database after processing")
    parser.add_argument("--init-db", action="store_true", help="Initialize DB schema before loading (use with --load-db)")

    # 추가 기능: 벡터 DB 구축 + 검색 자동화
    parser.add_argument("--build-vector-db", action="store_true", help="테이블/그림 적재 후 벡터 DB도 즉시 구축")
    parser.add_argument("--reset-vector-db", action="store_true", help="벡터 DB를 초기화하고 재구축 (주의)")
    parser.add_argument("--remote-host", type=str, default=os.getenv("CHROMA_HOST", None), help="원격 Chroma 서버 호스트 (기본: 환경변수 CHROMA_HOST)")
    parser.add_argument("--remote-port", type=int, default=os.getenv("CHROMA_PORT", None), help="원격 Chroma 서버 포트 (기본: 환경변수 CHROMA_PORT)")
    parser.add_argument("--company", type=str, default=None, help="벡터 DB 파이프라인 진행시 필터링할 회사명")
    parser.add_argument("--year", type=int, default=None, help="벡터 DB 파이프라인 진행시 필터링할 연도")
    parser.add_argument(
        "--search-queries",
        nargs="*",
        default=None,
        help="벡터 검색을 함께 수행할 질의 목록. 'mode::query' 형태로 개별 모드 지정 가능",
    )
    parser.add_argument(
        "--search-mode",
        choices=("semantic", "keyword", "hybrid"),
        default="semantic",
        help="search-queries에 모드가 명시되지 않았을 때 사용할 기본 모드",
    )
    parser.add_argument("--search-top-k", type=int, default=5, help="검색 결과 개수")
    
    args = parser.parse_args()

    # 0. Validate Input
    if not args.pdf.exists():
        print(f"Error: Input PDF not found: {args.pdf}")
        sys.exit(1)
        
    pdf_path = args.pdf.resolve()
    
    # 1. PDF Sanitization (Step 0)
    # The pdf_text_extractor.py tool handles the check logic internally.
    # It returns 0 if fine, or creates a sanitized file if needed.
    # However, structured_extract.py has logic to auto-switch to sanitized file.
    # WE MUST RUN sanitization check unless skipped.
    if not args.skip_sanitize:
        cmd_sanitize = [sys.executable, str(SCRIPT_PDF_EXTRACTOR), "--pdf", str(pdf_path)]
        # We don't check=True here because the script might return non-zero on error,
        # but current logic returns 1 on failure. We want to stop if sanitization fails.
        # But wait, pdf_text_extractor returns 0 on [Pass] as well. So check=True is fine.
        run_command(cmd_sanitize, "Step 0: PDF Sanitization Check")
    
    # Note: structured_extract.py has auto-switch logic, so we just pass the ORIGINAL path.
    # It will pick up the sanitized file if it exists.

    if args.pages:
        page_selection = args.pages
    else:
        pdf_doc = pdfium.PdfDocument(str(pdf_path))
        total_pages = len(pdf_doc)
        pdf_doc.close()
        page_selection = f"1-{total_pages}"

    # 2. Structured Extraction
    cmd_struct = [
        sys.executable,
        str(SCRIPT_STRUCTURED),
        "--pdf",
        str(pdf_path),
        "--pages",
        page_selection,
    ]
        
    # 구조화 결과 폴더명을 doc_name으로 고정 (PDF 이름 기반)
    doc_name = args.doc_name or pdf_path.stem
    cmd_struct.extend(["--report-name", doc_name])

    run_command(cmd_struct, "Step 1: Docling Structured Extraction")
    
    # 3. Table OCR
    # Now we know exactly where the pages are: data/pages_structured/{doc_name}
    target_page_dir = Path("data/pages_structured") / doc_name
    
    cmd_tocr = [sys.executable, str(SCRIPT_TABLE_OCR)]
    if page_selection:
        cmd_tocr.extend(["--pages", page_selection])
    
    # 표 추출은 구조화 폴더를 명시적으로 지정
    cmd_tocr.extend(["--structured-dir", str(target_page_dir)])
    cmd_tocr.extend(["--pdf", str(pdf_path)]) 
    
    run_command(cmd_tocr, "Step 2: Table Text Extraction (OCR/PDF)")
    
    # 4. Figure OCR
    if not args.skip_gpt:
        cmd_fig = [sys.executable, str(SCRIPT_FIGURE_OCR), "--model", "gpt-4o-mini"]
        if page_selection:
            cmd_fig.extend(["--pages", page_selection])
        cmd_fig.extend(["--structured-dir", str(target_page_dir)]) # Ensure we point to correct folder
        run_command(cmd_fig, "Step 3: Figure Description (GPT)")
    
    # 5. Table Diff
    cmd_diff = [sys.executable, str(SCRIPT_TABLE_DIFF)]
    if page_selection:
        cmd_diff.extend(["--pages", page_selection])
    cmd_diff.extend(["--structured-dir", str(target_page_dir)])
    run_command(cmd_diff, "Step 4: Table Validation (Diff)")
    
    # 6. DB 적재
    if args.load_db:
        cmd_load = [sys.executable, str(SCRIPT_LOAD_DB), "--doc-name", doc_name]
        if args.init_db:
            cmd_load.append("--init-db")
        # Ensure loading script knows where to look
        cmd_load.extend(["--input-dir", str(target_page_dir)])
        
        run_command(cmd_load, "Step 5: Database Loading")

    # 7. 벡터 DB 구축 (옵션)
    build_vector_flag = args.build_vector_db or (args.search_queries is not None and len(args.search_queries) > 0)
    if build_vector_flag:
        print("\n💡 벡터 DB는 DB 적재된 데이터를 기반으로 하므로 load_db 실행을 권장합니다.")
        cmd_vector = [sys.executable, str(SCRIPT_BUILD_VECTOR)]
        if args.reset_vector_db:
            cmd_vector.append("--reset")
        if args.remote_host:
            cmd_vector.extend(["--remote-host", args.remote_host])
        if args.remote_port:
            cmd_vector.extend(["--remote-port", str(args.remote_port)])
        if args.company:
            cmd_vector.extend(["--company", args.company])
        if args.year:
            cmd_vector.extend(["--year", str(args.year)])
        
        run_command(cmd_vector, "Step 6: Vector DB Build")

    # 8. 벡터 검색 (옵션)
    if args.search_queries:
        for raw_query in args.search_queries:
            if "::" in raw_query:
                mode, query = raw_query.split("::", 1)
                mode = mode.strip() or args.search_mode
            else:
                mode = args.search_mode
                query = raw_query
            query = query.strip()
            if not query:
                continue
            cmd_search = [
                sys.executable,
                str(SCRIPT_SEARCH_VECTOR),
                query,
                "--top-k",
                str(args.search_top_k),
                "--mode",
                mode,
            ]
            desc = f"Step 7: Vector Search ({mode} :: {query})"
            run_command(cmd_search, desc)

    print("\n✨ [Pipeline] 모든 단계 완료")
    print(f"   - 결과 폴더: {target_page_dir}")
    if args.load_db:
        print(f"   - DB 적재 문서명: {doc_name}")


if __name__ == "__main__":
    main()
