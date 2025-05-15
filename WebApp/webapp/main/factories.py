import factory
from factory.django import DjangoModelFactory
from faker import Faker
import random
from .models import Category, Player, Match, MatchPlayer, PlayerMatchStat, StaffMember, Meeting, Equipment

fake = Faker()

# CATEGORY
class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category


# PLAYER
class PlayerFactory(DjangoModelFactory):
    class Meta:
        model = Player

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    date_of_birth = factory.Faker('date_of_birth')
    position = factory.Iterator(['GK', 'DF', 'MF', 'FW'])
    category = factory.LazyFunction(lambda: random.choice(Category.objects.all()))
    goals = factory.LazyAttribute(lambda _: random.randint(0, 30))
    assists = factory.LazyAttribute(lambda _: random.randint(0, 30))


# MATCH
class MatchFactory(DjangoModelFactory):
    class Meta:
        model = Match

    date = factory.Faker('date_this_decade')
    opponent = factory.Faker('company')
    location = factory.Faker('city')
    category = factory.SubFactory(CategoryFactory)


# MATCH PLAYER
class MatchPlayerFactory(DjangoModelFactory):
    class Meta:
        model = MatchPlayer

    match = factory.SubFactory(MatchFactory)
    player = factory.SubFactory(PlayerFactory)
    is_captain = factory.Faker('boolean', chance_of_getting_true=10)


# PLAYER MATCH STAT
class PlayerMatchStatFactory(DjangoModelFactory):
    class Meta:
        model = PlayerMatchStat

    match = factory.SubFactory(MatchFactory)
    player = factory.SubFactory(PlayerFactory)
    goals = factory.LazyAttribute(lambda _: random.randint(0, 3))
    assists = factory.LazyAttribute(lambda _: random.randint(0, 3))


# STAFF MEMBER
class StaffMemberFactory(DjangoModelFactory):
    class Meta:
        model = StaffMember

    name = factory.Faker('name')
    role = factory.Iterator(['coach', 'physio', 'president', 'rep', 'other'])


# MEETING
class MeetingFactory(DjangoModelFactory):
    class Meta:
        model = Meeting

    date = factory.Faker('date_this_year')
    subject = factory.Faker('sentence', nb_words=6)
    minutes = factory.Faker('paragraph')


# EQUIPMENT
class EquipmentFactory(DjangoModelFactory):
    class Meta:
        model = Equipment

    name = factory.Faker('word')
    quantity = factory.LazyAttribute(lambda _: random.randint(1, 50))
    date_acquired = factory.Faker('date_this_year')
