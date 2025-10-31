# (Windows, Anaconda 프롬프트)
conda create -n kiwoom_web python=3.10 -y
conda activate kiwoom_web

pip install -r requirements.txt

py -3.9-32 -m venv C:\venvs\kiwoom32
C:\venvs\kiwoom32\Scripts\activate
pip install --upgrade pip
pip install pywin32 PyQt5==5.15.11 pykiwoom==0.1.6

