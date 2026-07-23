import random, re
from static import Awaish
from money import bank
from typing import Literal

POKERMENU = "\n".join([
    "斗地主...",
    "p4 加入: 开始或加入一场斗地主，满四人后自动开始。",
    "~~p4 bot: 增加机器人(很傻)~~娅姐睡着了",
    "p4 退出: 在开始之前退出对局。",
    "p4 set <底分>: 加入后设置底分(默认50-60)",
    "p4 <牌>: 出牌，具体规则请查看出牌规则。",
    "p4 结束: 在对局中结束游戏。",
    "p4 规则: 获取扑克的出牌规则。",
])
POKERRULE = "\n".join([
    "游戏规则请自行参考[此处](https://baike.baidu.com/item/%E4%B8%8A%E6%B5%B7%E6%96%97%E5%9C%B0%E4%B8%BB/10293246)(<-是个链接)，要注意的是这里用==H==代表==10==，==小==代表小王，==大==代表大王。以下是出牌规则：",
    "使用==p 牌==出牌，例如==p 1==, ==p J==，大小写均可；",
    "使用==p .==跳过回合、==p check==查看自己目前的牌、==p all==查看所有玩家的牌",
    "多张相同面值的牌间使用==牌*张数==，例如==p 3*2==，==p 4*3==；",
    "顺子使用==最小牌-最大牌==，例如==p 4-8==，==p 6-A==；",
    "双顺或三顺使用==最小-最大*张数==，例如==p 3-5*2==，==p 4-5*3==；",
    "三带二、飞机等带的对子中不使用==*==，例如==p K*3 77==，==p 8-9*3 33 44==,注意带的对子的顺序要按照小到大排序 如33 44,AA 22,22 33,KK AA",
    "王炸直接发送==p 王炸==即可；",
    "剩余的就将这两种组合，不同组别用空格隔开即可，例如==p 4-5*3 7 9== ==p 7*4 99 HH==……",
    "玩得开心~"
])
class Card:
    NUMS = ["3", "4", "5", "6", "7", "8", "9", "H", "J", "Q", "K", "A", "2"]
    JOKERS = ["小", "大"]
    SORT = NUMS + JOKERS
    FSZ={"2","3","4","5","6","7","8","9","H","J","Q","K","A"}
class ReType:
    MULT_SINGLE = re.compile(r"^[2-9HJQKA大小]\*[23]$")
    STRAIGHT = re.compile(r"^[2-9HJQKA]-[2-9HJQKA](\*[23]|)$")
    THREE_WITH = re.compile(r"^[2-9HJQKA]\*3 ([2-9HJQKA大小])\1$")
    PLANE = re.compile(r"^[3-9HJQKA]-[3-9HJQKA]\*3(?: ([2-9HJQKA大小])\1)+$")
    BOMB = re.compile(r"^[2-9HJQKA]\*[45678]$")

