import argparse
import yaml

from agent import *
from game import ChineseChecker
# import datetime
import tkinter as tk
from UI import GameBoard
import time

from typing import Callable, Dict, Any, Optional


def runGame(ccgame: ChineseChecker, agents: Dict[int, Agent]) -> int:
    """
    Runs a single game of Chinese Checkers.

    Args:
        ccgame (ChineseChecker): The game instance.
        agents (dict): A dictionary mapping player numbers to their respective agents.

    Returns:
        int: The winner of the game (1 for player 1, 2 for player 2, 0 for a tie).
    """
    state = ccgame.startState()
    print(state)
    max_iter = 200  # deal with some stuck situations
    iter = 0
    # start = datetime.datetime.now()
    while (not ccgame.isEnd(state, iter)) and iter < max_iter:
        iter += 1
        display_board.board = state[1]
        display_board.draw()
        display_board.update_idletasks()
        display_board.update()

        player = ccgame.player(state)
        agent: Agent = agents[player]
        # function agent.getAction() modify class member action
        agent.getAction(state)
        legal_actions = ccgame.actions(state)
        if agent.action not in legal_actions:
            agent.action = random.choice(legal_actions)
        state = ccgame.succ(state, agent.action)
        if state[-1]:
            print("opp step")
            print(agent.action)
            agent.oppAction(state)
            legal_actions = ccgame.opp_actions(state)
            if agent.opp_action not in legal_actions:
                agent.opp_action = random.choice(legal_actions)
            state = ccgame.opp_succ(state, agent.opp_action, agent.action)

    display_board.board = state[1]
    display_board.draw()
    display_board.update_idletasks()
    display_board.update()
    time.sleep(0.1)

    # end = datetime.datetime.now()
    # if ccgame.isEnd(state, iter):
    #     return state[1].isEnd(iter)[1]  # return winner
    is_end, winner = ccgame.board.isEnd(iter)
    if is_end:
        return winner  # type: ignore
    else:  # stuck situation
        print("stuck!")
        chess_count_res = state[1].compare_piece_num()
        if chess_count_res == 1:
            return 1
        elif chess_count_res == -1:
            return 2
        else:
            return 0


def simulateMultipleGames(
    agents_dict: Dict[int, Agent], simulation_times: int, ccgame: ChineseChecker
) -> None:
    """
    Simulates multiple games of Chinese Checkers and tracks the results.

    Args:
        agents_dict (dict): A dictionary mapping player numbers to their respective agents.
        simulation_times (int): The number of games to simulate.
        ccgame (ChineseChecker): The game instance.

    Returns:
        None
    """
    win_times_P1 = 0
    win_times_P2 = 0
    tie_times = 0
    # utility_sum = 0
    for i in range(simulation_times):
        run_result = runGame(ccgame, agents_dict)
        print(run_result)
        if run_result == 1:
            win_times_P1 += 1
        elif run_result == 2:
            win_times_P2 += 1
        elif run_result == 0:
            tie_times += 1
        print("game", i + 1, "finished", "winner is player ", run_result)
    print("In", simulation_times, "simulations:")
    print("winning times: for player 1 is ", win_times_P1)
    print("winning times: for player 2 is ", win_times_P2)
    print("Tie times:", tie_times)


def callback(ccgame: ChineseChecker, config: Optional[Dict[str, Any]] = None
             ) -> None:
    """
    Callback function to start the game simulation when the button is pressed.

    Args:
        ccgame (ChineseChecker): The game instance.

    Returns:
        None
    """
    B.destroy()

    if config is None:
        config = {}
    agent1_type = config.get("player1", "RandomAgent")
    agent2_type = config.get("player2", "RandomAgent")
    agent_dict = {
        1: getAgentCls(agent1_type)(ccgame),
        2: getAgentCls(agent2_type)(ccgame),
    }

    num_games: int = config.get("num_games", 1)  # type: ignore
    with open("run.log", "w") as f:
        f.write(f"Start running {num_games} games\n")
        # type of agent
        f.write(f"Player 1: {agent1_type}\n")
        f.write(f"Player 2: {agent2_type}\n")

    simulateMultipleGames(agent_dict, num_games, ccgame)
    
    # simpleGreedyAgent = SimpleGreedyAgent(ccgame)
    # simpleGreedyAgent1 = SimpleGreedyAgent(ccgame)
    # randomAgent = RandomAgent(ccgame)
    # teamAgent = YourAgent(ccgame)

    # Player 1 first move, Player 2 second move
    # YourAgent need to test as both player 1 and player 2
    # simulateMultipleGames({1: simpleGreedyAgent1, 2: simpleGreedyAgent}, 1, ccgame)
    # simulateMultipleGames({1: simpleGreedyAgent, 2: teamAgent}, 1, ccgame)
    # simulateMultipleGames({1: teamAgent, 2: simpleGreedyAgent}, 1, ccgame)

def getAgentCls(agent_name: str) -> Callable[..., Agent]:
    if agent_name == "RandomAgent":
        return RandomAgent
    if agent_name == "SimpleGreedyAgent":
        return SimpleGreedyAgent
    if agent_name == "YourAgent":
        return YourAgent
    raise Exception(f"Unknown agent name: {agent_name}")

def parser():
    _parser = argparse.ArgumentParser(description="Chinese Checkers")
    _parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file",
    )
    _parser.add_argument(
        "--num-games",
        "-n",
        type=int,
        default=None,
        help="Number of games to simulate. This overrides the same parameter in the config file.",
    )

    return _parser

def get_config():
    args = parser().parse_args()
    with open(args.config, "r") as config_file:
        config = yaml.safe_load(config_file)
    if args.num_games is not None:
        config["num_games"] = args.num_games
    return config


if __name__ == "__main__":
    """
    The script initializes a Chinese Checkers game and a Tkinter GUI. It sets up a button to start the game simulation.
    """
    config = get_config()

    ccgame = ChineseChecker(size=config.get("board_size", 10), piece_rows=config.get("piece_rows", 4))
    root = tk.Tk()
    display_board = GameBoard(root, ccgame.size, ccgame.size * 2 - 1, ccgame.board)
    display_board.pack(side="top", fill="both", expand=True, padx=4, pady=4)
    B = tk.Button(display_board, text="Start", command=lambda: callback(ccgame=ccgame, config=config))
    B.pack()
    root.mainloop()
