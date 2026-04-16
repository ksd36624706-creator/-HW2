
class GameEngine:
    def __init__(self, game_id, lstPlayers):
        self.game_id = game_id
        self.lstPlayers = lstPlayers

        for player in self.lstPlayers:
            player.setGameEngine(self)


    def start(self):
        pass