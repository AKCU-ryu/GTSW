import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, BatchNormalization
from keras.callbacks import EarlyStopping

df = pd.read_excel('TSLA_20010101_20250930.xlsx')
print(df.head())
# 시계열 데이터 생성
def create_sequences(p_data, seq_len, size):
    result = []
    for i in range(len(p_data) - seq_len):
        result.append(p_data[i:i+seq_len+size])
    return np.array(result)

x_size = 50
y_size = 1
dataset = create_sequences(df['Close'], x_size, y_size)
print(dataset)
# 학습/테스트 분할
train_size = int(len(dataset) * 0.9)
train_data = dataset[:train_size]
test_data = dataset[train_size:]
x_train = train_data[:,:-1] # 50
y_train = train_data[:,-1] # 1
x_test = test_data[:,:-1]
y_test = test_data[:,-1]

x_train = x_train.reshape(x_train.shape[0], x_train.shape[1], 1)
x_test = x_test.reshape(x_test.shape[0], x_test.shape[1], 1)
# 모델 구성
model = Sequential()
model.add(LSTM(64, return_sequences=True, input_shape=(x_size, y_size)))
model.add(Dropout(0.2))
model.add(BatchNormalization())
model.add(LSTM(64))
model.add(Dropout(0.2))
model.add(Dense(y_size))
model.summary()
# 학습
model.compile(loss='mse', optimizer='adam')
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=100, batch_size=20, callbacks=[early_stop], verbose=1)

model.save('TSLA_BASE.keras')
pred = model.predict(x_test)
# 시각화
fig = plt.figure(figsize=(20, 10))
ax = fig.add_subplot(111)
ax.plot(y_test, label='True')
ax.plot(pred, label='Prediction')
ax.legend()
plt.show()