class BasePlayer:

    def __init__(self, strPlayerName):
        self.strPlayerName = strPlayerName
        self.lstGameLogs = []
        self.lstGameTime = []
        self.objGameEngine = None

    def setGameEngine(self, objGameEngine):
        self.objGameEngine = objGameEngine

    def setGameLog(self, lstGameLogs):
        self.lstGameLogs = lstGameLogs

    def decision(self):
        pass
