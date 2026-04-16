import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QEventLoop
from hw2.players.BingoPlayerAgent import BaseBingoPlayer


class HumanInterface(QDialog):
    # 사용자가 클릭을 완료했음을 알리는 시그널
    move_made = pyqtSignal()

    def __init__(self, player_name, engine):
        super().__init__()
        self.setWindowTitle(f"Human Turn - {player_name}")
        self.setMinimumSize(800, 700)

        self.engine = engine
        self.width_count = engine.width
        self.height_count = engine.height
        self.selected_pos = None
        self.is_my_turn = False  # 클릭 가능 여부 제어

    def get_layout_params(self):
        margin = 50
        top_padding = 80
        available_w = self.width() - (margin * 2)
        available_h = self.height() - margin - top_padding

        cell_w = available_w / self.width_count
        cell_h = available_h / self.height_count
        cell_size = min(cell_w, cell_h) * 0.9

        startX = (self.width() - (cell_size * self.width_count)) / 2
        startY = top_padding + (available_h - (cell_size * self.height_count)) / 2
        return cell_size, startX, startY

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setPen(QPen(Qt.black, 2))
        qp.setFont(QFont('Arial', 16))

        cell_size, startX, startY = self.get_layout_params()

        # 턴 상태에 따른 메시지 변경
        status_text = "당신의 차례입니다! 클릭하세요." if self.is_my_turn else "상대방(AI)의 차례를 기다리는 중..."
        qp.drawText(20, 40, f"[{self.windowTitle()}] {status_text}")

        for i in range(self.height_count):
            for j in range(self.width_count):
                x = startX + j * cell_size
                y = startY + i * cell_size

                state = self.engine.getState(j, i)  #
                if state == 2:  # Red
                    qp.setBrush(QBrush(Qt.red, Qt.SolidPattern))
                elif state == 1:  # Green
                    qp.setBrush(QBrush(Qt.green, Qt.SolidPattern))
                else:
                    qp.setBrush(Qt.NoBrush)

                qp.drawEllipse(int(x), int(y), int(cell_size), int(cell_size))

    def mousePressEvent(self, event):
        if not self.is_my_turn:
            return

        cell_size, startX, startY = self.get_layout_params()
        j = int((event.x() - startX) // cell_size)
        i = int((event.y() - startY) // cell_size)

        if 0 <= j < self.width_count and 0 <= i < self.height_count:
            cx, cy = startX + j * cell_size + cell_size / 2, startY + i * cell_size + cell_size / 2
            if (event.x() - cx) ** 2 + (event.y() - cy) ** 2 <= (cell_size / 2) ** 2:
                if self.engine.isFeasiblePosition(j, i):  #
                    self.selected_pos = (i, j)
                    self.is_my_turn = False  # 한 번 클릭하면 턴 종료
                    self.move_made.emit()  # decision 함수에 신호를 보냄
                    self.update()
                else:
                    QMessageBox.warning(self, "Invalid Move", "착수할 수 없는 위치입니다!")


class HumanPlayer(BaseBingoPlayer):
    def __init__(self, strPlayerName):
        super().__init__(strPlayerName)
        self.gui = None
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

    def decision(self, matGrid):
        if self.objGameEngine is None:
            return (None, None)

        if self.gui is None:
            self.gui = HumanInterface(self.strPlayerName, self.objGameEngine)
            self.gui.show()

        self.gui.is_my_turn = True
        self.gui.update()

        loop = QEventLoop()
        self.gui.move_made.connect(loop.quit)
        loop.exec_()

        return self.gui.selected_pos

    def show_final_result(self, winner_name):
        if self.gui:
            self.gui.is_my_turn = False  # 더 이상 클릭 불가
            self.gui.update()

            if winner_name == self.strPlayerName:
                msg = f"Winnder is {self.strPlayerName}"
            elif winner_name:
                msg = f"Winner is {winner_name}"
            else:
                msg = "Draw"

            QMessageBox.information(self.gui, "Game Over", msg)

            print("Close Window")
            self.app.exec_()