class SingleHand:
    SINGLE = 1 
    MULT_SINGLE = 2
    STRAIGHT = 3
    MULT_STRAIGHT = 4
    THREE_WITH = 5
    PLANE = 6
    FOUR_WITH = 7
    BOMB = 8
    ROCKET = 9
    BOMBS = [BOMB, ROCKET]
    def __init__(self, msg: str=""):
        self.text = msg
        self.type: int | None = None
        self.length: int = 1
        self.withs_length: Literal[1, 2] = 1
        self.mults: Literal[1, 2, 3] = 1
        self.all_cards: str = ""
        self.max_num: str | int
        self.msg: str = ""
        self._parse_type(msg)


    def __str__(self):
        return self.text
    
    def execute(self, player: "Player"):
        if self.type is None:
            return

        self.max_num = Card.SORT.index(self.max_num)
        for card in set(self.all_cards):
            if player.cards.count(card) < self.all_cards.count(card):
                self.type = None
                self.msg = "牌数不足"
                break
    
    def _parse_type(self, msg: str):
        msg_list = msg.split(" ")
        # 单张
        if msg in Card.SORT:
            self.type = self.SINGLE
            self.all_cards = self.max_num = msg
        # 对子、三张
        elif ReType.MULT_SINGLE.fullmatch(msg):
            self.type = self.MULT_SINGLE
            self.mults = int(msg[-1])
            self.max_num = msg[0]
            self.all_cards = self.max_num * self.mults
        # 顺子、双顺、三顺
        elif ReType.STRAIGHT.fullmatch(msg):
            if "*" in msg:
                self.type = self.MULT_STRAIGHT
                self.mults = int(msg[-1])
            else:
                self.type = self.STRAIGHT
            STRA= ["A","2","3","4","5","6","7","8","9","H","J","Q","K","A"]
            st=msg[0],ed=msg[2]
            if st=="A" and ed=="A":
                sp=0,ep=13
            elif st=="A":
                sp=0,ep=STRA.index(ed)
            elif ed == "A":
                sp=STRA.index(st),ep=13
            else:
                sp=STRA.index(st),ep=STRA.index(ed)
            if sp>=ep:
                self.msg="牌型不合法:/"
                self.type=None
                return
            if "*" in msg:
                self.type = self.MULT_STRAIGHT
                self.mults = int(msg[-1])
            else:
                self.type = self.STRAIGHT

            self.length = ep- sp+ 1
            if self.mults == 1 and self.length < 5:
                self.msg = "顺子至少5张"
                self.type = None
            elif self.mults == 2 and self.length < 3:
                self.msg = "双顺至少3张"
                self.type = None
            elif self.length < 2:
                self.msg = "三顺至少2张"
                self.type = None
            self.max_num = msg[2]
            for num in range(sp,ep+1):
                self.all_cards += num * self.mults
        # 三带一、三带对
        elif ReType.THREE_WITH.fullmatch(msg):
            self.type = self.THREE_WITH
            self.max_num = msg[0]
            self.withs_length = 2
            if self.max_num==msg_list[1][0]:
                self.msg="三带和对子不能相同！"
                self.type=None
                return 
            self.all_cards = self.max_num * 3 + msg_list[1]
        # 飞机
        elif ReType.PLANE.fullmatch(msg):
            if not same_length(msg_list[1:]):
                self.msg = "带的牌格式有误"
                return
            self.type = self.PLANE
            start, end = Card.SORT.index(msg[0]), Card.SORT.index(msg[2])
            self.length = end - start + 1
            if self.length < 2:
                self.msg = "三顺至少2张"
                self.type = None
            elif len(msg_list[1:]) != self.length:
                self.msg = "带的牌数量须与三顺数量一致"
                self.type = None
                return
            else:
                wing=[Card.SORT.index(i[0]) for i in msg_list[1:]]
                if any(wing[i+1]!=wing[i]+1 for i in range(len(wing)-1)):
                    self.msg="带的对子必须连续"
                    self.type=None
                    return
            self.max_num = msg[2]
            self.withs_length = len(msg_list[1])
            for num in Card.SORT[start:end+1]:
                self.all_cards += num * 3
            self.all_cards += "".join(msg_list[1:])
        # 炸弹
        elif ReType.BOMB.fullmatch(msg):
            self.type = self.BOMB
            self.mults = int(msg[-1])
            self.max_num = msg[0]
            self.all_cards = self.max_num * self.mults
        # 王炸
        elif msg == "王炸":
            self.type = self.ROCKET
            self.all_cards = "大大小小"
            self.max_num = "大"

# 带多的带的是否为同长度(对或单)
def same_length(seq: list[str]) -> bool:
    length = len(seq[0])
    for i in seq[1:]:
        if len(i) != length:
            return False
    return True

class Player:
    is_bot: bool
    def __init__(self, name: str, trip: str):
        self.trip = trip
        self.name = name
        self.cards: list[str] = []
        self.naked = False
        self.is_landlord = False
        self.report_score=0
        self.turned=0
        self.bolim=99999
        self.reported=0
        self.isrptusef=0
        
    def __str__(self):
        return self.name
    def __eq__(self, value):
        return self.trip == value
    def format(self) -> str:
        return " ".join(self.cards)

class Human(Player):
    is_bot = False

class Hand(list):
    def __init__(self, *args):
        super().__init__(*args)

