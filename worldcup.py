import random
import uuid
import itertools
import math
import copy

def gameString(g, t1, t2, res):
    return "[%s] - %s v. %s : %s" % (g, t1, t2, res)

class WorldCup(object):
    def __init__(self, teams):
        self.tokenPrefix = "Virtual Team "
        self.teams = self.packTeams(teams, self.tokenPrefix)
        
        # World Cups can be played with 16, 32, 64, or 128 players.
        # We create token teams to fill up to one of these powers.
        # If this team wins, we repeat the entire World Cup.
        self.pc = len(teams)
        self.notplayed = ""
        self.groups = self.createGroups()
        self.gs = sorted(self.groups.keys())
        self.gw = {}
        self.gsroster = self.createGroupStageRoster(self.groups)
        self.knroster = None
        self.gsday = 0
        self
    
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

    def printGroups(self):
        for g in self.gs:
            print("%s: %s" % (g, self.groups[g]))

    def printGroupRoster(self, lastDay = False):
        for i in range(1,7) if not lastDay else range(self.gsday, self.gsday+1):
            print("Day %d games:" % i)
            for (g, t1, t2), res in self.gsroster[i].items():
                print(gameString(g, t1, t2, res))

    def printGroupWinners(self):
        for g in self.gs:
            gw = self.gw[g]
            print("%s: 1st Place: %s | 2nd Place: %s" % (g, gw[0], gw[1]))

    def createGroups(self):
        if self.pc % 4 != 0:
            raise Exception("Can't create initial roster with %d teams" % self.pc)
        random.seed()
        groups = {}
        # We first create len(teams) / 4 groups.
        for i in range(int(self.pc / 4)):
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

    def getWinners(self, group):
        if group not in self.gw:
            byPoints = sorted(self.groups[group].items(), key=lambda i: i[1], reverse=True)
            first = byPoints[0]
            second = byPoints[1]
            third = byPoints[2]
            # TODO(rafa): Use roster results to check goals for. For now choose one.
            if third[1] == second[1]:
                self.gw[group] = first, random.choice((second, third))
            else:
                self.gw[group] = first, second
        return self.gw[group]

    
    def createKnockoutStageRoster(self):
        # Once we have played all games, we get winners on each group, and we create the rosters.
        # Like a World Cup, we will pit 1st place of a group v. 2nd place of another.
        # Unlike a World Cup, we can have 64, 128, 256, 512... so we'll just create Day 7.
        r = {7 : {}}
        fp = [g for g in self.groups.keys()]
        sp = copy.deepcopy(fp)
        while len(fp) > 0 and len(sp) > 0:
            # Select a random from first place list.
            g1 = random.choice(fp)
            g11, _ = self.getWinners(g1)

            # Remove it from first place
            fp.remove(g1)

            removed = False
            # Remove g2 from second place, choose g2, add back g1, and remove g2.
            if g1 in sp:
                removed = True
                sp.remove(g1)
            g2 = random.choice(sp)
            if removed:
                sp.append(g1)

            sp.remove(g2)
            # Add entry
            _, g22 = self.getWinners(g2)
            r[7][(g11[0], g22[0])] = self.notplayed
            # print("[%s] 1st Place %s v. [%s] 2nd Place %s" % (g1, g11[0], g2, g22[0]))
        if len(sp) > 0 or len(fp) > 0:
            raise Exception ("Mismatched first/second place list")

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
                r[i][(g, t1, t2)] = self.notplayed
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

    def playGroupStageGame(self, one_day=False):
        # Group stage requires 6 games per group. We group a single game across all groups in "Days".
        # For each game in a day:
        # * Get a random number between 0 and 10 for the number of goals to be scored.
        # * For each goal, choose a random team "scorer"
        # Winner of each game gets 3 points
        # Ties get 1 point each.
        # Loser gets 0 points.
        # If one_day is True, it will play one day only, and return True if it's Day 6, False otherwise.
        # Otherwise, it will play the entire group stage, and return True.
        while self.gsday < 6:
            self.gsday += 1
            day = self.gsroster[self.gsday]
            for (g, t1, t2), res in day.items():
                if res != self.notplayed:
                    raise Exception("Match %s already played!" % gameString(g,t1,t2,res))
                gt1, gt2 = self.playOneGame()
                # Update the roster
                day[(g,t1,t2)] = (gt1, gt2)
                if gt1 > gt2:
                    # t1 won. Yay!
                    self.groups[g][t1] += 3
                elif gt2 > gt1:
                    # t2 won. Yay!
                    self.groups[g][t2] += 3
                else:
                    # Tie, 1 point each
                    self.groups[g][t1] += 1
                    self.groups[g][t2] += 1
            if self.gsday == 6:
                self.createKnockoutStageRoster()
            if one_day:
                return False
        return True


if __name__ == "__main__":
    sol = WorldCup(["Team %d" % i for i in range(32)])
    # print("Initial groups:")
    # sol.printGroups()
    # print("Initial roster:")
    # sol.printGroupRoster()
    print("\nGroup Stage Game")
    while not sol.playGroupStageGame(True):
        sol.printGroupRoster(True)
    print("\nAfter group stage")
    sol.printGroups()
    print("\nGroup winners:")
    sol.printGroupWinners()