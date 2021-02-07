import random
import uuid
import itertools
import math

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
        self.gsroster = self.createGroupStageRoster(self.groups)
        self.gsday = 0
    
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
        gs = list(self.groups.keys())
        gs.sort()
        for g in gs:
            print("%s: %s" % (g, self.groups[g]))

    def printGroupRoster(self, lastDay = False):
        for i in range(1,7) if not lastDay else range(self.gsday, self.gsday+1):
            print("Day %d games:" % i)
            for (g, t1, t2), res in self.gsroster[i].items():
                print(gameString(g, t1, t2, res))

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
                goals = random.randint(0,10)
                gt1, gt2 = 0, 0 
                for _ in range(goals):
                    if random.randrange(256) % 2 == 0:
                        gt2 += 1
                    else:
                        gt1 += 1
                # Update the roster
                day[(g,t1,t2)] = (gt1, gt2)
                if t1 > t2:
                    # t1 won. Yay!
                    self.groups[g][t1] += 3
                elif t2 > t1:
                    # t2 won. Yay!
                    self.groups[g][t2] += 3
                else:
                    # Tie, 1 point each
                    self.groups[g][t1] += 1
                    self.groups[g][t2] += 1
            if one_day:
                return False
        return True


if __name__ == "__main__":
    sol = WorldCup(["Team %d" % i for i in range(32)])
    # print("Initial groups:")
    # sol.printGroups()
    # print("Initial roster:")
    # sol.printGroupRoster()
    print("Group Stage Game")
    while not sol.playGroupStageGame(True):
        sol.printGroupRoster(True)