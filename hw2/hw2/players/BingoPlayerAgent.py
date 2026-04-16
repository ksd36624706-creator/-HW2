from gameengine.BasePlayer import BasePlayer


class BaseBingoPlayer(BasePlayer):

    def __init__(self, strPlayerName):
        super().__init__(strPlayerName)

    def decision(self, matGrid):
        pass