class AutoBot(Player):
    is_bot = True
    def __init__(self, name, trip):
        super().__init__(name, trip)
        # self.cards = Hand()
        self.pass_all = False
        self.types: dict[str | int, list | bool]

    def get_types(self) -> dict:
        setCards = set(self.cards)
        allType = {
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],
            6: [],
            7: [],
            8: [],
            "st": self._get_straights(setCards, 5)
        }
        
        for card in setCards:
            allType[self.cards.count(card)].append(card)
        for i in range(1, 5):
            allType[i].sort(key=lambda x: Card.SORT.index(x))

        allType["2st"] = self._get_straights(allType[2], 3)
        allType["3st"] = self._get_straights(allType[3], 2)

        if "大" in self.cards and "小" in self.cards:
            allType["王炸"] = True
        else:
            allType["王炸"] = False

        return allType
    
    def _get_straights(self, cards, min_len: int) -> list[list]:
        result = []
        valids = [Card.SORT.index(i) for i in cards if i not in "2小大"]
        valids.sort()
        
        if len(valids) < min_len:
            return result
        
        start = 0
        for i in range(1, len(valids)):
            if valids[i] != valids[i-1] + 1:
                length = len(valids[start:i])
                if length >= min_len:
                    result.append([valids[start], length])
                start = i
        if len(valids) - start >= min_len:
            result.append([valids[start], len(valids) - start])

        return result

    def execute(self, player: Human, cmd: str) -> str:
        if player.is_landlord or self.is_landlord:
            return "只有同阵营玩家能操控bot"
        
        if cmd == ".":
            self.pass_all = not self.pass_all
            return f"设置成功，当前禁言：{self.pass_all}"

    def pop_type(self, type, times: int=1) -> list:
        types = self.types
        if type not in types:
            return []
        text = []
        # for _ in range(times):
        #     for card in types[type]:
        #         if card

    def _first_play(self, types: dict, last_player: Human) -> str:
        if types["3st"]:
            start, length = types["3st"].pop(0)
            end = Card.SORT[start + length - 1]
            start = Card.SORT[start]
            if len(types[1]) >= length:
                withs = " ".join(str(types[1].pop(0)) for _ in range(length))
                text = f"{start}-{end}*3 {withs}"
            elif len(types[2]) >= length:
                withs = " ".join(str(types[2].pop(0))*2 for _ in range(length))
                text = f"{start}-{end}*3 {withs}"
            else:
                text = f"{start}-{end}*3"
        elif types[3]:
            three = types[3].pop(0)
            if types[1]:
                text = f"{three}*3 {types[1].pop(0)}"
            elif types[2]:
                text = f"{three}*3 {str(types[2].pop(0))*2}"
        
        elif types["2st"]:
            start, length = types["2st"].pop(0)
            end = Card.SORT[start + length - 1]
            start = Card.SORT[start]
            text = f"{start}-{end}*2"
        elif types["st"]:
            start, length = types["st"].pop(0)
            text = f"{Card.SORT[start]}-{Card.SORT[start + length - 1]}"

        elif types[1]:
            text = f"{types[1].pop(0)}"
        elif types[2]:
            text = f"{types[2].pop(0)}*2"
        else:
            if len(types[1]) >= 2:
                withs = " ".join(str(types[1].pop(0)) for _ in range(2))
                text = f"{types[4].pop(0)}*4 {withs}"
            elif len(types[2]) >= 2:
                withs = " ".join(str(types[2].pop(0))*2 for _ in range(2))
                text = f"{types[4].pop(0)}*4 {withs}"
            else:
                text = f"{types[4].pop(0)}*4"
        return text

    def _follow_play(self, types: dict, last_player: Human, last_hand: SingleHand) -> str:
        text = ""
        max_num = last_hand.max_num
        isFriend = not (self.is_landlord or last_player.is_landlord)
        
        # 别太坑队友
        if isFriend and max_num > 10:
            text = "."
        # 单张两张三张四张
        elif last_hand.type == SingleHand.SINGLE or last_hand.type == SingleHand.MULT_SINGLE:
            times = last_hand.mults
            if times == 4 and isFriend:
                return "."
            for card in types[times]:
                if Card.SORT.index(card) > max_num:
                    if times == 1:
                        text = card
                    else:
                        text = f"{card}*{times}"
                    break
        # 顺子双顺三顺
        elif last_hand.type == SingleHand.STRAIGHT or last_hand.type == SingleHand.MULT_STRAIGHT:
            times = last_hand.mults
            if times == 1:
                sts = types["st"]
            elif times == 2:
                sts = types["2st"]
            else:
                sts = types["3st"]
            llength = last_hand.length
            for start, length in sts:
                if length >= llength:
                    rend = start + length - 1
                    rstart = rend - llength + 1
                    if rstart > max_num:
                        if times == 1:
                            text = f"{Card.SORT[rstart]}-{Card.SORT[rend]}"
                        else:
                            text = f"{Card.SORT[rstart]}-{Card.SORT[rend]}*{times}"
                        break
        # 三带一、三带对
        elif last_hand.type == SingleHand.THREE_WITH:
            withs_length = last_hand.withs_length
            for card in types[3]:
                if Card.SORT.index(card) > max_num and types[withs_length]:
                    text = f"{card}*3 {types[withs_length].pop(0)*withs_length}"
        # 飞机
        elif last_hand.type == SingleHand.PLANE and not isFriend:
            llength = last_hand.length
            withs_length = last_hand.withs_length
            times=3
            for start, length in types["3st"]:
                if length >= llength:
                    rend = start + length - 1
                    if Card.SORT[rend - llength + 1] > max_num and len(types[withs_length]) >= llength:
                        withs = types[withs_length].pop(0)*withs_length
                        for _ in range(llength-1):
                            withs += f" {types[withs_length].pop(0)*withs_length}"
                        text = f"{Card.SORT[start]}-{Card.SORT[rend]}*{times} {withs}"

        return text or "."

    def play(self) -> str:
        if game.status == game.ROB_LANDLORD:
            return "."

        self.types = self.get_types()
        # 本轮第一发
        if game.last_hand.type is None:
            return self._first_play(self.types, game.last_player)
        elif self.pass_all:
            return "."
        # 接别人的牌
        else:
            return self._follow_play(self.types, game.last_player, game.last_hand)

