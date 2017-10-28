
class PlayerStrategy(object):

    def __init__(self):
        pass

    def get_action(self, game, game_state, other = None):
        raise NotImplementedError()


class PlayerGame(object):
    def __init__(self, game, player_1_strategy, player_2_strategy):
        self.game = game
        self.player_1_strategy = player_1_strategy
        self.player_2_strategy = player_2_strategy
        self.strategies = [player_1_strategy, player_2_strategy]

    def evaluate(self):
        if self.game.game_over():
            print('Warning: executed PlayerGame.evaluate but game is already over! Aborting')
            return

        game_state = self.game.get_game_state_as_class()
        for player_idx, strategy in enumerate(self.strategies):
            action = strategy.get_action(self.game, game_state)
            self.game.set_action(player_idx, action)