#!/bin/bash
# 1. 모든 패키지 제거
pip uninstall numpy scipy scikit-learn gensim -y

# 2. 캐시 삭제
pip cache purge

# 3. Python 3.12 호환 버전 설치
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir numpy==1.26.4
pip install --no-cache-dir scipy==1.12.0
pip install --no-cache-dir scikit-learn==1.4.0
pip install --no-cache-dir gensim==4.3.2
