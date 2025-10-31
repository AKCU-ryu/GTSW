# app/services/ml/lstm.py
# (옵션) LSTM 예시 스텁 - 추후 학습/저장/예측 파이프라인 확장
import numpy as np, pandas as pd, tensorflow as tf

def build_lstm(input_dim: int, units: int = 64):
    m = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(None, input_dim)),
        tf.keras.layers.LSTM(units),
        tf.keras.layers.Dense(1)
    ])
    m.compile(optimizer="adam", loss="mse")
    return m

# TODO: windowing, train(), predict() 등 구현
