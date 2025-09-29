import random 
import numpy as np
from copy import deepcopy

class Player:
    def __init__(self,policy_fnc):
        self.policy_fnc = policy_fnc
    
    def policy(self, match_state):
        pass

class RandomPlayer(Player):
    def __init__(self, player_idx):
        super().__init__(None)
        self.player_idx = player_idx
    def policy(self, match_state):
        # This player selects a random action
        # 20% fold
        # 40% Call
        # 40 Raise
        # old code was when the game was No limits
        game_state = match_state.current_game_state
        chips = game_state.players_chips[self.player_idx]

        action = None
        rand = random.random()
        if rand < 0.2:
            action = ('fold', None)
        else: 
            if rand < 0.6:
                action = ('call', None)
            else:
                prev_bet = game_state.current_bets[(self.player_idx - 1) % game_state.num_players]
                if rand < 0.8:   
                    amount = min(chips, prev_bet + game_state.big_blind)
                    action = ('bet', None)
                elif rand < 0.9:
                    amount = min(chips, prev_bet + (int)(abs(random.random()*(chips - prev_bet))) // game_state.big_blind * game_state.big_blind)
                    action = ('bet', None)
                else:
                    amount = chips
                    action = ('bet', None)
        value = 0
        return action, value
    
class RaisePlayer(Player):
    def __init__(self, player_idx):
        super().__init__(None)
        self.player_idx = player_idx
        
    def policy(self, match_state):

        # This player will always raise. The player can raise multiple times in the same betting round
        game_state = match_state.current_game_state
        chips = game_state.players_chips[self.player_idx]

        action = None
        prev_bet = game_state.current_bets[(self.player_idx - 1) % game_state.num_players]
        rand = random.random()
        
        # 50% min bet
        # 40% random bet
        # 10% all-in
        if rand < 0.5:   
            # min bet
            amount = min(chips, prev_bet + game_state.big_blind)
            action = ('bet', amount)
        elif rand < 0.9:
            # random bet
            amount = min(chips, prev_bet + (int)(abs(random.random()*(chips - prev_bet))) // game_state.big_blind * game_state.big_blind)
            action = ('bet', amount)
        else:
            # all in
            amount = chips
            action = ('bet', amount)
            
        value = 0
        return action, value

class CallPlayer(Player):
    def __init__(self, player_idx):
        super().__init__(None)
        self.player_idx = player_idx

    def policy(self, match_state):
        # This player will always call
        action = ('call', None)
        value = 0
        return action, value

class VexBot(Player):
    def __init__(self, player_idx):
        super().__init__(None)
        self.player_idx = player_idx
        self.opponent_idx = (player_idx + 1) % 2

        # Need to roots; one for player starting, the other is if the player goes second
        self.roots = [None, None]
        self.roots[self.player_idx] = self.ProgramDecisionNode(self.player_idx, None, None)
        self.roots[self.opponent_idx] = self.OpponentNode(self.opponent_idx, None, None)

        # Used to track current node in the game
        self.current_node = None
        self.match_state = None
        
        
        #Init coarse abstraction

        # Min num raises -> 0
        # max num raises -> 24
        # each histogram is .1
        self.coarse_abstraction = np.zeros((25,10))
        

        # Initialize histograms using human experience

        # 0-1 not bluffing; likely to be weak
        self.coarse_abstraction[0:2,:] = np.array([4,3,2,1,0,0,0,0,0,0])
        # 2-4 likely bluffing; probably weak
        self.coarse_abstraction[2:5,:] = np.array([0,1,2,3,2,1,1,0,0,0])
        # 5-15: very likely to be strong
        self.coarse_abstraction[5:16,:] = np.array([0,0,0,0,1,2,3,2,1,1])
        # 15-24:
        self.coarse_abstraction[15:25,:] = np.array([0,0,0,0,0,0,0,2,3,5])
    
    class Node:
        def __init__(self, player_idx, parent, parent_action):
            self.player_idx = player_idx
            self.children = []
            self.parent = None
            self.n_visited = 0
            self.parent = parent
            self.parent_action = parent_action
        def __repr__(self):
            class_name = type(self).__name__
            return f"{class_name}(parent={self.parent}, action_to_node={self.parent_action})"
            
    class ChanceNode(Node):
        # Deals with board cards
        def __init__(self,player_idx, parent, parent_action, node_type):
            super().__init__(player_idx, parent, parent_action)
            # card(s) -> [child node, action(card deal) frequency]
            self.children_and_freqs = dict()
            self.node_type = node_type
            self.num_outcomes = 1
            if node_type == 'flop':
                self.num_outcomes = (50 * 49 * 48)/6
            elif node_type == 'turn':
                self.num_outcomes = 47
            elif node_type == 'river':
                self.num_outcomes = 46
        
    def add_chance_outcome(self, chance_node, cards):
        node_after_chance = None
        
        if self.match_state.current_game_state.start_player == self.player_idx:
            node_after_chance = self.ProgramDecisionNode(self.player_idx, chance_node, 3)
        else:
            node_after_chance = self.OpponentNode(self.opponent_idx, chance_node, 3)
        if len(cards) == 3:
            sorted_cards = sorted(cards, key=lambda x: x.suit.value, reverse=True)
            sorted_cards = sorted(sorted_cards, key=lambda x: x.value, reverse=True)

            if tuple(sorted_cards) not in chance_node.children_and_freqs:
                chance_node.children_and_freqs[tuple(sorted_cards)] = [node_after_chance,0]
            chance_node.children_and_freqs[tuple(sorted_cards)][1] += 1
        else:
            card = cards[0]
            if card not in chance_node.children_and_freqs:
                chance_node.children_and_freqs[card] = [node_after_chance, 0]
            chance_node.children_and_freqs[card][1] += 1

            
        
    class OpponentNode(Node):
        def __init__(self,player_idx, parent, parent_action):
            super().__init__(player_idx, parent, parent_action)
            self.children = [None] * 3
            self.act_freqs = [0] * 3
            self.showdown_node = None
            self.showdown_freq = 0
    

    
    class ProgramDecisionNode(Node):
        def __init__(self,player_idx, parent, parent_action):
            super().__init__(player_idx, parent, parent_action)
            self.children = [None] * 3
            self.act_freqs = [0] * 3
            self.showdown_node = None
            self.showdown_freq = 0
        
    class FoldLeafNode(Node):
        def __init__(self, parent, parent_action, p_win):
            # no need to maintain children
            super().__init__(None, parent, parent_action)
            self.p_win = p_win
    
    class ShowdownLeafNode(Node):
        def __init__(self, parent, parent_action):
            # no need to maintain children
            super().__init__(None, parent, parent_action)
            self.hist = np.zeros(10)
    
    def get_coarse_statistics(self, curr_node):
        opp_bets = 0
        player_bets = 0
        opp_raises = 0
        player_raises = 0
        n_actions = 0
        while curr_node is not None:
            parent = curr_node.parent
            if curr_node.parent_action == 0:
                if parent is not None and parent.parent_action == 0:
                    if isinstance(parent, self.ProgramDecisionNode):
                        player_raises += 1
                    elif isinstance(parent, self.OpponentNode):
                        opp_raises += 1
                else:
                    if isinstance(parent, self.ProgramDecisionNode):
                        player_bets += 1
                    elif isinstance(parent, self.OpponentNode):
                        opp_bets += 1
            if not isinstance(parent, self.ChanceNode):
                n_actions += 1
            curr_node = parent
        
        # return opp_bets + opp_raises
        # return (opp_bets, opp_raises)
        return player_raises + opp_raises
    
    def get_hr_from_cards(self, cards, hand_type):
        
        # hr ranges from 0 to 1.0 indicating the strength of the hand, relative to other hands
        hr = 0
        if hand_type == 0:
            hr = 0.95
        elif hand_type == 1:
            hr = 0.95
        elif hand_type == 2:
            hr = 0.85
        elif hand_type == 3:
            hr = 0.75
        elif hand_type == 4:
            hr = 0.75
        elif hand_type == 5:
            hr = 0.65
        elif hand_type == 6:
            hr = 0.55
        elif hand_type == 7:
            hr = 0.45
        elif hand_type == 8:
            if cards[0].value > 10:
                hr = 0.35
            elif cards[0].value > 8:
                hr = 0.25
            elif cards[0].value > 5:
                hr = 0.15
            else:
                hr = 0.05
        return hr




    def get_ev_from_hist(self, hist_pdf, match_state, player_idx):
        game_state = match_state.current_game_state
        board = deepcopy(game_state.board)
        hand = deepcopy(game_state.players_hands[player_idx])
        cards = board+hand
        cards = sorted(cards, key=lambda x: x.value, reverse=True)

        # Evaluate strength of hand if no board is present (preflop)


        selected_cards= None
        if len(cards) == 2:
            # Human set hr values
            # if none of the below-> 0.1
            # if within range ->0.2
            # if same value -> 0.5
            # if high value (>10) -> +0.1
            # if one ace (14) -> +0.1
            # if same suit -> +0.1
            card_1 = cards[0]
            card_2 = cards[1]
            ev = 0.1
            if card_1.value - card_2.value < 5:
                ev = 0.2
            if card_1.value == card_2.value:
                ev = 0.5
            if card_1.suit == card_2.suit:
                ev += 0.1
            if card_1.value >= 10 or card_2.value >= 10:
                ev += 0.2
            if card_1.value == 14 or card_2.value == 14:
                ev += 0.1
            return ev*game_state.pot
        elif len(cards) == 7:
            for hand_type in range(9):
                for i in range(5, -1, -1):
                    for j in range(6, i, -1):
                        if i == 5 and j == 6:
                            continue
                        five_cards = [deepcopy(cards[k]) for k in range(len(cards)) if (k != i and k != j)]
                        comparable_cards = game_state.check_if_hand_type(five_cards, hand_type)
                        if comparable_cards:

                            hr = self.get_hr_from_cards(comparable_cards, hand_type)
                            hr_idx = ((int)(hr * 10) - 1 )
                            ev = (np.sum(hist_pdf[0:max(hr_idx-1,0)])+0.5*hist_pdf[hr_idx])/np.sum(hist_pdf)*game_state.pot
                            return ev
            return 0
        elif len(cards) == 6:
            for hand_type in range(9):
                for i in range(5, -1, -1):
                    five_cards = [deepcopy(cards[k]) for k in range(len(cards)) if (k != i)]
                    comparable_cards = game_state.check_if_hand_type(five_cards, hand_type)
                    if comparable_cards:
                        hr = self.get_hr_from_cards(comparable_cards, hand_type)
                        hr_idx = ((int)(hr * 10) - 1 )
                        ev = (np.sum(hist_pdf[0:max(hr_idx-1,0)])+0.5*hist_pdf[hr_idx])/np.sum(hist_pdf)*game_state.pot
                        return ev
                    
            return 0
        elif len(cards) == 5:
            for hand_type in range(9):
                five_cards = [deepcopy(cards[k]) for k in range(len(cards))]
                comparable_cards = game_state.check_if_hand_type(five_cards, hand_type)
                if comparable_cards:
                    hr = self.get_hr_from_cards(comparable_cards, hand_type)
                    hr_idx = ((int)(hr * 10) - 1 )
                    ev = (np.sum(hist_pdf[0:max(hr_idx-1,0)])+0.5*hist_pdf[hr_idx])/np.sum(hist_pdf)*game_state.pot
                    return ev
            return 0


    
    
    def dfs(self,curr_node):

        if isinstance(curr_node, self.ProgramDecisionNode):
            child_evs = list()
            for a in range(len(curr_node.children)):
                child = curr_node.children[a]
                child_ev = 0
                if child is None:
                    child_coarse_stats = self.get_coarse_statistics(curr_node)
                    if a == 0:
                        child_coarse_stats += 1                                                             
                    hist_pdf = self.coarse_abstraction[child_coarse_stats]
                    child_ev = self.get_ev_from_hist(hist_pdf, self.match_state, self.player_idx,)
                else:
                    child_ev = self.dfs(child)
                child_evs.append(child_ev)
            return max(child_evs)
        elif isinstance(curr_node,self.OpponentNode):
            child_evs = list()
            for a in range(len(curr_node.children)):
                child = curr_node.children[a]
                child_ev = 0
                if child is None:
                    child_coarse_stats = self.get_coarse_statistics(curr_node)
                    if a == 0:
                        child_coarse_stats += 1                                                             
                    hist_pdf = self.coarse_abstraction[child_coarse_stats]
                    child_ev = self.get_ev_from_hist(hist_pdf, self.match_state, self.player_idx)
                else:
                    child_ev = self.dfs(child)
                child_evs.append(child_ev)
            return np.dot(child_evs, curr_node.act_freqs)/sum(curr_node.act_freqs)
        elif isinstance(curr_node,self.ChanceNode):
            child_evs = list()
            for k in curr_node.children_and_freqs:
                child, act_freq = curr_node.children_and_freqs[k]
                child_ev = self.dfs(child)
                child_evs.append(child_ev)
            net_ev = sum(child_evs)/curr_node.num_outcomes
            
            coarse_stats = self.get_coarse_statistics(curr_node)
            hist_pdf = self.coarse_abstraction[coarse_stats]
            unexplored_children_ev = self.get_ev_from_hist(hist_pdf, self.match_state, self.player_idx)
            net_ev += (curr_node.num_outcomes - len(child_evs)) / curr_node.num_outcomes * unexplored_children_ev
            return net_ev

        elif isinstance(curr_node,self.FoldLeafNode):
            # Leaf node represents a fold action
            # if curr_node.parent_action == 2:
            #     if isinstance(curr_node.parent, self.ProgramDecisionNode):
            #          return -1*(self.match_state.current_bets(self.player_idx) + self.match_state.pot/2)
            #     elif isinstance(curr_node.parent, self.OpponentNode):
            #         return self.match_state.current_bets(self.opponent_idx) + self.match_state.pot/2
            return curr_node.p_win * self.match_state.current_game_state.pot - self.match_state.current_game_state.current_bets[self.player_idx]
        elif isinstance(curr_node,self.ShowdownLeafNode):
            # Leaf node represents a showdown
            hist_pdf = self.coarse_abstraction[self.get_coarse_statistics(curr_node)]
            return self.get_ev_from_hist(hist_pdf,self.match_state,self.player_idx)
            
                
                
    def action_to_num(self, action_t):
        action = action_t[0]
        if action == 'bet':
            return 0
        elif action == 'call':
            return 1
        elif action == 'fold':
            return 2
        elif action == 'flop' or action == 'turn' or action == 'river':
            return 3
        elif action == 'showdown':
            return 4
            
            

    def add_branch_to_tree(self, prev_game_state):
        prev_node = None
        curr_node = self.roots[prev_game_state.start_player]
        game_actions = prev_game_state.game_actions
        i = 0
        while i < len(game_actions):
            outcome = game_actions[i]
            # select
            next_node = None
            action_num = self.action_to_num(outcome)
            if action_num == 0 or action_num == 1 or action_num == 2:
                next_node = curr_node.children[action_num]
                curr_node.act_freqs[action_num] += 1
            elif action_num == 3:
                next_node = None if outcome[1] not in curr_node.children_and_freqs else curr_node.children_and_freqs[outcome[1]][0]
                curr_node.children_and_freqs[outcome[1]][1] += 1
            elif action_num == 4:
                next_node = curr_node.showdown_node
                curr_node.showdown_freq += 1
            
            if next_node is None:
                # expand
                if action_num == 2:
                    next_node = self.FoldLeafNode(curr_node, action_num, outcome[1])
                    curr_node[action_num] = next_node
                elif action_num == 4:
                    next_node = self.ShowdownLeafNode(curr_node, action_num)
                    curr_node.showdown_node = next_node
                elif action_num == 3:
                    self.add_chance_outcome(curr_node, outcome[1])
                    next_node = curr_node.children_and_freqs[outcome[1]][0]
                elif action_num == 0:
                    next_node = self.OpponentNode(self.opponent_idx, curr_node,action_num) if outcome[1] == self.player_idx else self.ProgramDecisionNode(self.player_idx, curr_node, action_num)
                    curr_node[action_num] = next_node
                elif action_num == 1:
                    next_action_num = self.action_to_num(game_actions[i+1])
                    if next_action_num == 3:
                        next_node = self.ChanceNode(None, curr_node, action_num, outcome[0])
                    else:
                        next_node = self.OpponentNode(self.opponent_idx, curr_node,action_num) if outcome[1] == self.player_idx else self.ProgramDecisionNode(self.player_idx, curr_node, action_num)
                    curr_node[action_num] = next_node

            curr_node = next_node 
            i += 1
                

    def printTree(self,leaf_node):
        temp = leaf_node
        while(temp.parent is not None):
            print(temp)
            temp = leaf_node.parent


        
        

    def policy(self, match_state):
        prev_match_state = self.match_state
        if prev_match_state is not None:
            prev_game_state = prev_match_state.current_game_state
            # If the game ended last turn, update the tree
            if prev_game_state.game_over:
                self.add_branch_to_tree(prev_game_state)



        
        self.match_state = match_state
        game_state = match_state.current_game_state
        self.current_node = self.roots[game_state.start_player]

        action_sequence = game_state.game_actions
        for actions in action_sequence:
            
            act = actions[0]
            task = actions[1]

            action_index = 0 if act =="bet" else 1 if act =="call" else 2 if act =="fold" else 3
            if action_index < 3:
                if task == self.opponent_idx and self.current_node.children[action_index] is None:
                    self.current_node.children[action_index] = self.ProgramDecisionNode(self.player_idx, self.current_node,action_index)
                elif task == self.player_idx and self.current_node.children[action_index] is None:
                    self.current_node.children[action_index] = self.OpponentNode(self.opponent_idx,self.current_node,action_index)
                # move to next node
                self.current_node = self.current_node.children[action_index]
            else:

                # Sort task, which should be some cards
                sorted_cards = sorted(task, key=lambda x: x.suit.value, reverse=True)
                task = tuple(sorted(sorted_cards, key=lambda x: x.value, reverse=True))
               


                # The current node is mistakenly a programdecision or an opponent
                # Go to parent and change the node; parent is either a program decision or an opponent node
                if not isinstance(self.current_node,self.ChanceNode):
                    index = self.current_node.parent_action
                    self.current_node = self.current_node.parent
                    self.current_node.children[index] = self.ChanceNode(None,self.current_node,index,task)
                    self.current_node = self.current_node.children[index]
                    self.add_chance_outcome(self.current_node,task)
                # move to next move
                self.add_chance_outcome(self.current_node,task)

                 # needed since tuples suck
                if len(task) == 1:
                    task = task[0]
                self.current_node = self.current_node.children_and_freqs[task][0]
           
            
        # self.current_node should point to the current node
        child_evs = list()
        for a in range(len(self.current_node.children)):
            child = self.current_node.children[a]
            if child is not None:
                child_ev = self.dfs(child)
                child_evs.append((child_ev,a))
            else:
                coarse_stats = self.get_coarse_statistics(self.current_node)
                if a == 0:
                    coarse_stats += 1                                                             
                hist_pdf = self.coarse_abstraction[coarse_stats]
                child_ev = self.get_ev_from_hist(hist_pdf, self.match_state, self.player_idx)
                child_evs.append((child_ev,a))
        child_evs.sort()
        idx = 0 # this is miximax
        rand = random.random()
        if rand < 0.1: # this is miximix
            idx = 1
        chosen_a = child_evs[idx][1]
        actual_a = None
        if chosen_a == 0:
            actual_a = ('bet', None)
        elif chosen_a == 1:
            actual_a = ('call', None)
        else:
            actual_a = ('fold', None)
        return actual_a, child_evs[idx][0]
        


                    

       