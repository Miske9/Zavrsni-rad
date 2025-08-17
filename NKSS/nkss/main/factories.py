import factory
import random
from datetime import date, timedelta
from django.utils.timezone import now

from main.models import Player, Match, Goal, Assist

class PlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Player

    first_name = factory.Sequence(lambda n: f"Player{n+1}")
    last_name = factory.Sequence(lambda n: f"Lastname{n+1}")
    date_of_birth = factory.LazyFunction(lambda: date(2000, 1, 1) + timedelta(days=random.randint(0, 3650)))
    position = factory.LazyFunction(lambda: random.choice(["GK", "DF", "MF", "FW"]))
    category = factory.LazyFunction(lambda: random.choice(["U9", "U11", "MP", "SP", "JUN", "SEN", "VET"]))
    goals = 0
    assists = 0
    yellow_cards = 0
    red_cards = 0
    appearances = 0

class MatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Match

    date = factory.LazyFunction(now)
    home_or_away = factory.LazyFunction(lambda: random.choice(["H", "A"]))
    opponent = factory.Sequence(lambda n: f"Opponent{n+1}")
    home_score = 0
    away_score = 0
    captain = None
    goalkeeper = None

    @factory.post_generation
    def players(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            players = extracted
        else:
            players = PlayerFactory.create_batch(20)

        starting_eleven = random.sample(players, 11)
        bench_players = [p for p in players if p not in starting_eleven]
        bench_players = random.sample(bench_players, min(7, len(bench_players)))

        self.starting_players.set(starting_eleven)
        self.bench_players.set(bench_players)

        self.captain = random.choice(starting_eleven)
        gk_candidates = [p for p in starting_eleven if p.position == "GK"]
        self.goalkeeper = random.choice(gk_candidates) if gk_candidates else random.choice(starting_eleven)

        self.save()

        self._generate_goals_and_assists(starting_eleven)

    def _generate_goals_and_assists(self, starting_players):
        num_goals = random.randint(0, 5)

        for p in starting_players:
            p.goals = 0
            p.assists = 0
            p.save()

        Goal.objects.filter(match=self).delete()
        Assist.objects.filter(match=self).delete()

        for _ in range(num_goals):
            scorer = random.choice(starting_players)
            minute = random.randint(1, 90)
            Goal.objects.create(match=self, player=scorer, minute=minute)
            scorer.goals += 1
            scorer.save()

            if random.choice([True, False]):
                assistant = random.choice(starting_players)
                while assistant == scorer and len(starting_players) > 1:
                    assistant = random.choice(starting_players)
                Assist.objects.create(match=self, player=assistant, minute=minute)
                assistant.assists += 1
                assistant.save()

        self.home_score = num_goals
        self.away_score = random.randint(0, 5)
        self.save()
