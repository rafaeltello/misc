import random
import uuid
import itertools
import math
import copy

NOT_PLAYED = ""
THIRD_PLACE = "third"
FINAL = "final"

def gGameString(g, t1, t2, res):
    return "[%s] - %s v. %s : %s" % (g, t1, t2, res)

def kGameString(d, t1, t2, res):
    return "[Day %s] - %s v. %s : %s" % (d, t1, t2, res)

# WorldCup allows to choose a first, second, and third place from a set of "teams", using
# a format inspired by FIFA(R) World Cup's mechanics.
# For full details, visit https://en.wikipedia.org/wiki/FIFA_World_Cup
# In essence, it will first divide participants in groups of 4, which will compete against each other,
# obtaining points for each win or tie.
# Half of the group will move forward to the Knockout stage.
# In the first game of the knockout stage, each group winner will face a second-place from a different group.
# On this and all next rounds there are no ties; ties get solved through a round of 5 penalty kicks, and if not, 
# sudden death (first unmatched score wins).
# In order for this to work, the number of teams has to be a power of 2 greater than 8. The game will introduce virtual players
# until this condition is satisfied. This means that it's possible that the game is won by a virtual player. In this case, it's
# necessary to re-run the game.
class WorldCup(object):
    def __init__(self, teams):
        self.tokenPrefix = "Virtual Team "
        self.teams = self.packTeams(teams, self.tokenPrefix)
        
        # World Cups can be played with 16, 32, 64, or 128 players.
        # We create token teams to fill up to one of these powers.
        # If this team wins, we repeat the entire World Cup.
        self._pc = len(teams)
        
        self._groups = self.createGroups()
        self._gs = sorted(self._groups.keys())
        self.gw = {}
        self._gsroster = self.createGroupStageRoster(self._groups)
        self._knroster = None
        self._gday = 0
        self._cup = {}
    
    def packTeams(self, teams, tokenPrefix):
        tc = len(teams)
        if tc < 8:
            raise Exception("A World Cup should have at least 8 teams. Sorry.")
        # If we have 8, 16, 32, 64, 128, 256, we don't do anything.
        # Otherwise, we insert as many items as necessary to fill one of them.
        if tc & (tc - 1) != 0:
            extrateams = ["%s%i" % (tokenPrefix, i) for i in range(tc, 2**(int(math.log2(tc)) + 1))]
            print("***Input was %d teams. To ensure the tournament can be played as a tournament (with %d teams), adding extra: %s" % (tc, tc + len(extrateams), extrateams))
            teams.extend(extrateams)
        return teams

    def printWinners(self):
        if len(self._cup) != 3:
            return
        print("\n\n\nWorld Cup Results")
        print("First Place:   %s" % self._cup[1])
        print("Second Place:  %s" % self._cup[2])
        print("Third Place:   %s" % self._cup[3])

    def areAllWinnersReal(self):
        return not any([(self.tokenPrefix in i) for i in self._cup.values()])

    def printGroups(self):
        for g in self._gs:
            print("%s: %s" % (g, self._groups[g]))

    def printKnockoutRoster(self, lastDay = False):
        for i in range(7, 7+len(self._knroster)) if not lastDay else range(self._gday, self._gday+1):
            print("Knockout Day %d games:" % i)
            for (t1, t2), res in self._knroster[i].items():
                print(kGameString(i, t1, t2, res))

    def printGroupRoster(self, lastDay = False):
        for i in range(1,7) if not lastDay else range(self._gday, self._gday+1):
            print("Group Stage. Day %d games:" % i)
            for (g, t1, t2), res in self._gsroster[i].items():
                print(gGameString(g, t1, t2, res))

    def printGroupWinners(self):
        for g in self._gs:
            gw = self.gw[g]
            print("%s: 1st Place: %s | 2nd Place: %s" % (g, gw[0], gw[1]))

    def createGroups(self):
        if self._pc % 4 != 0:
            raise Exception("Can't create initial roster with %d teams" % self._pc)
        random.seed()
        groups = {}
        # We first create len(teams) / 4 groups.
        for i in range(int(self._pc / 4)):
            groups["Group %s" % (chr(ord('A') + i))] = {}
        
        # Assign each team to a random group
        # Sorry, no continents here.
        gs = list(groups.keys())
        for t in self.teams:
            g = random.choice(gs)
            groups[g][t] = 0
            if len(groups[g]) == 4:
                gs.remove(g)
        
        if len(gs) > 0:
            raise Exception("Unexpected non-full group after lottery")
        
        return groups

    def getGroupWinners(self, group):
        if group not in self.gw:
            byPoints = sorted(self._groups[group].items(), key=lambda i: i[1], reverse=True)
            first = byPoints[0]
            second = byPoints[1]
            third = byPoints[2]
            # TODO(rafa): Use roster results to check goals for. For now choose one.
            if third[1] == second[1]:
                self.gw[group] = first, random.choice((second, third))
            else:
                self.gw[group] = first, second
        return self.gw[group]

    def updateKnockoutStageRoster(self):
        winners = []; losers = []
        new_games = {}
        # This creates the next day of games.
        for (t1, t2), (s1, s2, _) in self._knroster[self._gday].items():
            if s1 > s2:
                winners.append(t1)
                losers.append(t2)
            else:
                winners.append(t2)
                losers.append(t1)
        
        # If there are 2 winners only, and we haven't done finals, we're about to play the final.
        # We schedule the third place race first.
        if len(winners) == 2:
            if len(self._cup) == 0:
                new_games[(losers[0], losers[1])] = THIRD_PLACE
                new_games[(winners[0], winners[1])] = FINAL
                winners.clear()
            else:
                raise Exception("No call to update should happen if the cup has entries")
        
        # Otherwise, we pick randomly winners and create new matches.
        while len(winners) >= 2:
            w1 = random.choice(winners)
            winners.remove(w1)
            w2 = random.choice(winners)
            winners.remove(w2)
            new_games[(w1, w2)] = NOT_PLAYED
        
        if len(winners) != 0:
            raise Exception("We got a winners leak!", winners)
        self._knroster[self._gday + 1] = new_games


    def createKnockoutStageRoster(self):
        # Once we have played all games, we get winners on each group, and we create the rosters.
        # Like a World Cup, we will pit 1st place of a group v. 2nd place of another.
        # Unlike a World Cup, we can have 64, 128, 256, 512... so we'll just create Day 7.
        r = {7 : {}}
        fp = [g for g in self._groups.keys()]
        sp = copy.deepcopy(fp)
        while len(fp) > 0 and len(sp) > 0:
            # Select a random from first place list.
            g1 = random.choice(fp)
            g11, _ = self.getGroupWinners(g1)

            # Remove it from first place
            fp.remove(g1)

            removed = False
            # Remove g2 from second place, choose g2, add back g1, and remove g2.
            if g1 in sp:
                removed = True
                sp.remove(g1)
            if len(sp) == 0:
                raise Exception("Shouldn't be empty!", r[7])
            g2 = random.choice(sp)
            if removed:
                sp.append(g1)

            sp.remove(g2)
            # Add entry
            _, g22 = self.getGroupWinners(g2)
            r[7][(g11[0], g22[0])] = NOT_PLAYED
            # print("[%s] 1st Place %s v. [%s] 2nd Place %s" % (g1, g11[0], g2, g22[0]))
        if len(sp) > 0 or len(fp) > 0:
            raise Exception ("Mismatched first/second place list")
        self._knroster = r

    def createGroupStageRoster(self, groups):
        # Resulting object has:
        # Day#: {(group, teamA, teamB): (scoreA, scoreB)}
        r = {i:{} for i in range(1,7)}
        for g, teams in groups.items():
            days = [i for i in range(1,7)]
            roster = list(itertools.combinations(teams, 2))
            for t1, t2 in roster:
                i = random.choice(days)
                days.remove(i)
                r[i][(g, t1, t2)] = NOT_PLAYED
        return r

    def playOneGame(self):
        # TODO(rafaeltello): Make the number of goals weighted based on actual statistics.
        goals = random.randint(0,10)
        gt1, gt2 = 0, 0 
        for _ in range(goals):
            if random.randrange(256) % 2 == 0:
                gt2 += 1
            else:
                gt1 += 1
        return gt1, gt2

    def playPenaltyKicks(self):
        gt1, gt2 = 0, 0 
        for kick in range(5):
            if random.randrange(256) % 2 == 0:
                gt2 += 1
            if random.randrange(256) % 2 == 1:
                gt1 += 1
            # If not recoverable, end
            if abs(gt1-gt2) > kick + 1:
                break
        # Sudden Death
        if gt1 == gt2:
            while True:
                if random.randrange(256) % 2 == 0:
                    gt2 += 1
                if random.randrange(256) % 2 == 1:
                    gt1 += 1
                if gt1 != gt2:
                    break
        return gt1, gt2

    def playKnockoutStageDay(self, one_day = False):
        # We will play each game day. Differences from group stage:
        # * No ties. If there's a tie, we go straight to penalties (life is too short for extra time)
        # * Semifinals AND finals will both have 2 games.
        # * In the finals, the first game determines the third place; the second the 1st and 2nd.
        # If one_day is True, it will play one day only, and return False if we have a World Cup winner, True otherwise.
        # Otherwise, it will play the entire knockout stage, and return False.
        while True:
            self._gday += 1
            game_over = False
            if self._gday not in self._knroster:
                raise Exception("Not yet implemented")
            games = self._knroster[self._gday]
            for (t1, t2), res in games.items():
                if res not in (NOT_PLAYED, THIRD_PLACE, FINAL):
                    raise Exception("Match %s already played!" % kGameString(self._gday, t1,t2,res))
                ks1, ks2 = self.playOneGame()
                gt = "Regular Time"
                if ks1 == ks2:
                    ks1, ks2 = self.playPenaltyKicks()
                    gt = "Penalties"     
                if res == THIRD_PLACE:
                    game_over = True
                    self._cup[3] = t1 if ks1 > ks2 else t2
                    gt = gt + " - Third Place"
                elif res == FINAL:
                    game_over = True
                    self._cup[1], self._cup[2] = (t1, t2) if ks1 > ks2 else (t2, t1)
                    gt = gt + " - Final"
                games[(t1, t2)] = (ks1, ks2, gt)
            if game_over:
                break
            self.updateKnockoutStageRoster()
            if one_day:
                return True
        return False

    def play(self, verbose=False):
        self.playGroupStageGame()
        if verbose:
            self.printGroupRoster()
            print("\n\nAfter group stage")
            self.printGroups()
        print("\n\nGroup Stage winners:")
        self.printGroupWinners()
        if verbose:
            print("\n\nKnockout Stage Games:")
            self.printKnockoutRoster()
        self.playKnockoutStageDay()
        self.printWinners()
        return self.areAllWinnersReal()

    def playGroupStageGame(self, one_day=False):
        # Group stage requires 6 games per group. We group a single game across all groups in "Days".
        # For each game in a day:
        # * Get a random number between 0 and 10 for the number of goals to be scored.
        # * For each goal, choose a random team "scorer"
        # Winner of each game gets 3 points
        # Ties get 1 point each.
        # Loser gets 0 points.
        # If one_day is True, it will play one day only, and return False if it's Day 6, True otherwise.
        # Otherwise, it will play the entire group stage, and return False.
        while self._gday < 6:
            self._gday += 1
            day = self._gsroster[self._gday]
            for (g, t1, t2), res in day.items():
                if res != NOT_PLAYED:
                    raise Exception("Match %s already played!" % gGameString(g,t1,t2,res))
                gt1, gt2 = self.playOneGame()
                # Update the roster
                day[(g,t1,t2)] = (gt1, gt2)
                if gt1 > gt2:
                    # t1 won. Yay!
                    self._groups[g][t1] += 3
                elif gt2 > gt1:
                    # t2 won. Yay!
                    self._groups[g][t2] += 3
                else:
                    # Tie, 1 point each
                    self._groups[g][t1] += 1
                    self._groups[g][t2] += 1
            if self._gday == 6:
                self.createKnockoutStageRoster()
            if one_day:
                return True
        return False


if __name__ == "__main__":
    while True:
        teams = ["Comment %d" % i for i in range(34)]
        wc = WorldCup(teams)
        valid = wc.play(True)
        if not valid:
            print("\n\n\n\nGame yielded an inexistent player as finalist. Retrying...")
        else:
            break
