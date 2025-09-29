import numpy as np
from card import Suit, Card, Deck, Hand, handtype_to_str
import random
from copy import deepcopy
from player import Player, RandomPlayer, RaisePlayer, VexBot


class GameState:
    """
    Represents a State in the game
    """
    # round = betting round, game = preflop to river, (match = many games)
    def __init__(self, num_players, small_blind_player, players_chips, variant):
        self.variant = variant
        self.betting_round = 0 # 0 = preflop, 1 = postflop, 2 = after turn, 3 = after river,
        self.deck = Deck()
        self.deck.shuffle()
        self.board = list()
        self.num_players = num_players

        self.current_bets = [0 for i in range(num_players)]
        self.small_blind = 20
        self.big_blind = 40

        self.players_chips = players_chips
        self.players_hands = [self.deal_cards(2) for i in range(num_players)]

        # self.pot = 0
        self.all_pots = [0]
        self.pots_players = [[i for i in range(num_players) if players_chips[i] is not 0]]

        self.is_player_set = [False for i in range(num_players)]
        self.is_player_all_in = [False for i in range(num_players)]
        self.folded = [False for i in range(num_players)]

        self.small_blind_player = small_blind_player
        self.big_blind_player = (small_blind_player + 1) % num_players
        self.start_player = (small_blind_player + 2) % num_players

        
        self.n_bets_left_init = [np.inf for i in range(num_players)]
        if self.variant == 'FL':
            self.n_bets_left_init = [3 for i in range(num_players)]
        self.n_bets_left = [v for v in self.n_bets_left_init]

        self.game_actions = list()

        self.setting_blinds = True
        self.current_better = self.small_blind_player
        self.act(('bet', self.small_blind))
        self.act(('bet', self.big_blind))
        self.setting_blinds = False

        self.should_showdown = False
        self.game_over = False
        
    def deal_cards(self,num):
        return self.deck.deal(num)
    
    def deal_to_board(self,num):
        cards = self.deal_cards(num)
        for card in cards:
            self.board.append(card)
    
    def check_if_hand_type(self, five_cards, hand_type):
        comp_cards = None
        if hand_type == 0:
            comp_cards = Hand.is_straight_flush(five_cards)
        elif hand_type == 1:
            comp_cards = Hand.is_four_oak(five_cards)
        elif hand_type == 2:
            comp_cards = Hand.is_full_house(five_cards)
        elif hand_type == 3:
            comp_cards = Hand.is_flush(five_cards)
        elif hand_type == 4:
            comp_cards = Hand.is_straight(five_cards)
        elif hand_type == 5:
            comp_cards = Hand.is_three_oak(five_cards)
        elif hand_type == 6:
            comp_cards = Hand.is_two_pair(five_cards)
        elif hand_type == 7:
            comp_cards = Hand.is_pair(five_cards)
        elif hand_type == 8:
            comp_cards = five_cards
        return comp_cards

    def check_for_hand(self, seven_cards, hand_type):
        for i in range(5, -1, -1):
            for j in range(6, i, -1):
                five_cards = [deepcopy(seven_cards[k]) for k in range(len(seven_cards)) if (k != i and k != j)]
                comparable_cards = self.check_if_hand_type(five_cards, hand_type)
                if comparable_cards:
                    return comparable_cards
        return None

    def determine_winners(self, pot_players):
        # tuple (hand type, player_idx, best 5 cards) 
        # hand_types : 0 - straight flush, 1 - four of a kind, 2 - full house, 3 - flush, 4 - straight, 5 - 3 of a kind, 6 - two pair, 7 - pair, 8 - high card
        best_five_cards_list = list() 
        best_hand_type = None
        for hand_type in range(9):
            for p_idx in pot_players:
                hand = deepcopy(self.players_hands[p_idx])
                board = deepcopy(self.board)
                seven_cards = sorted(board+hand, key=lambda x: x.value, reverse=True)
                p_best_five_cards = self.check_for_hand(seven_cards, hand_type)
                if p_best_five_cards:
                    best_five_cards_list.append((p_idx, p_best_five_cards))
            if len(best_five_cards_list) > 0:
                best_hand_type = hand_type
                break
                  
        winners = None
        if len(best_five_cards_list) == 1:
            winners = list()
            winners.append(best_five_cards_list[0][0])
        else:
            winners = [best_five_cards_list[i][0] for i in range(len(best_five_cards_list))]
            
            for i in range(5):
                max_level_card_value = -1
                for (p_idx, p_best_five_cards) in best_five_cards_list:
                    if p_idx in winners:
                        card = p_best_five_cards[i]
                        if card.value > max_level_card_value:
                            max_level_card_value = card.value
                for (p_idx, p_best_five_cards) in best_five_cards_list:
                    if p_idx in winners:
                        card = p_best_five_cards[i]
                        if card.value < max_level_card_value:
                            winners.remove(p_idx)
                if len(winners) == 1:
                    break
        print("Board:" + str(self.board) + ", Winners:"+str(winners)+", HandType: "+handtype_to_str[hand_type])
        curr_winner = -1
        for p_idx in pot_players:
            best_five = []
            for hand_type in range(9):
                hand = deepcopy(self.players_hands[p_idx])
                board = deepcopy(self.board)
                seven_cards = sorted(board+hand, key=lambda x: x.value, reverse=True)
                p_best_five_cards = self.check_for_hand(seven_cards, hand_type)
                if p_best_five_cards:
                    best_five = p_best_five_cards
                    break
            print("Player "+str(p_idx)+" - Hand:" + str(self.players_hands[p_idx])+ ", BestFive:" + str(best_five))            

        # could return hand type and best five cards
        return winners
            
    def pay_winners(self, winners, pot_idx):
        # if want more than 2 players, need to account for side pots
        pot = self.all_pots[pot_idx]
        prize = pot // len(winners)
        for winner in winners:
            self.players_chips[winner] += prize
        print(f"Winners:{winners}")
        self.all_pots[pot_idx] = 0

        # self.winners = winners
        # self.game_over = True

    def showdown(self):
        
        num_to_deal = 5 - len(self.board)
        if num_to_deal != 0:
            self.deal_to_board(num_to_deal)

        for pot_idx in range(len(self.all_pots)):

            winners = self.determine_winners(self.pots_players[pot_idx])
            self.pay_winners(winners, pot_idx)
        
    def update_round(self):

        # if all but one folded, its over
        num_not_folded = 0
        for f in self.folded:
            if not f:
                num_not_folded += 1
        if num_not_folded == 1:
            winners = list()
            for p_idx in range(self.num_players):
                if not self.folded[p_idx]:
                    winners.append(p_idx)
            for p_idx in range(self.num_players):
                self.all_pots[-1] += self.current_bets[p_idx]
                self.players_chips[p_idx] -= self.current_bets[p_idx]
                self.current_bets[p_idx] = 0
            for pot_idx in range(len(self.all_pots)):
                winners = self.determine_winners(self.pots_players[pot_idx])
                self.pay_winners(winners, pot_idx)
            self.pay_winners(winners, 0)
            self.game_over = True
            return

        # collect bets to pots
        min_bet_above_0 = np.inf
        for p_idx in range(self.num_players):
            current_bet = self.current_bets[p_idx]
            if current_bet != 0 and current_bet < min_bet_above_0:
                min_bet_above_0 = current_bet
        for p_idx in range(self.num_players):
            self.current_bets[p_idx] = min(self.current_bets[p_idx], min_bet_above_0)
            self.pot += self.current_bets[p_idx]
            self.players_chips[p_idx] -= self.current_bets[p_idx]
            self.current_bets[p_idx] = 0    

        # if should showdown, then do showdown
        if self.should_showdown:
            self.showdown()
            self.game_over = True
            return

        # deal to board
        if self.betting_round == 0:
            self.deal_to_board(3)  
            self.game_actions.append(('flop', tuple(self.board[0:3])))
        elif self.betting_round == 1:
            self.deal_to_board(1)
            self.game_actions.append(('turn', (self.board[3],)))
        elif self.betting_round == 2:
            self.deal_to_board(1)
            self.game_actions.append(('river', (self.board[4],)))
        # elif self.betting_round == 3:
        #     print()

        # new betting round
        self.is_player_set = [False for i in range(self.num_players)]  
        self.is_player_all_in = [False for i in range(self.num_players)]
        self.folded = [False for i in range(self.num_players)]
        self.n_bets_left = [v for v in self.n_bets_left_init]
        self.betting_round += 1  
        
    
    def bet(self, desired_amount):
        player_idx = self.current_better
        prev_bet = self.current_bets[(player_idx - 1) % self.num_players]
        chips = self.players_chips[player_idx]
        
        if self.variant == 'FL':
            desired_amount = prev_bet + self.big_blind if not self.setting_blinds else prev_bet + self.small_blind
            if self.betting_round == 2 or self.betting_round == 3:
                desired_amount += self.big_blind

        amount = desired_amount
        # setting blinds
        # if self.setting_blinds:
        #     if amount >= chips:
        #         amount = chips
        #         self.is_player_all_in[player_idx] = True
        #     self.current_bets[player_idx] = amount
        #     return
        # bet
        # won't happen in limit holdem
        # if desired_amount < prev_bet + self.big_blind:
        #     amount = prev_bet + self.big_blind
        if desired_amount >= chips:
            amount = chips
            self.is_player_all_in[player_idx] = True
        # else:
        #     amount = amount // self.big_blind * self.big_blind
        self.current_bets[player_idx] = amount
        self.game_actions.append(('bet',self.current_better))

        # if amount < self.players_chips:
        # if amount >= self.players_chips[player_idx]:
        #     amount = self.players_chips[player_idx]
        #     self.is_player_all_in[player_idx] = True
        # elif amount//self.big_blind != amount/self.big_blind:
        #     amount = amount//self.big_blind * self.big_blind
        # self.players_chips[player_idx] -= amount
        # self.current_bets[player_idx] += amount
            
        
    def call(self):
        player_idx = self.current_better
        prev_player_idx = (player_idx - 1) % self.num_players
        prev_bet = self.current_bets[(player_idx - 1) % self.num_players]
        chips = self.players_chips[player_idx]
        desired_amount = self.current_bets[prev_player_idx]
        # self.bet(amount_to_bet)
        # call
        amount = desired_amount
        if desired_amount >= chips:
            amount = chips
            self.is_player_all_in[player_idx] = True
        self.current_bets[player_idx] = amount
        self.game_actions.append(('call', self.current_better))

    def fold(self):
        player_idx = self.current_better
        self.folded[player_idx] = True
        self.game_actions.append(('fold', self.current_better))

    def is_all_set(self):
        num_not_folded = 0
        for p_idx in range(self.num_players):
            if self.folded[p_idx]:
                num_not_folded += 1
        if num_not_folded == 1:
            return True
        for p_idx in range(self.num_players):
            if not (self.is_player_set[p_idx] or self.is_player_all_in[p_idx]):
                return False
        return True


    def act(self, action):
        if action[0] == 'bet':
            prev_bet = self.current_bets[(self.current_better - 1) % self.num_players]
            chips = self.players_chips[self.current_better]
            if prev_bet >= chips or self.n_bets_left[self.current_better] == 0:
                self.call()
            else:
                self.bet(action[1])
                if not self.setting_blinds:
                    self.n_bets_left[self.current_better] -= 1
                if self.current_bets[self.current_better] > self.current_bets[(self.current_better-1)%self.num_players]:
                    self.is_player_set = [False for i in range(self.num_players)]
                
                # print('here')
        elif action[0] == 'call':
            self.call()
        elif action[0] == 'fold':
            self.fold()

        if not self.setting_blinds:
            self.is_player_set[self.current_better] = True

        just_betted = self.current_better
        self.current_better = (self.current_better + 1) % self.num_players
        while self.folded[self.current_better] or self.is_player_all_in[self.current_better]:
            self.current_better = (self.current_better + 1) % self.num_players
            if self.current_better == just_betted:
                break
        
        if self.is_all_set():
            num_not_all_in = 0
            for p_all_in in self.is_player_all_in:
                if not p_all_in:
                    num_not_all_in += 1
            if num_not_all_in < 2 or self.betting_round == 3:
                self.should_showdown = True
                self.game_actions.append(('showdown', None))

    
    def is_termination_state(self):
        return self.game_over

