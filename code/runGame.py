import argparse
import datetime
import json
import time
import tkinter as tk
import pathlib
import yaml

from copy import deepcopy
from collections import namedtuple
from typing import Callable, Dict, Any, List, Optional

from agent import *
from board import Board
from game import ChineseChecker
from UI import GameBoard



Run_game_result = namedtuple(
    "Run_game_result",
    ["winner", "iter", "board", "time_used", "iter_time_list"],
    defaults=[0, 0, None, None, None],
)


def runGame(ccgame: ChineseChecker, agents: Dict[int, Agent]) -> Run_game_result:
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
    start = time.time()
    iter_times = []
    while (not ccgame.isEnd(state, iter)) and iter < max_iter:
        iter += 1
        print(f"iter: {iter}")
        display_board.board = state[1]
        display_board.draw()
        display_board.update_idletasks()
        display_board.update()

        iter_start = time.time()
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
        iter_end = time.time()
        iter_times.append(iter_end - iter_start)

    end = time.time()

    display_board.board = state[1]
    display_board.draw()
    display_board.update_idletasks()
    display_board.update()
    time.sleep(0.1)

    ret = Run_game_result(
        winner=0,
        iter=iter,
        board=state[1].as_formatted_string(),
        time_used=end - start,
        iter_time_list=iter_times,
    )

    is_end, winner = ccgame.board.isEnd(iter)
    if is_end:
        ret = ret._replace(winner=winner)
        # return winner  # type: ignore
    else:  # stuck situation
        print("stuck!")
        chess_count_res = state[1].compare_piece_num()
        winner = 1 if chess_count_res == 1 else 2 if chess_count_res == -1 else 0
        ret = ret._replace(winner=winner)

    return ret


def simulateMultipleGames(
    agents_dict: Dict[int, Agent], simulation_times: int, ccgame: ChineseChecker
) -> List[Run_game_result]:
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
    ret: List[Run_game_result] = []

    for i in range(simulation_times):
        run_result = runGame(ccgame, agents_dict)
        print(run_result)
        ret.append(run_result)

    return ret


def callback(
    ccgame: ChineseChecker,
    config: Optional[Dict[str, Any]] = None,
    log_dir: Optional[pathlib.Path] = None,
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

    if log_dir is not None:
        with open(log_dir / "run_config.yaml", "w") as f:
            yaml.safe_dump(config, f)

    agent1_type = config.get("player1", "RandomAgent")
    agent2_type = config.get("player2", "RandomAgent")
    agent_dict = {
        1: getAgentCls(agent1_type)(ccgame),
        2: getAgentCls(agent2_type)(ccgame),
    }

    num_games: int = config.get("num_games", 1)  # type: ignore

    results = simulateMultipleGames(agent_dict, num_games, ccgame)

    parsed_results = [r._asdict() for r in results]
    overview = {
        "player1_wins": sum(1 for r in results if r.winner == 1),
        "player2_wins": sum(1 for r in results if r.winner == 2),
        "ties": sum(1 for r in results if r.winner == 0),
    }

    if log_dir is not None:
        with open(log_dir / "results.json", "w") as f:
            json.dump(
                {
                    "overview": overview,
                    "results": parsed_results,
                },
                f,
                indent=4,
            )

    if root is not None:
        root.destroy()


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

    log_dir = pathlib.Path("logs")
    run_name = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = log_dir / run_name
    log_dir.mkdir(parents=True, exist_ok=True)

    ccgame = ChineseChecker(
        size=config.get("board_size", 10), piece_rows=config.get("piece_rows", 4)
    )
    root = tk.Tk()
    display_board = GameBoard(root, ccgame.size, ccgame.size * 2 - 1, ccgame.board)
    display_board.pack(side="top", fill="both", expand=True, padx=4, pady=4)
    B = tk.Button(
        display_board,
        text="Start",
        command=lambda: callback(ccgame=ccgame, config=config, log_dir=log_dir),
    )
    B.pack()
    root.mainloop()
