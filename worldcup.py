import random
import uuid
import itertools

def gameString(g, t1, t2, res):
    return "[%s] - %s v. %s : %s" % (g, t1, t2, res)

class WorldCup(object):
    def __init__(self, teams):
        self.teams = teams
        self.tokenPrefix = str(uuid.uuid4())
        # World Cups first stage have multiples of four.
        # We fill to the nearest group with a "token" team.
        # If this team wins, we repeat the entire World Cup.
        if len(teams) % 4 != 0:
            self.teams.extend(["%s%i" % (self.tokenPrefix, i) for i in range(4 - len(teams) % 4)])
        self.pc = len(teams)
        self.notplayed = ""
        self.groups = self.createGroups()
        self.gsroster = self.createGroupStageRoster(self.groups)
        self.gsday = 0
    
    def printGroups(self):
        gs = self.groups.keys()
        gs.sort()
        for g in gs:
            print("%s: %s" % (g, self.groups[g]))

    def printGroupRoster(self):
        for i in range(1,7):
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
        gs = groups.keys()
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
            day = self.gsroster[d]
            for (g, t1, t2), res in self.gsroster[d].items():
                if res != self.notplayed:
                    raise Exception("Match %s already played!" % gameString(g,t1,t2,res))
                goals = random.randint(0,10)
                gt1, gt2 = 0, 0 
                for i in range(goals):
                    if random.randrange(256) % 2 == 0:
                        gt2 += 1
                    else:
                        gt1 += 1
                




if __name__ == "__main__":
    sol = WorldCup(["Team %d" % i for i in range(31)])
    print("Initial groups:")
    sol.printGroups()
    print("Initial roster:")
    sol.printGroupRoster()
    sol.playGroupStageGame()