class MatchState:
    def __init__(self, num_players, initial_small_blind_player, initial_players_chips, variant):
        self.num_players = num_players
        self.small_blind_player = initial_small_blind_player
        self.players_chips = initial_players_chips
        self.current_game = 0
        self.variant = variant
        self.current_game_state = GameState(self.num_players, self.small_blind_player, self.players_chips, self.variant)
    
    def update_game(self):
        
        self.small_blind_player = (self.small_blind_player + 1) % self.num_players
        self.players_chips = [chips for chips in self.current_game_state.players_chips]
        self.current_game_state = GameState(self.num_players, self.small_blind_player, self.players_chips, self.variant)
        self.current_game += 1

    def is_termination_state(self):
        n_players_alive = 0
        for chips in self.players_chips:
            if chips != 0:
                n_players_alive += 1
        if n_players_alive > 1:
            return False
        return True

class MatchSimulator:
    def __init__(self, players, initial_small_blind_player=0, initial_players_chips=[2000,2000], n_games=100, variant='NL'):
        self.num_players = len(players)
        self.variant = variant
        self.match_state = MatchState(self.num_players, initial_small_blind_player, initial_players_chips, variant)
        self.current_game = -1
        self.players = players
        self.n_games = n_games

    def run(self):

        while self.current_game < self.n_games - 1 and not self.match_state.is_termination_state():
            self.current_game += 1

            game_state = self.match_state.current_game_state
            
            print(f"Game: {self.current_game}, Chips:{game_state.players_chips}, Bets:{game_state.current_bets}")
            while not game_state.is_termination_state():

                while not game_state.is_all_set():
                    current_better = game_state.current_better
                    action, value = self.players[current_better].policy( self.match_state )
                    
                    print(f"Game: {self.current_game}, Round:{game_state.betting_round}, Player: {current_better}, Chips:{game_state.players_chips[current_better]-game_state.current_bets[current_better]}, Action:{action}")

                    game_state.act(action)
                
                game_state.update_round()
            


            self.match_state.update_game()

        max_chips = -1
        winner = -1
        for p_idx, chips in enumerate(self.match_state.players_chips):
            if chips > max_chips:
                max_chips = chips
                winner = p_idx
        return winner, self.current_game, [chips for chips in self.match_state.players_chips]

if __name__ == '__main__':
    players = [RaisePlayer(0), RaisePlayer(1)]
    sim = MatchSimulator(players, n_games=3,initial_players_chips=[2000, 2000])
    sim.run()
    # x = np.linspace(0,100,10000)
    # y = np.log(x)
    # plt.plot(x,y)
    # plt.show()