class Poker:
    CLOSED = 0
    ROB_LANDLORD = 1
    FIRST_TURN = 2
    OPEN = 3
    PLAYING = [FIRST_TURN, OPEN]
    def __init__(self):
        self.context: Awaish
        self.status = self.CLOSED

        self.cards: list[str]
        self.last_hand: SingleHand = SingleHand()
        
        self.players: list[Human | AutoBot] = []
        self.player_index: int
        self.last_player: Human | AutoBot
        
        self.base_money: int = 0
        self.mults: int = 0
        
        self.anti_spring_count: int # 地主出完一手后剩余牌数
        self.mark=""
        self.biaojiweiwang=0
        self.touliao=0
        self.lasthuangfan=0
        self.ishuangfan=0
        self.now_rs=0
        self.calltimes=0

    @property
    def landlord(self) -> Human | AutoBot:
        for player in self.players:
            if player.is_landlord:
                return player
    @property
    def current_player(self):
        return self.players[self.player_index]
    
    def _init_cards(self):
        self.cards = []
        for _ in range(8):
            for num in Card.NUMS:
                self.cards.append(num)
        for _ in range(2):
            for joker in Card.JOKERS:
                self.cards.append(joker)
        random.shuffle(self.cards)

    def get_player(self, nick: str="", trip: str="") -> Human | AutoBot | None:
        for player in self.players:
            if ((trip and player.trip == trip) or
                (not player.trip and player.name == nick)):
                return player

    def _check_bot(self):
        if self.status and self.current_player.is_bot:
            bot: AutoBot = self.current_player
            self.play(bot.name, bot.trip, bot.play())

    def _format_order(self) -> str:
        text = []
        for i, player in enumerate(self.players):
            if i == self.player_index:
                text.append(f"=={player}==")
            else:
                text.append(player.name)
        return "顺序: " + " -> ".join(text)

    def _format_all(self) -> str:
        text = []
        for player in self.players:
            nick = player.name
            if player.is_landlord:
                nick += "(地主)"

            if player.naked:
                text.append(f"{nick}(明牌): {player.format()}")
            else:
                text.append(f"{nick}: {len(player.cards)}张")
        return "\n".join(text)
    
    def _check_end(self) -> bool:
        player = self.current_player
        if not player.cards:
            farmers: list[Human | AutoBot] = []
            player_cards: list[str] = []
            is_spring = True
            is_anti_spring = True
            moneyless = False

            for player_ in self.players:
                if not player_.is_landlord:
                    farmers.append(player_)
                    if len(player_.cards) != 25:
                        is_spring = False
                    if len(self.landlord.cards)!=self.anti_spring_count:
                        is_anti_spring=0
                if player_.cards:
                    player_cards.append(f"{player_.name}的牌：{player_.format()}")
                if not bank.get(player_.trip):
                    moneyless = True

            if player.is_landlord:
                winner = player.name
            else:
                winner = farmers[0].name + " @" + farmers[1].name+" @"+farmers[2].name

            self.context.appText(f"@{winner} 获胜！")
            self.context.appText("\n---")
            self.context.appText("\n".join(player_cards))
            self.context.appText("\n---")
            if is_spring and player.is_landlord:
                self.mults *= 2
                self.context.appText("春天！！！！！！！！！！！！倍数翻倍！🍾🍾🍾")
            elif is_anti_spring and not player.is_landlord:
                self.mults *= 2
                self.context.appText("反春天！！！！！！！！！！！！！！倍数翻倍！🍾🍾🍾")
            if self.lasthuangfan:
                self.mults*=2
            if self.biaojiweiwang:
                self.mults*=2
            if self.touliao and player.is_landlord:
                self.mults=self.mults*4//3
            self.lasthuangfan=0
            self.context.appText(f"底分{self.base_money}，倍数{self.mults}")
            
            if not moneyless:
                landlord = self.landlord
                base_money = self.base_money * self.mults
                if landlord and landlord.reported and not player.is_landlord: 
                    self.context.appText("地主报到后输牌，此局无效!")
                    self.end_game()
                    return True
                for farmer in farmers:
                    if player.is_landlord:
                        bank.give(farmer.trip, landlord.trip, base_money, "斗地主-", benefit=True)
                        self.context.appText(f"{farmer}输给了{landlord} **{base_money}**阿瓦豆。")
                    else:
                        bank.give(landlord.trip, farmer.trip, base_money, "斗地主-", benefit=True)
                        self.context.appText(f"{landlord}输给了{farmer} **{base_money}**阿瓦豆。")

            self.end_game()
            return True

        if len(player.cards) <= 3 and self.last_player == player:
            self.context.appText(f"{player}只剩**{len(player.cards)}**张牌了！")

        return False

    def _next_player(self):
        if self._check_end():
            return
        
        self.player_index = (self.player_index + 1) % len(self.players)
        player = self.current_player
        if self.status == self.ROB_LANDLORD:
            if self.calltimes>=4:
                if self.mults==0:
                    self.context.appText("荒番喵，下局倍数×2喵。")
                    self.lasthuangfan = 1
                    self.start()
                    return
                self.context.appText(f"{self.last_player}叫档最高，成为地主")
                self.player_index = self.players.index(self.last_player)
                self._set_landlord(self.last_player)
                self._set_bolim()
                return
            else:
                self.context.appText(f"轮到 @{player} 了,请叫分~")
        elif player==self.last_player:
            self.last_hand = SingleHand()
            self.context.appText(f"所有玩家都不要，@{player} 继续出牌")
        else:
            self.context.appText(f"轮到 @{player}")

    def _set_bolim(self):
        for i in self.players:
            if i.is_landlord:
                i.bolim=99999
            elif i.turned==0 :
                i.bolim=99999
            elif i.report_score==2:
                i.bolim=2
            else :
                i.bolim=1

    def _rob_landlord(self, msg: str):
        player = self.current_player
        if msg == ".":
            self.calltimes+=1
            player.turned=1
            player.report_score=0
            self.context.appText(f"{player}不叫")
            self._next_player()
        elif msg in ["1", "2", "3"]:
            point = int(msg)
            if point <= self.mults:
                self.context.appText(f"叫的数字必须比{self.mults}大！")
                return
            self.calltimes+=1
            player.report_score=point
            player.turned=True
            self.mults = point
            self.last_player = player
            self.context.appText(f"{player}叫出了{point}档")

            if point == 3:
                player.report_score=3
                player.turned=1
                self.last_player=player
                self.mults=3
                if self.calltimes==1:
                    self.touliao=1
                    self.context.appText(f"{player}头撂! 赢牌按4档计豆，输牌按3档计豆")
                self.player_index = self.players.index(self.last_player)
                self._set_landlord(player)
                self._set_bolim()
                return 
            else:
                self._next_player()
        else:
            self.context.appText("命令错误，请先叫分")
        
    def _set_landlord(self, player: Human | AutoBot):
        self.status = self.FIRST_TURN


        self.mults = max(self.mults, 1)

        player.cards += self.cards
        player.cards.sort(key=lambda x: Card.SORT.index(x))

        player.is_landlord = True
        self.context.appText(
            f"{' '.join(self.cards)}是底牌，{player}是地主。\n" +
            f"底分{self.base_money}豆，基础倍数{self.mults}倍。\n" +
            f"游戏开始，地主@{player} 可发送==p 明==明牌，或直接出牌\n" +
            "发送==p 规则==可以查看出牌规则哦；"
        )

        if not player.is_bot:
            self.context.appText(f":\n你的牌：{player.format()}", "whisper", to=player.name)
        else:
            self.play(player.name, player.trip, player.play())
    
    def _play_card(self, msg: str):
        player = self.current_player
        if msg == "明":
            if self.status == self.FIRST_TURN:
                if player.naked:
                    self.context.appText("你已经明牌了！")
                elif not player.is_landlord:
                    self.context.appText("你不是地主")
                else:
                    player.naked = True
                    self.mults *= 2
                    self.context.appText(
                        f"{player}明牌！倍数翻倍，当前{self.mults}倍。\n"
                        f"以下是{player}的牌:\n{player.format()}"
                    )
            else:
                self.context.appText("只能在游戏开始时明牌")
            return
        if msg == ".":
            if self.status in self.PLAYING and self.last_hand.type is None:
                self.context.appText("由你开始的啦，随便出一张吧")
            else:
                self.context.appText(f"{player}不要")
                self._next_player()
            return

        hand = SingleHand(msg)
        last_hand = self.last_hand
        hand.execute(player)
        if hand.type is None:
            self.context.appText("出牌错误")
            self.context.appText(hand.msg)
            return
        if hand.type in SingleHand.BOMBS:
            if player.bolim<=0:
                self.context.appText(f"炸弹次数已用完qaq")
                return
        if last_hand.type is not None:
            if(hand.type==SingleHand.BOMB and last_hand.type==SingleHand.BOMB):
                if hand.mults<last_hand.mults or (hand.mults==last_hand.mults and hand.max_num<=last_hand.max_num):
                    self.context.appText("你的炸弹没有上家大")
                    return
            elif (hand.type == last_hand.type and hand.mults == last_hand.mults and
                hand.length == last_hand.length and hand.withs_length == last_hand.withs_length):
                if hand.max_num <= last_hand.max_num:
                    self.context.appText("你的牌没有上家大")
                    return
            elif hand.type not in SingleHand.BOMBS:
                self.context.appText("牌型不符")
                return
        for card in hand.all_cards:
            player.cards.remove(card)

        self.context.appText(f"{player}出了{msg}".replace("*", "\\*"))

        if self.status == self.FIRST_TURN:
            self.status = self.OPEN
            self.anti_spring_count = len(player.cards)

        if hand.type in SingleHand.BOMBS:
            self.mults *= 2
            player.bolim-=1
            self.context.appText(
                f"{player}出了炸弹，倍数翻倍💣💣💣\n"+
                f"当前倍数：{self.mults}"
            )
            self.context.appText(
                f"你还能出{player.bolim}次炸弹",
                "whisper",to=player.name
            )
            if hand.type == SingleHand.ROCKET:
                self.last_hand = SingleHand()
                if not player.cards:
                    self.last_player=player
                    self._check_end()
                else:
                    self.context.appText(f"@{player} 继续出牌")
                self._check_end()
                return

        self.last_hand = hand
        self.last_player = player
        if not player.cards:
            self._check_end()
            return
        self._next_player()

    def play(self, sender: str, trip: str, msg: str):
        player = self.get_player(sender, trip)
        player.name = sender
        if msg == "check":
            self.context.appText(
                f"地主：{self.landlord}，上家{self.last_player}的牌：{str(self.last_hand) or '无'}\n"
                + self._format_order() + "\n"
                + player.format(),
                "whisper", to=sender
            )
        elif msg == "all":
            self.context.appText(
                f"底分{self.base_money}，当前倍数{self.mults}\n" +
                self._format_order() + "\n" +
                "玩家手牌: \n" + self._format_all()
            )
        elif msg=="报到":
            if not player.is_landlord:
                self.context.appText("只有地主可以报到！")
            elif (player.cards.count("大")==2 and player.cards.count("小")==2)or any(player.cards.count(n)>=7 for n in Card.NUMS):
                if player.reported:
                    self.context.appText("你已经报到过了!")
                else :
                    player.reported=1
                    self.mults*=2
                    self.context.appText(
                        f"{player}报到了！/续标识/续标识/续标识 \n"
                        f"倍数翻倍！当前倍数：{self.mults}"
                    )
            else:
                self.context.appText("你手中没有 4 个王 或者 7/8星炸")
            return 
        elif self.current_player == trip:
            if self.status == self.ROB_LANDLORD:
                self._rob_landlord(msg)
            else:
                self._play_card(msg.upper())
        else:
            self.context.appText(f"现在是{self.current_player}的回合。")
        
        self._check_bot()
    
    def start(self):
        self.status = self.ROB_LANDLORD
        self.last_hand = SingleHand()
        self.player_index = 0
        self.base_money = self.base_money or random.randint(50, 60)
        self.mults = 0
        self.now_rs=0
        self.ishuangfan=0
        self.biaojiweiwang=0
        self.touliao=0
        self.calltimes=0

        self._init_cards()
        random.shuffle(self.players)
        
        for player in self.players:
            player.report_score=0
            player.turned=0
            player.bolim=99999
            player.reported=0
            player.isrptusef=0
            player.is_landlord=0
            player.naked=0
            player.cards.clear()
            for _ in range(25):
                player.cards.append(self.cards.pop())
            player.cards.sort(key=lambda x: Card.SORT.index(x))
            if not player.is_bot:
                self.context.appText("发牌完成\n你的牌：" + player.format(), "whisper", to=player.name)
        
        landlord = self.current_player

        self.mark=random.choice(landlord.cards)
        self.last_player = landlord
        self.context.appText(
            "发牌完成~\n" +
            self._format_order() +
            f"\n底分{self.base_money}豆\n" +
            f"随机到{landlord}拥有地主牌{self.mark}\n"
        )
        if self.mark=='小' or self.mark=='大':
            self.biaojiweiwang=1;
            self.context.appText(
                "标记为王,倍数翻倍!"
            )
        self.context.appText(
            f"@{landlord} 请发送`p 1/2/3`叫地主或`p .`选择不叫。"
        )

        self._check_bot()
    
    def end_game(self):
        self.status = self.CLOSED
        self.players = []
        
        self.base_money = 0

