Overview: Recreation study of the Texas Hold'em AI agent in the paper "Game Tree Search with Adaptation in Stochastic Imperfect Information Games" 

Files: 
game.py - Game logic for two player Texas Hold'em; dealing new cards and the subsequent betting rounds until the pot is won or split is denoted as a 'game' and its logic abstracted into GameState, while MatchState represents a sequence of such games. Also doubles as the executable that runs a match of poker via 'python game.py' (requires NumPy) - just modify the players array at the bottom to contain the two agents you want playing (RandomPlayer, RaisePlayer, CallPlayer, or VexBot, with the player index, 0 or 1, as the argument).
player.py - Primarily contains my recreation of the paper's novel AI agent 'Vexbot', a method that uses a probabilistic game tree to handle player modeling at a granular level, while bridging any sparsity-related gaps subsequently introduced by way of heuristic data structures. Also contains a couple other simple agent policies for benchmarking performance.
card.py - Contains low level implementation details involving cards; includes data structures and functions to determine the type of a hand.
