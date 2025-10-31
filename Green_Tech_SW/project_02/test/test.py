# test.py
# 필수 패키지 임포트 확인 및 간단 버전 출력 (최소 수정)

import numpy, pandas, flask, websockets, bs4, openpyxl
import Crypto  # pycryptodome
from importlib.metadata import version         # Flask __version__ deprec. 대응
from PyQt5 import QtCore                      # PyQt5는 루트에서 QtCore 바로 접근 불가

print("OK numpy:", numpy.__version__)
print("OK pandas:", pandas.__version__)
print("OK flask:", version("flask"))          # __version__ 대신 권장 방식
print("OK websockets:", websockets.__version__)
print("OK PyQt5 (Qt):", QtCore.QT_VERSION_STR)        # Qt 런타임 버전
print("OK PyQt5 (PyQt):", QtCore.PYQT_VERSION_STR)    # PyQt 래퍼 버전
print("OK bs4:", getattr(bs4, "__version__", "loaded"))
print("OK openpyxl:", openpyxl.__version__)
print("OK pycryptodome:", getattr(Crypto, "__version__", "loaded"))
