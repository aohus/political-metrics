import asyncio
import glob
import os
from datetime import datetime
from pathlib import Path

from .analyzer import AsyncPoliticalBillAnalyzer, progress_callback


async def analyze_massive_directory(directory_path, output_path, batch_size=100):
    analyzer = AsyncPoliticalBillAnalyzer(max_concurrent_tasks=50)

    try:
        pdf_files = list(Path(directory_path).rglob("*.json"))
        print(f"총 {len(pdf_files)}개 PDF 파일 발견")

        all_results = []

        # 배치 단위로 처리
        for i in range(0, len(pdf_files), batch_size):
            batch_files = pdf_files[i : i + batch_size]
            batch_paths = [str(f) for f in batch_files]

            print(f"\n배치 {i//batch_size + 1}/{(len(pdf_files) + batch_size - 1)//batch_size} 처리 중...")
            batch_results = await analyzer.analyze_multiple_bills(batch_paths)
            all_results.extend(batch_results)

            # 중간 저장 (메모리 절약)
            if len(all_results) >= 1000:
                await analyzer.save_analysis_results(all_results, f"{output_path}_batch_{i//batch_size}", "json")
                all_results = []

        # 최종 결과 저장
        if all_results:
            await analyzer.save_analysis_results(all_results, output_path, "json")

        print(f"\n전체 분석 완료!")

    finally:
        analyzer.close()


asyncio.run(
    analyze_massive_directory(
        "/Users/aohus/Workspaces/github/politics/backend/src/etl/data/document/formatted",
        "/Users/aohus/Workspaces/github/politics/backend/src/etl/pipelines/analyzer/results/output",
    )
)
