import argparse
import datetime
import numpy as np
import logging
import json
import time
import tkinter as tk
import tqdm
import pathlib
import tqdm.contrib
import tqdm.contrib.logging
import yaml

from copy import deepcopy
from collections import namedtuple
from typing import Callable, Dict, Any, List, Optional

from agent import *
from board import Board
from game import ChineseChecker
from board import Board
# import datetime
import tkinter as tk
from UI import GameBoard

logger = logging.getLogger(__name__)

class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record) 


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
    # print(state)
    max_iter = 200  # deal with some stuck situations
    iter = 0
    start = time.time()
    iter_times = []
    inner_bar = tqdm.trange(
        max_iter,
        desc="Game Iteration",
        dynamic_ncols=True,
        position=1,
    )

    while (not ccgame.isEnd(state, iter)) and iter < max_iter:
        time.sleep(0.05)
        iter += 1
        inner_bar.update(1)
        logger.info(f"Iteration {iter}\n{state[1].as_formatted_string()}")

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
            logger.warning(f"Invalid action, choosing random action.")
        logger.info(f"Player {player} action: {agent.action[0]} -> {agent.action[1]}")
        state = ccgame.succ(state, agent.action)
        if state[-1]:
            logger.info(f"Player {player} has another opp action")
            agent.oppAction(state)
            legal_actions = ccgame.opp_actions(state)
            if agent.opp_action not in legal_actions:
                agent.opp_action = random.choice(legal_actions)
                logger.warning(f"Invalid opp action, choosing random action.")
            logger.info(f"Player {player} opp action: {agent.opp_action[0]} -> {agent.opp_action[1]}")
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

    is_end, winner = state[1].isEnd(iter)
    logger.debug(f"{(is_end, winner) = }")

    if is_end:
        logger.info(f"Game over at {iter=} with winner {winner}")
        ret = ret._replace(winner=winner)
        # return winner  # type: ignore
    else:  # stuck situation
        # print("stuck!")
        chess_count_res = state[1].compare_piece_num()
        winner = 1 if chess_count_res == 1 else 2 if chess_count_res == -1 else 0
        logger.info(f"Game stuck at {iter=} with winner {winner}")
        ret = ret._replace(winner=winner)
        logger.debug(f"new winner: {winner}")
        logger.debug(f"{ret = }")

    logger.info(f"Game over! Winner: {winner}")
    logger.info(f"Total time used: {end - start}")
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
    tie_p1_p2_count = [0, 0, 0] # index 0, 1, 2 for tie, player1 win, player2 win respectively

    ret: List[Run_game_result] = []

    outer_bar = tqdm.trange(
        simulation_times, 
        desc="Simulations",
        dynamic_ncols=True,
        position=0,
    )
    outer_bar.set_postfix_str(f"T|P1:P2: 0|0:0")

    for i in outer_bar:
        logger.info(f"=== Game {i} ===")

        run_result = runGame(ccgame, agents_dict)
        # print(run_result)
        ret.append(run_result)

        winner = run_result.winner
        tie_p1_p2_count[winner] += 1
        tie_count, p1_count, p2_count = tie_p1_p2_count
        outer_bar.set_postfix_str(f"T|P1:P2: {tie_count}|{p1_count}:{p2_count}")
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
    if config is None:
        config = {}

    if not config.get("direct_start", False):
        # not direct start, then the button should be destroyed
        B.destroy()

    if log_dir is not None:
        with open(log_dir / "run_config.yaml", "w") as f:
            yaml.safe_dump(config, f)

    agent1_type = config.get("player1", "RandomAgent")
    agent2_type = config.get("player2", "RandomAgent")
    agent_dict = {
        1: getAgentCls(agent1_type)(ccgame),
        2: getAgentCls(agent2_type)(ccgame),
    }

    # try get agent1.params
    try:
        params = agent_dict[1].__getattribute__("params")
    except AttributeError:
        params = None

    if log_dir is not None and params is not None:
        json.dump(params, open(log_dir / "params.json", "w"), indent=4)


    num_games: int = config.get("num_games", 1)  # type: ignore

    results = simulateMultipleGames(agent_dict, num_games, ccgame)

    parsed_results = [r._asdict() for r in results]
    no_time_series = False
    if no_time_series:
        for r in parsed_results:
            r.pop("iter_time_list")
    else:
        for r in parsed_results:
            # pick the odd number of iterations as the player 1's time
            player1_series = r["iter_time_list"][::2]
            # avg and var
            r["player1_time_avg"] = np.mean(player1_series)
            r["player1_time_var"] = np.var(player1_series)
            # high 10%, 5%, 1%
            r["player1_time_high10"] = np.percentile(player1_series, 90)
            r["player1_time_high5"] = np.percentile(player1_series, 95)
            r["player1_time_high1"] = np.percentile(player1_series, 99)



    overview = {
        "player1_wins": sum(1 for r in results if r.winner == 1),
        "player2_wins": sum(1 for r in results if r.winner == 2),
        "ties": sum(1 for r in results if r.winner == 0),
        "match_iter_avg": np.mean([r.iter for r in results]),
        "match_iter_var": np.var([r.iter for r in results]),
        "match_time_avg": np.mean([r.time_used for r in results]),
        "match_time_var": np.var([r.time_used for r in results]),
        "player1_time_avg": np.mean([r["player1_time_avg"] for r in parsed_results]),
    }


    if log_dir is not None:
        with open(log_dir / "results.json", "w") as f:
            json.dump(
                {
                    "params": params,
                    "overview": overview,
                    "results": parsed_results,
                },
                f,
                indent=4,
            )

    logger.info("====================")
    logger.info(f"Overview: {overview}")
    logger.info(f"Results have been saved to {log_dir}")

    if config.get("direct_exit", False):
        # exit directly by destroying the root window
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
        help="Path to the configuration file. Default is 'config.yaml'",
    )
    _parser.add_argument(
        "--num-games",
        "-n",
        type=int,
        default=None,
        help="Number of games to simulate. This overrides the same parameter in the config file.",
    )
    _parser.add_argument(
        "--direct-start",
        "--ds",
        action="store_true",
        help="Start the game directly without having to press the start button.",
    )
    _parser.add_argument(
        "--direct-exit",
        "--de",
        action="store_true",
        help="Exit the game directly without having to close the window or ctrl+c.",
    )
    _parser.add_argument(
        "--title",
        type=str,
        default="debug",
        help="Distinguish the run of the game: e.g. debug, v1.0, etc. Default is 'run'.",
    )

    return _parser


