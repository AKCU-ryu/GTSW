import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
from pykiwoom.kiwoom import Kiwoom

class CustomKiwoom(Kiwoom):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    def OnReceiveRealData(self, code, real_type, data):
        if real_type == "주식체결":
            current_price = abs(int(self.GetCommRealData(10)))
            self.callback(str(current_price))

class StockTradingSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('stocktrading.ui', self)

        self.kiwoom = CustomKiwoom(self.update_price)
        self.kiwoom.CommConnect()
        self.account = self.kiwoom.GetLoginInfo("ACCNO")[0]
        self.kiwoom.SetRealReg("1000", "005930", "10", "1")

        self.pushButton.clicked.connect(self.place_order)
        self.ordered = False
        self.holding_qty = 0
        self.entry_price = 0  # 진입 가격

    def update_price(self, price):
        self.lineEdit.setText(price)
        if self.ordered:
            profit_or_loss = (int(price) - self.entry_price) * self.holding_qty
            self.lineEdit_2.setText(str(profit_or_loss))

            profit_target = int(self.lineEdit_3.text())
            loss_target = int(self.lineEdit_4.text())
            if int(price) >= profit_target or int(price) <= loss_target:
                self.sell_stock(self.holding_qty)
                self.ordered = False
                self.holding_qty = 0
                self.entry_price = 0

    def place_order(self):
        current_price = int(self.lineEdit.text())
        if current_price < 0:  # 예외 처리 추가
            qty = 1000000 // current_price
            self.buy_stock(qty)
            self.holding_qty = qty
            self.entry_price = current_price
            self.ordered = True

    def buy_stock(self, qty):
        self.kiwoom.SendOrder("매수주문", "0101", self.account, 2, "005930", qty, 0, "03", "")
    def self_stock(self, qty):
        self.kiwoom.SendOrder("매수주문", "0101", self.account, 2, "005930", qty, 0, "03", "")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = StockTradingSystem()
    myWindow.show()
    app.exec_()

