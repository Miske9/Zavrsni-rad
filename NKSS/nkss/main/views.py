from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import *
from .forms import *

def index(request):
    return render(request, 'main/index.html')
def player_list(request):
    players = Player.objects.all().order_by('category', 'last_name')

    category = request.GET.get('category')
    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    dob = request.GET.get('date_of_birth')
    position = request.GET.get('position')

    if category:
        players = players.filter(category=category)
    if first_name:
        players = players.filter(first_name__icontains=first_name)
    if last_name:
        players = players.filter(last_name__icontains=last_name)
    if dob:
        players = players.filter(date_of_birth=dob)
    if position:
        players = players.filter(position=position)

    return render(request, 'main/players/player_list.html', {
        'players': players,
        'filter_values': {
            'category': category,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': dob,
            'position': position,
        },
        'categories': CATEGORIES,
        'positions': POSITIONS
    })

def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    history = player.category_history.order_by('-changed_at')
    return render(request, 'main/players/player_detail.html', {
        'player': player,
        'category_history': history
    })

def player_create(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            player = form.save()
            # Spremi početnu kategoriju u povijest
            if player.category:
                PlayerCategoryHistory.objects.create(player=player, category=player.category)
            return redirect('main:player_list')
    else:
        form = PlayerForm()
    return render(request, 'main/players/player_form.html', {'form': form})

def player_update(request, pk):
    player = get_object_or_404(Player, pk=pk)
    old_category = player.category  # Spremi staru kategoriju

    if request.method == 'POST':
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
            new_category = form.cleaned_data['category']
            if old_category != new_category and new_category:
                PlayerCategoryHistory.objects.create(player=player, category=new_category)
            form.save()
            return redirect('main:player_detail', pk=pk)
    else:
        form = PlayerForm(instance=player)
    return render(request, 'main/players/player_form.html', {'form': form})

def player_delete(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == 'POST':
        player.delete()
        return redirect('main:player_list')
    return render(request, 'main/players/player_confirm_delete.html', {'player': player})

def stats_dashboard(request):
    selected_category = request.GET.get('category', '')  # "" za sve

    players = Player.objects.all()
    if selected_category:
        players = players.filter(category=selected_category)

    goals = (
        Goal.objects.filter(player__in=players)
        .values('player__id', 'player__first_name', 'player__last_name')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    assists = (
        Assist.objects.filter(player__in=players)
        .values('player__id', 'player__first_name', 'player__last_name')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    appearances = (
        players.order_by('-appearances')
        .values('id', 'first_name', 'last_name', 'appearances')[:10]
    )

    def format_data(queryset, value_field='total'):
        return [
            {
                "name": f"{item.get('first_name') or item.get('player__first_name')} {item.get('last_name') or item.get('player__last_name')}",
                "value": item.get(value_field) or 0
            } for item in queryset
        ]

    context = {
        'categories': CATEGORIES,
        'selected_category': selected_category,
        'goals': format_data(goals),
        'assists': format_data(assists),
        'appearances': format_data(appearances, value_field='appearances'),
    }

    return render(request, 'main/stats_dashboard.html', context)

def match_list(request):
    matches = Match.objects.all().order_by('-date')

    category = request.GET.get('category')
    date = request.GET.get('date')

    if category:
        matches = matches.filter(category=category)
    if date:
        matches = matches.filter(date=date)

    return render(request, "main/matches/match_list.html", {
        "matches": matches,
        "filter_values": {
            "category": category,
            "date": date
        },
        'categories': CATEGORIES 
    })

def match_detail(request, pk):
    match = get_object_or_404(Match, pk=pk)
    events = MatchEvent.objects.filter(match=match).order_by('minute')

    valid_players = match.starting_players.all() | match.bench_players.all()

    if request.method == "POST":
        form = MatchEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.match = match
            event.save()
            return redirect("main:match_detail", pk=pk)
    else:
        form = MatchEventForm()

    # Ovdje ograničavamo forme samo na relevantne igrače
    goal_form = GoalForm()
    goal_form.fields['player'].queryset = valid_players.distinct()

    assist_form = AssistForm()
    assist_form.fields['player'].queryset = valid_players.distinct()

    card_form = CardForm()
    card_form.fields['player'].queryset = valid_players.distinct()

    return render(request, "main/matches/match_detail.html", {
        "match": match,
        "events": events,
        "form": form,
        "goal_form": goal_form,
        "assist_form": assist_form,
        "card_form": card_form,
    })


def match_create(request):
    if request.method == "POST":
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save()
            for player in form.cleaned_data['starting_players']:
                player.appearances += 1
                player.save()
            for player in form.cleaned_data['bench_players']:
                player.appearances += 1
                player.save()
            return redirect("main:match_list")
    else:
        form = MatchForm(request.GET or None)  
    return render(request, "main/matches/match_form.html", {"form": form})


def match_update(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.method == "POST":
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            return redirect("main:match_detail", pk=pk)
    else:
        form = MatchForm(instance=match)
    return render(request, "main/matches/match_form.html", {"form": form})


from django.shortcuts import get_object_or_404, redirect, render

def match_delete(request, pk):
    match = get_object_or_404(Match, pk=pk)

    if request.method == "POST":
        for goal in match.goals.all():
            player = goal.player
            player.goals = max(player.goals - 1, 0)
            player.save()

        for assist in match.assists.all():
            player = assist.player
            player.assists = max(player.assists - 1, 0)
            player.save()

        for card in match.cards.all():
            player = card.player
            if card.card_type == 'Y':
                player.yellow_cards = max(player.yellow_cards - 1, 0)
            elif card.card_type == 'R':
                player.red_cards = max(player.red_cards - 1, 0)
            player.save()

        for player in match.starting_players.all() | match.bench_players.all():
            player.appearances = max(player.appearances - 1, 0)
            player.save()

        match.goals.all().delete()
        match.assists.all().delete()
        match.cards.all().delete()

        match.delete()
        return redirect("main:match_list")

    return render(request, "main/matches/match_confirm_delete.html", {"match": match})



def add_goal(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == 'POST':
        player_id = request.POST['player']
        minute = request.POST['minute']
        Goal.objects.create(match=match, player_id=player_id, minute=minute)
        player = Player.objects.get(id=player_id)
        player.goals += 1
        player.appearances += 0
        player.save()
        return redirect('main:match_detail', pk=match_id)

def add_assist(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == 'POST':
        player_id = request.POST['player']
        minute = request.POST['minute']
        Assist.objects.create(match=match, player_id=player_id, minute=minute)
        player = Player.objects.get(id=player_id)
        player.assists += 1
        player.appearances += 0
        player.save()
    return redirect('main:match_detail', pk=match_id)

def add_card(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == 'POST':
        player_id = request.POST['player']
        minute = request.POST['minute']
        card_type = request.POST['card_type']
        Card.objects.create(match=match, player_id=player_id, minute=minute, card_type=card_type)
        player = Player.objects.get(id=player_id)
        if card_type == 'Y':
            player.yellow_cards += 1
        elif card_type == 'R':
            player.red_cards += 1
        player.appearances += 0
        player.save()
    return redirect('main:match_detail', pk=match_id)


def staffmember_list(request):
    staffmembers = StaffMember.objects.all()
    return render(request, 'main/staff/staffmember_list.html', {'staffmembers': staffmembers})

def staffmember_detail(request, pk):
    staffmember = get_object_or_404(StaffMember, pk=pk)
    return render(request, 'main/staff/staffmember_detail.html', {'staffmember': staffmember})

def staffmember_create(request):
    if request.method == "POST":
        form = StaffMemberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:staffmember-list')
    else:
        form = StaffMemberForm()
    return render(request, 'main/staff/staffmember_form.html', {'form': form})

def staffmember_update(request, pk):
    staffmember = get_object_or_404(StaffMember, pk=pk)
    if request.method == "POST":
        form = StaffMemberForm(request.POST, instance=staffmember)
        if form.is_valid():
            form.save()
            return redirect('main:staffmember-list')
    else:
        form = StaffMemberForm(instance=staffmember)
    return render(request, 'main/staff/staffmember_form.html', {'form': form})

def staffmember_delete(request, pk):
    staffmember = get_object_or_404(StaffMember, pk=pk)
    if request.method == "POST":
        staffmember.delete()
        return redirect('main:staffmember-list')
    return render(request, 'main/staff/staffmember_confirm_delete.html', {'staffmember': staffmember})

def meeting_list(request):
    meetings = Meeting.objects.all()
    return render(request, 'main/meeting/meeting_list.html', {'meetings': meetings})

def meeting_detail(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    return render(request, 'main/meeting/meeting_detail.html', {'meeting': meeting})

def meeting_create(request):
    if request.method == "POST":
        form = MeetingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:meeting-list')
    else:
        form = MeetingForm()
    return render(request, 'main/meeting/meeting_form.html', {'form': form})

def meeting_update(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if request.method == "POST":
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            return redirect('main:meeting-list')
    else:
        form = MeetingForm(instance=meeting)
    return render(request, 'main/meeting/meeting_form.html', {'form': form})

def meeting_delete(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if request.method == "POST":
        meeting.delete()
        return redirect('main:meeting-list')
    return render(request, 'main/meeting/meeting_confirm_delete.html', {'meeting': meeting})

def equipment_list(request):
    equipment = Equipment.objects.all()
    return render(request, 'main/equipment/equipment_list.html', {'equipment': equipment})

def equipment_detail(request, pk):
    equipment_item = get_object_or_404(Equipment, pk=pk)
    return render(request, 'main/equipment/equipment_detail.html', {'equipment': equipment_item})

def equipment_create(request):
    if request.method == "POST":
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:equipment-list')
    else:
        form = EquipmentForm()
    return render(request, 'main/equipment/equipment_form.html', {'form': form})

def equipment_update(request, pk):
    equipment_item = get_object_or_404(Equipment, pk=pk)
    if request.method == "POST":
        form = EquipmentForm(request.POST, instance=equipment_item)
        if form.is_valid():
            form.save()
            return redirect('main:equipment-list')
    else:
        form = EquipmentForm(instance=equipment_item)
    return render(request, 'main/equipment/equipment_form.html', {'form': form})

def equipment_delete(request, pk):
    equipment_item = get_object_or_404(Equipment, pk=pk)
    if request.method == "POST":
        equipment_item.delete()
        return redirect('main:equipment-list')
    return render(request, 'main/equipment/equipment_confirm_delete.html', {'equipment_item': equipment_item})