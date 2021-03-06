import numpy as np
import collections
import copy
from strategy.simple_strategy import SimpleStrategy

GameState = collections.namedtuple('GameState', ['game_over', 'game_field', 'player_pos', 'player_orientation', 'player_lost'])
Point = collections.namedtuple('Point', ['x', 'y'])
Replay = collections.namedtuple('Replay', ['info', 'bodies', 'orientations', 'actions', 'game_field', 'player_lost'])

PLAYER_1 = 0
PLAYER_2 = 1

ACTION_TURN_LEFT = 0
ACTION_TURN_RIGHT = 1
ACTION_STRAIGHT = 2


class Player():

    def __init__(self, name='default', pos=Point(0, 0), orientation=180, body=None, actions=None):
        self.name = name
        self.x, self.y = pos
        self.pos = pos
        self.orientation = orientation
        self.body = body if body is not None else []
        self.actions = [] if actions is None else actions
        self.orientations = [orientation]

    def get_position(self):
        return self.pos

    def set_pos(self, pos):
        self.x, self.y = pos
        self.pos = pos

    def add_to_body(self, pos=None):
        self.body.append(self.get_position() if pos is None else pos)

    def get_next_position_after_action(self, action):
        factor = 0

        if action == ACTION_TURN_LEFT:
            factor = -90
        elif action == ACTION_TURN_RIGHT:
            factor = 90

        orientation = (self.orientation + factor) % 360
        x, y = self.get_position()

        if orientation == 0:
            y -= 1
        elif orientation == 90:
            x += 1
        elif orientation == 180:
            y += 1
        else:
            x -= 1

        return orientation, Point(x, y)


    def do_action(self, action):
        self.actions.append(action)
        factor = 0

        if action == ACTION_TURN_LEFT:
            factor = -90
        elif action == ACTION_TURN_RIGHT:
            factor = 90

        self.orientation = (self.orientation + factor) % 360

        if self.orientation == 0:
            self.y -= 1
        elif self.orientation == 90:
            self.x += 1
        elif self.orientation == 180:
            self.y += 1
        else:
            self.x -= 1

        self.orientations.append(self.orientation)
        self.pos = Point(self.x, self.y)

    def clone(self):
        copied = Player(self.name, self.get_position(), self.orientation, [])
        return copied

def is_same_point(pos1, pos2):
    return pos1.x == pos2.x and pos1.y == pos2.y


