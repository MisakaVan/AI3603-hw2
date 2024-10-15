import random, re, datetime
import board

class Agent(object):
    """
    Base class for all agents.
    """
    def __init__(self, game):
        """
        Initializes the agent with the game instance.
        """
        self.game = game
        self.action = None

    def getAction(self, state):
        """
        Abstract method to get the action for the current state.
        """
        raise Exception("Not implemented yet")

    def oppAction(self, state):
        """
        Abstract method to get the opponent's action for the current state.
        """
        raise Exception("Not implemented yet")


class RandomAgent(Agent):
    """
    Agent that selects actions randomly.
    """
    def getAction(self, state):
        """
        Selects a random legal action.
        """
        legal_actions = self.game.actions(state)
        self.action = random.choice(legal_actions)

    def oppAction(self, state):
        """
        Selects a random legal action for the opponent.
        """
        legal_actions = self.game.actions(state)
        self.opp_action = random.choice(legal_actions)


class SimpleGreedyAgent(Agent):
    # a one-step-lookahead greedy agent that returns action with max vertical advance
    """
    Greedy agent that selects actions based on maximum vertical advance.
    """
    def getAction(self, state):
        """
        Selects an action with the maximum vertical advance.
        """
        legal_actions = self.game.actions(state)
        self.action = random.choice(legal_actions)

        player = self.game.player(state)
        if player == 1:
            max_vertical_advance_one_step = max([action[0][0] - action[1][0] for action in legal_actions])
            max_actions = [action for action in legal_actions if action[0][0] - action[1][0] == max_vertical_advance_one_step]
        else:
            max_vertical_advance_one_step = max([action[1][0] - action[0][0] for action in legal_actions])
            max_actions = [action for action in legal_actions if action[1][0] - action[0][0] == max_vertical_advance_one_step]
        self.action = random.choice(max_actions)

    def oppAction(self, state):
        """
        Selects an action with the minimum vertical advance for the opponent.
        """
        legal_actions = self.game.actions(state)
        self.opp_action = random.choice(legal_actions)

        player = self.game.player(state)
        if player == 1:
            min_vertical_advance_one_step = min([action[0][0] - action[1][0] for action in legal_actions])
            min_actions = [action for action in legal_actions if action[0][0] - action[1][0] == min_vertical_advance_one_step]
        else:
            min_vertical_advance_one_step = min([action[1][0] - action[0][0] for action in legal_actions])
            min_actions = [action for action in legal_actions if action[1][0] - action[0][0] == min_vertical_advance_one_step]

        self.opp_action = random.choice(min_actions)


class YourAgent(Agent):
    """
    Placeholder for user-defined agent.
    """
    def getAction(self, state):
        """
        Placeholder for user-defined action selection.
        """
        pass
        ##########################################
        # write your own implementation here
        ##########################################

    def oppAction(self, state):
        """
        Placeholder for user-defined opponent action selection.
        """
        pass
        ##########################################
        # write your own implementation here
        ##########################################