def get_config():
    args = parser().parse_args()
    with open(args.config, "r") as config_file:
        config: Dict[str, Any] = yaml.safe_load(config_file)
    if args.num_games is not None:
        config["num_games"] = args.num_games
    config["direct_start"] = args.direct_start
    config["direct_exit"] = args.direct_exit
    config["title"] = args.title
    return config


if __name__ == "__main__":
    """
    The script initializes a Chinese Checkers game and a Tkinter GUI. It sets up a button to start the game simulation.
    """

    config = get_config()

    log_dir = pathlib.Path("logs")
    run_name = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + f"_{config['title']}"
    log_dir = log_dir / run_name
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)-10.10s - [%(levelname)-5.5s] %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "run.log"),
            TqdmLoggingHandler(),
        ]
    )

    ccgame = ChineseChecker(
        size=config.get("board_size", 10), piece_rows=config.get("piece_rows", 4)
    )
    root = tk.Tk()
    display_board = GameBoard(root, ccgame.size, ccgame.size * 2 - 1, ccgame.board)
    display_board.pack(side="top", fill="both", expand=True, padx=4, pady=4)

    if config.get("direct_start", False):
        callback(ccgame=ccgame, config=config, log_dir=log_dir)
    else:
        B = tk.Button(
            display_board,
            text="Start",
            command=lambda: callback(ccgame=ccgame, config=config, log_dir=log_dir),
        )
        B.pack()
    root.mainloop()