class TronGame(object):
    ACTION_TURN_LEFT = ACTION_TURN_LEFT
    ACTION_TURN_RIGHT = ACTION_TURN_RIGHT
    ACTION_STRAIGHT = ACTION_STRAIGHT

    def __init__(self, width=20, height=20, reset=True, save_history = False):
        self.width = width
        self.height = height
        self.save_history = save_history
        # Start positions
        if reset:
            self.reset()

    def reset(self, set_random = False):
        x_offset = 5
        y_offset = 5
        self.players = [Player('P1', Point(x_offset, y_offset), orientation=180), Player('P2', Point(self.width - x_offset - 1, self.height - y_offset - 1), orientation=0)]
        self.has_played = [False, False]
        self.player_lost = [False, False]
        self.tick = 0
        self.game_field = np.zeros((self.height, self.width), dtype=np.int8)
        self.game_field_history = []

        if set_random:
            self.set_player_pos(self.get_random_pos(), self.get_random_pos())
            self.set_player_orientation([self.get_random_orientation(), self.get_random_orientation()])

        return self.get_decomposed_game_field()

    def get_decomposed_game_field(self):
        mats = [np.copy(self.game_field), np.copy(self.game_field)]
        for player_idx, mat in enumerate(mats):
            mat[mat != player_idx + 1] = 0
            mat[mat == player_idx + 1] = 1

        player_heads = np.array([[p.x, p.y] for p in self.players]).flatten()
        player_heads = []
        for p in self.players:
            player_head = np.zeros(mats[0].shape)
            if self.check_pos_is_invalid(p.x, p.y):
                player_head[p.y, p.x] = 1
            mats.append(player_head)
        return np.stack(mats, axis = 2)
            #np.concatenate([np.vstack(mats).flatten(), player_heads])

    def step(self, action):
        s = SimpleStrategy(1)

        self.set_action(0, action)
        self.set_action(1, s.get_action(self, self.get_game_state_as_class()))

        #player = [p for p, played in zip(range(len(self.players)), self.has_played) if not played][0]
        #
        #player = [p for p, played in zip(range(len(self.players)), self.has_played) if not played][0]
        #self.set_action(player, action)

        def get_reward(reward_turns = False, reward_aliveness = True):
            reward = 0
            if reward_turns:
                if action in [ACTION_TURN_RIGHT, ACTION_TURN_LEFT]:
                    reward += 0.5

            if reward_aliveness and self.tick % 2 == 0:
                reward += 2

            return reward

        reward = get_reward()

        info = {}

        game_over = self.game_over()
        game_field = self.get_decomposed_game_field()

        if game_over and np.all(self.has_played):
            #reward += self.tick
            reward += 10 if not self.player_lost[0] else -5
            self.reset(True)

        #game_field = np.copy(self.game_field)
        #game_field[game_field> 0] = 1
        #game_field = game_field_copy
        print('GameField', game_field.shape)
        return game_field, reward, game_over, info

    def get_random_orientation(self):
        return np.random.choice([0, 90, 180, 270])

    def render(self, mode):
        pass

    def set_player_pos(self, player_1_pos, player_2_pos):
        for player, pos in zip(self.players, [player_1_pos, player_2_pos]):
            player.set_pos(pos)

    def set_player_orientation(self, player_orientations):
        for player, orientation in zip(self.players, player_orientations):
            player.orientation = orientation

    def set_action(self, player, action):
        if self.save_history and not np.any(self.has_played):
            self.save_current_state()

        if self.save_history:
            self.players[player].add_to_body()

        if self.has_played[player]:
            print('Warning: player {} already did an action this tick. Ignoring'.format(player))
            return

        if np.all(self.has_played) and self.game_over():
            print('Warning: tried to do an action for player {}, but the game is already over! Aborting'.format(player))
            return

        player_ = self.players[player]
        player_.do_action(action)
        self.has_played[player] = True

        if np.all(self.has_played):
            self.check_for_player_pos()
            if not np.any(self.player_lost):

                self.check_collisions()

                # Add position to body
                #for player in self.players:
                #    player.add_to_body()

                # Write player positions in game field
                self.update_game_field()
                #self.check_player_lost_status()

                self.has_played = [False, False]
            self.tick += 1




    def check_collisions(self):
        for player_idx, player in enumerate(self.players):
            x, y = player.get_position()

            if self.check_pos_is_invalid(x, y) or self.game_field[y, x] != 0:
                self.player_lost[player_idx] = True

    def update_game_field(self):
        for player_idx, player in enumerate(self.players):
            pos = player.get_position()
            if not self.check_pos_is_invalid(*pos):
                self.game_field[pos.y, pos.x] = player_idx + 1

    def check_for_player_pos(self):
        for player_idx, player in enumerate(self.players[:-1]):
            other_player = self.players[player_idx + 1]
            if is_same_point(player.get_position(), other_player.get_position()):
                self.player_lost[player_idx] = True
                self.player_lost[player_idx + 1] = True

    def check_player_lost_status(self):
        for player_idx, player in enumerate(self.players):
            pos = player.get_position()
            if self.check_pos_is_invalid(*pos):
                self.player_lost[player_idx] = True
                break
            other_player = self.players[(player_idx + 1) % 2]
            for other_pos in other_player.body + player.body[:-1]:
                if is_same_point(pos, other_pos):
                    self.player_lost[player_idx] = True
                    break
        return np.any(self.player_lost)

    def check_player_lost_status_x(self):
        for player_idx, player in enumerate(self.players):

            pos = player.get_position()
            x, y = pos
            position_invalid = self.check_pos_is_invalid(x, y)

            if position_invalid:
                self.player_lost[player_idx] = True
                break

            cell_value = self.game_field[y][x]

            if cell_value == 0:
                continue

            if cell_value != player_idx + 1:
                self.player_lost[player_idx] = True
                break

            last_player_pos = player.body[-1]
            for body_pos in player.body[:-1]:
                if is_same_point(pos, body_pos):
                    self.player_lost[player_idx] = True
                    break

        return np.any(self.player_lost)

    def get_player_pos(self):
        return [player.get_position() for player in self.players]

    def get_player_orientation(self):
        return [player.orientation for player in self.players]


    def check_pos_is_invalid(self, x, y):
        return y < 0 or y >= self.height or x >= self.width or x < 0

    def get_player_positions_flat(self, check_valid = True):
        player_bodies = []
        for player in [PLAYER_1, PLAYER_2]:
            player_bodies += [(player, pos) for pos in self.players[player].body if not check_valid or not self.check_pos_is_invalid(*pos)]

        return player_bodies

    def get_game_state(self):
        return self.game_over(), self.game_field, self.get_player_pos(), self.get_player_orientation(), self.player_lost

    def get_game_state_flattened(self):
        return np.array(self.get_game_state()).flatten()

    def get_game_state_as_class(self):
        return GameState(*self.get_game_state())

    def get_random_pos(self):
        return Point(np.random.choice(self.width), np.random.choice(self.height))

    def clone(self):
        new_game = TronGame(reset=False)
        new_game.width = self.width
        new_game.height = self.height
        new_game.players = [player.clone() for player in self.players]
        new_game.has_played = np.copy(self.has_played)
        new_game.player_lost = np.copy(self.player_lost)
        new_game.tick = self.tick
        new_game.game_field = np.copy(self.game_field)
        return new_game

    def game_over(self):
        player_has_lost = np.any(self.player_lost)
        return player_has_lost

    def get_replay(self):
        return Replay(
            info = dict(
                width = self.width,
                height = self.height
            ),
            player_lost = np.copy(self.player_lost),
            orientations= [np.copy(p.orientations) for p in self.players],
            bodies = [np.copy(p.body) for p in self.players],
            actions = [np.copy(p.actions) for p in self.players],
            game_field = self.game_field_history
        )

    def save_current_state(self):
        self.game_field_history.append(np.copy(self.game_field))


    def get_available_actions(self):
        return [ACTION_TURN_LEFT, ACTION_TURN_RIGHT, ACTION_STRAIGHT]

    def __str__(self):
        out = 'Tick: {}\n'.format(self.tick)
        field_width_padded = (self.width * 2 + 2)
        out += '_' * field_width_padded
        out += '\n'
        for row in self.game_field:
            out += '|'
            for cell in row:
                if cell == 0:
                    out += ' '
                else:
                    out += str(cell)
                out += ' '
            out += '|\n'
        out += '-' * field_width_padded
        return out