game = Poker()

def main(context: Awaish, sender: str, msg: str, bot: bool=False):
    if bot:
        trip = bank.offering_box
    else:
        trip = context.user["trip"]
    player = game.get_player(sender, trip)
    if msg == "规则":
        context.appText(POKERRULE)
    elif msg == "help":
        context.appText(POKERMENU)
    elif msg == "结束" and player:
        game.end_game()
        context.appText("唔，结束了;;;;")

        """
    elif msg[:3] == "bot":
        cmd = msg[4:] or context.nick
        if game.status and player:
            bot_obj = game.get_player(trip=bank.offering_box)
            context.appText(bot_obj.execute(player, cmd), "whisper", to=sender)
        elif bank.offering_box in game.players:
            context.appText("BOT!!!!!!!😭")
            main(context, cmd, "退出", bot=True)
        else:
            context.appText("BOT!!!!!!!ヾ|≧_≦|〃")
            main(context, cmd, "加入", bot=True)
        """

    elif msg == "退出":
        if game.status:
            context.appText("这局已经开始了，等下局吧(￣▽￣)")
        elif player is None:
            context.appText("你不在游戏中~")
        else:
            game.players.remove(player)
            context.appText("已成功退出(‾◡◝)")
    elif game.status and player:
        game.play(sender, trip, msg)
    elif msg == "加入":
        if game.status:
            context.appText("这局已经开始了，等下局吧(￣▽￣)")
            return
        elif player:
            context.appText("你已经加入过了，再找些人吧ヾ|≧_≦|〃")
            return

        if bot:
            game.players.append(AutoBot(sender, trip))
        else:
            if not bank.get(trip):
                context.appText("(有无银行玩家加入，本局可能不算钱)")
            game.players.append(Human(sender, trip))

        if len(game.players) == 4:
            game.context = context
            game.start()
        else:
            context.appText("加入成功，再找些人吧")
    elif msg.startswith("set") and player:
        if game.status:
            context.appText("这局已经开始了，等下局吧(￣▽￣)")
            return
        msg_list = msg.split(" ")
        try:
            point = int(msg_list[1])
        except:
            context.appText("参数错误！")
            return
        divide3 = point / 3
        for player in game.players:
            if bank.get(player.trip) and bank.getAttr(player.trip, "money") < divide3:
                context.appText("数字过大！")
                return
        game.base_money = point
        context.appText(f"成功设置底分为{game.base_money}")
    else:
        context.appText("命令错误，使用p4 help查看帮助")