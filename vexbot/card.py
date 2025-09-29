
import random
import enum
from copy import deepcopy

handtype_to_str = {0:'Straight Flush', 1:'Four of a Kind', 2:'Full House', 3:'Flush', 4:'Straight', 5:'Three of a Kind', 6:'Two Pair', 7:'Pair', 8:'High Card'}
class Suit(enum.Enum):
    Club = 'c'
    Diamond = 'd'
    Heart =  'h'
    Spade = 's'

class Card:
    def __init__(self,suit,value):
        self.suit = suit
        self.value = value
    def __repr__(self):
        v = self.value
        if v == 11:
            v = 'J'
        elif v == 12:
            v = 'Q'
        elif v == 13:
            v = 'K'
        elif v == 14:
            v = 'A'
        return repr(str(v) + str(self.suit.value))

class Deck:
    def __init__(self):
        self.deck = list()
        i = 0
        for suit in Suit:
            for value in range(2,15):
                self.deck.append(Card(suit,value))
        self.out = list()
    
    def shuffle(self):
        random.shuffle(self.deck)

    def deal(self,numCards):
        try:
            # draw = random.sample(self.deck,numCards)
            draw = [self.deck[i] for i in range(numCards)]
            for card in draw:
                self.deck.remove(card)
                self.out.append(card)
            return draw

        except ValueError:
            raise ValueError("Unable to draw cards: Deck does not have enough cards")

class Hand:

    @staticmethod
    def is_straight_flush(cards):
        if Hand.is_flush(cards):
            return Hand.is_straight(cards)
        return None

    @staticmethod
    def is_four_oak(cards):
        d = dict()
        for card in cards:
            if card.value not in d:
                d[card.value] = 0
            d[card.value] += 1
        is_four = False
        four_val = -1
        for k in d:
            if d[k] == 4:
                is_four = True
                four_val = k
                break
        comp_cards = None
        if is_four:
            comp_cards = deepcopy(cards)
            e = None
            for i in range(len(comp_cards)):
                if comp_cards[i].value != four_val:
                    e = comp_cards[i]
            comp_cards.remove(e)
            comp_cards.append(e)
        return comp_cards
               

    @staticmethod
    def is_full_house(cards):
        d = dict()
        for card in cards:
            if card.value not in d:
                d[card.value] = 0
            d[card.value] += 1
        is_three = False
        three_val = -1
        is_two = False
        two_val = -1
        for k in d:
            if d[k] == 3:
                is_three = True
                three_val = k
            if d[k] == 2:
                is_two = True
                two_val = k
        comp_cards = None
        if is_three and is_two:
            comp_cards = list()
            for card in cards:
                comp_card = deepcopy(card)
                if card.value == three_val:
                    comp_cards.insert(0, comp_card)
                else:
                    comp_cards.append(comp_card)
        return comp_cards

    @staticmethod
    def is_flush(cards):
        s = set()
        for card in cards:
            s.add(card.suit)
        comp_cards = None
        if len(s) == 1:
            comp_cards = deepcopy(cards)
        return comp_cards
    
    @staticmethod
    def is_straight(cards):
        a = [card.value for card in cards]
        is_str = True
        for i in range(1,len(a)):
            if a[i] != a[i-1] - 1:
                is_str = False
                break
        if (not is_str) and a[0] == 14:
            a.remove(a[0])
            a.append(1)
            is_str = True
            for i in range(1,len(a)):
                if a[i] != a[i-1] - 1:
                    is_str = False
                    break
        comp_cards = None
        if is_str:
            comp_cards = deepcopy(cards)
            if a[-1] == 1:
                comp_cards.append(comp_cards[0])
                comp_cards.remove(comp_cards[0])
        return comp_cards
            


    @staticmethod
    def is_three_oak(cards):
        d = dict()
        for card in cards:
            if card.value not in d:
                d[card.value] = 0
            d[card.value] += 1
        is_three = False
        three_val = -1
        for k in d:
            if d[k] == 3:
                is_three = True
                three_val = k
                break
        comp_cards = None
        if is_three:
            comp_cards = list()
            for card in cards:
                comp_card = deepcopy(card)
                if card.value == three_val:
                    comp_cards.insert(0, comp_card)
                else:
                    comp_cards.append(comp_card)
            e = comp_cards[3]
            if e.value < comp_cards[4].value:
                comp_cards.remove(e)
                comp_cards.append(e)
        return comp_cards

    @staticmethod
    def is_two_pair(cards):
        d = dict()
        for card in cards:
            if card.value not in d:
                d[card.value] = 0
            d[card.value] += 1
        n_pairs = 0
        two_vals = [-1, -1]
        for k in d:
            if d[k] == 2:
                two_vals[n_pairs] = k
                n_pairs += 1
        comp_cards = None
        if n_pairs == 2:
            if two_vals[0] < two_vals[1]:
                temp = two_vals[0]
                two_vals[0] = two_vals[1]
                two_vals[1] = temp
            comp_cards = list()
            # append high pair 
            for card in cards:
                if card.value == two_vals[0]:
                    comp_card = deepcopy(card)
                    comp_cards.append(comp_card)
            # append low pair followed by single
            for card in cards:
                if card.value == two_vals[1]:
                    comp_card = deepcopy(card)
                    comp_cards.insert(2, comp_card)
                elif card.value != two_vals[0]:
                    comp_card = deepcopy(card)
                    comp_cards.append(comp_card)
        return comp_cards

    @staticmethod
    def is_pair(cards):
        d = dict()
        for card in cards:
            if card.value not in d:
                d[card.value] = 0
            d[card.value] += 1
        is_pair = False
        pair_val = -1
        for k in d:
            if d[k] == 2:
                is_pair = True
                pair_val = k
                break
        comp_cards = None
        if is_pair:
            comp_cards = deepcopy(cards)
            pair_cards = list()
            for comp_card in comp_cards:
                if comp_card.value == pair_val:
                    pair_cards.append(comp_card)
            for pair_card in pair_cards:
                comp_cards.remove(pair_card)
                comp_cards.insert(0,pair_card)
        return comp_cards
            
