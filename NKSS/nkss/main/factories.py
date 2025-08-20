import factory
import random
from datetime import date, datetime, timedelta
from django.utils import timezone
from factory import fuzzy

from main.models import (
    Player, Match, Goal, Assist, Card, MatchEvent,
    StaffMember, Meeting, Equipment, PlayerCategoryHistory,
    MembershipHistory, POSITIONS, CATEGORIES, CARD_TYPES
)

CROATIAN_FIRST_NAMES = [
    "Luka", "Ivan", "Marko", "Josip", "Stjepan", "Mateo", "Filip", "Ante",
    "Tomislav", "Nikola", "Petar", "Matija", "Karlo", "Dario", "Mario",
    "Branimir", "Vedran", "Davor", "Zvonimir", "Mladen", "Igor", "Boris",
    "Goran", "Željko", "Damir", "Robert", "Antonio", "Dominik", "Leon"
]

CROATIAN_LAST_NAMES = [
    "Horvat", "Kovačević", "Babić", "Marić", "Jurić", "Novak", "Kovačić",
    "Vuković", "Knežević", "Marković", "Petrović", "Matić", "Pavlović",
    "Božić", "Nikolić", "Tomić", "Radić", "Vidović", "Savić", "Barišić",
    "Bošnjak", "Filipović", "Grgić", "Ivanović", "Lončar", "Martinović"
]

CROATIAN_OPPONENTS = [
    "NK Valpovka", "NK Belišće", "NK Bizovac", "NK Čepin", "NK Darda",
    "NK Josipovac", "NK Ladimirevci", "NK Petrijevci", "NK Semeljci",
    "NK Tenja", "NK Višnjevac", "NK Bilje", "NK Dalj", "NK Ernestinovo",
    "NK Jagodnjak", "NK Bijelo Brdo", "NK Podgorač", "NK Marijanci"
]


class PlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Player

    first_name = factory.LazyFunction(lambda: random.choice(CROATIAN_FIRST_NAMES))
    last_name = factory.LazyFunction(lambda: random.choice(CROATIAN_LAST_NAMES))
    
    @factory.lazy_attribute
    def date_of_birth(self):
        today = date.today()
        if hasattr(self, '_category'):
            category = self._category
        else:
            category = random.choice([c[0] for c in CATEGORIES])
        
        age_ranges = {
            'U9': (7, 9),
            'U11': (9, 11),
            'MP': (11, 13),
            'SP': (13, 15),
            'JUN': (15, 18),
            'SEN': (18, 35),
            'VET': (35, 50),
        }
        
        min_age, max_age = age_ranges.get(category, (18, 35))
        age = random.randint(min_age, max_age)
        birth_year = today.year - age
        
        month = random.randint(1, 12)
        if month == 2:
            day = random.randint(1, 28)
        elif month in [4, 6, 9, 11]:
            day = random.randint(1, 30)
        else:
            day = random.randint(1, 31)
        
        return date(birth_year, month, day)
    
    position = factory.LazyFunction(lambda: random.choice([p[0] for p in POSITIONS]))
    
    @factory.lazy_attribute
    def category(self):
        if hasattr(self, '_category'):
            return self._category
        return random.choice([c[0] for c in CATEGORIES])
    
    goals = 0
    assists = 0
    yellow_cards = 0
    red_cards = 0
    appearances = 0
    
    is_active_member = factory.LazyFunction(lambda: random.choice([True, True, True, False]))  # 75% active
    
    @factory.lazy_attribute
    def member_since(self):
        days_ago = random.randint(365, 365 * 5)
        return date.today() - timedelta(days=days_ago)
    
    @factory.lazy_attribute
    def member_until(self):
        if self.is_active_member:
            if random.choice([True, False]):
                return None
            else:
                days_future = random.randint(30, 365)
                return date.today() + timedelta(days=days_future)
        else:
            days_ago = random.randint(1, 180)
            return date.today() - timedelta(days=days_ago)

    @factory.post_generation
    def create_history(self, create, extracted, **kwargs):
        if not create:
            return
        
        PlayerCategoryHistory.objects.create(
            player=self,
            category=self.category,
            changed_at=timezone.now()
        )
        
        if not self.is_active_member:
            MembershipHistory.objects.create(
                player=self,
                action='DEACTIVATED',
                date_from=self.member_since,
                date_until=self.member_until or date.today(),
                notes=f"Deaktiviran {date.today().strftime('%d.%m.%Y')}"
            )

class StaffMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StaffMember

    name = factory.LazyFunction(
        lambda: f"{random.choice(CROATIAN_FIRST_NAMES)} {random.choice(CROATIAN_LAST_NAMES)}"
    )
    role = factory.LazyFunction(lambda: random.choice(['U', 'T', 'F', 'P', 'S', 'O']))
    email = factory.LazyAttribute(lambda obj: f"{obj.name.lower().replace(' ', '.')}@nkss.hr")
    phone = factory.LazyFunction(
        lambda: f"+385 {random.randint(91, 99)} {random.randint(100, 999)} {random.randint(1000, 9999)}"
    )
    active = factory.LazyFunction(lambda: random.choice([True, True, True, False]))  

class MeetingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Meeting

    date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=random.randint(1, 365))
    )
    title = factory.LazyFunction(
        lambda: random.choice([
            "Redovni mjesečni sastanak",
            "Izvanredni sastanak uprave",
            "Sastanak o pripremi sezone",
            "Planiranje treninga",
            "Financijski izvještaj",
            "Organizacija turnira",
            "Sastanak trenera",
            "Godišnja skupština",
            "Rasprava o transferima",
            "Infrastrukturni projekti"
        ])
    )
    notes = factory.Faker('text', max_nb_chars=500, locale='hr_HR')

    @factory.post_generation
    def attendees(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for attendee in extracted:
                self.attendees.add(attendee)
        else:
            staff_members = StaffMember.objects.all()
            if staff_members.exists():
                num_attendees = min(random.randint(3, 8), staff_members.count())
                attendees = random.sample(list(staff_members), num_attendees)
                for attendee in attendees:
                    self.attendees.add(attendee)

class EquipmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Equipment

    @factory.lazy_attribute
    def name(self):
        if self.type == "BALL":
            return random.choice([
                "Adidas Finale",
                "Nike Strike",
                "Puma Liga",
                "Select Brillant",
                "Mitre Delta",
                "Umbro Neo",
                "Joma Dali"
            ])
        else:  
            return random.choice([
                "Dres domaći - plavi",
                "Dres gostujući - bijeli",
                "Dres rezervni - crveni",
                "Trening dres - zeleni",
                "Golmanski dres - žuti",
                "Golmanski dres - crni",
                "Dječji komplet"
            ])

    type = factory.LazyFunction(lambda: random.choice(["BALL", "KIT"]))
    quantity = factory.LazyFunction(lambda: random.randint(1, 25))
    condition = factory.LazyFunction(
        lambda: random.choice(["Novo", "Odlično", "Dobro", "Zadovoljavajuće", "Za popravak"])
    )
    purchase_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=random.randint(30, 730))
    )

class MatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Match

    date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=random.randint(1, 180))
    )
    home_or_away = factory.LazyFunction(lambda: random.choice(["H", "A"]))
    opponent = factory.LazyFunction(lambda: random.choice(CROATIAN_OPPONENTS))
    category = factory.LazyFunction(lambda: random.choice([c[0] for c in CATEGORIES]))
    
    @factory.lazy_attribute
    def home_score(self):
        return random.randint(0, 5)
    
    @factory.lazy_attribute
    def away_score(self):
        return random.randint(0, 5)

    @factory.post_generation
    def setup_match(self, create, extracted, **kwargs):
        if not create:
            return

        players = list(Player.objects.filter(category=self.category))
        
        if len(players) < 18:
            needed = 18 - len(players)
            for _ in range(needed):
                player = PlayerFactory(category=self.category)
                player._category = self.category
                player.save()
                players.append(player)
        
        starting_eleven = random.sample(players, 11)
        self.starting_players.set(starting_eleven)
        
        remaining = [p for p in players if p not in starting_eleven]
        bench_size = min(7, len(remaining))
        bench_players = random.sample(remaining, bench_size) if remaining else []
        self.bench_players.set(bench_players)
        
        self.captain = random.choice(starting_eleven)
        
        goalkeepers = [p for p in starting_eleven if p.position == "GK"]
        self.goalkeeper = random.choice(goalkeepers) if goalkeepers else random.choice(starting_eleven)
        
        self.save()
        self.starting_players.set(starting_eleven)
        self.bench_players.set(bench_players)
        self.captain = random.choice(starting_eleven)
        self.goalkeeper = random.choice([p for p in starting_eleven if p.position == "GK"] or starting_eleven)

        all_players = starting_eleven + bench_players
        
        for _ in range(self.home_score):
            scorer = random.choice(all_players)
            minute = random.randint(1, 90)
            Goal.objects.create(match=self, player=scorer, minute=minute)
            
            if random.random() < 0.6:
                eligible_assisters = [p for p in all_players if p != scorer]
                if eligible_assisters:
                    assister = random.choice(eligible_assisters)
                    Assist.objects.create(match=self, player=assister, minute=minute)
        
        num_yellows = random.randint(0, 3)
        for _ in range(num_yellows):
            player = random.choice(all_players)
            minute = random.randint(1, 90)
            Card.objects.create(match=self, player=player, card_type='Y', minute=minute)
        
        if random.random() < 0.1:  
            player = random.choice(all_players)
            minute = random.randint(30, 90)
            Card.objects.create(match=self, player=player, card_type='R', minute=minute)

class GoalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Goal

    match = factory.SubFactory(MatchFactory)
    player = factory.SubFactory(PlayerFactory)
    minute = factory.LazyFunction(lambda: random.randint(1, 90))

class AssistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Assist

    match = factory.SubFactory(MatchFactory)
    player = factory.SubFactory(PlayerFactory)
    minute = factory.LazyFunction(lambda: random.randint(1, 90))

class CardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Card

    match = factory.SubFactory(MatchFactory)
    player = factory.SubFactory(PlayerFactory)
    card_type = factory.LazyFunction(lambda: random.choice(['Y', 'R']))
    minute = factory.LazyFunction(lambda: random.randint(1, 90))


class MatchEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MatchEvent

    match = factory.SubFactory(MatchFactory)
    player = factory.SubFactory(PlayerFactory)

def create_test_data(num_players=50, num_matches=20, num_staff=10):
    """Create a complete set of test data for the application."""
    
    print("Creating staff members...")
    staff_members = [StaffMemberFactory() for _ in range(num_staff)]
    
    print("Creating equipment...")
    equipment = [EquipmentFactory() for _ in range(15)]
    
    print("Creating players...")
    players_by_category = {}
    for category_code, category_name in CATEGORIES:
        num_in_category = max(18, num_players // len(CATEGORIES))
        players = []
        for _ in range(num_in_category):
            player = PlayerFactory()
            player._category = category_code
            player.category = category_code
            player.save()
            players.append(player)
        players_by_category[category_code] = players
    
    print("Creating matches...")
    for _ in range(num_matches):
        category = random.choice([c[0] for c in CATEGORIES])
        match = MatchFactory(category=category)
    
    print("Creating meetings...")
    meetings = [MeetingFactory() for _ in range(8)]
    
    print("Test data created successfully!")
    return {
        'players': Player.objects.all(),
        'matches': Match.objects.all(),
        'staff': staff_members,
        'equipment': equipment,
        'meetings': meetings
    }