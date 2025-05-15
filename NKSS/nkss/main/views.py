from django.shortcuts import render, redirect, get_object_or_404
from .models import Player, Match, MatchEvent, Goal, Assist, Card, CATEGORIES, POSITIONS
from .forms import AssistForm, CardForm, GoalForm, PlayerForm, MatchForm, MatchEventForm

def index(request):
    return render(request, 'main/index.html')
# Player Views
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
    return render(request, 'main/players/player_detail.html', {'player': player})

def player_create(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:player_list')
    else:
        form = PlayerForm()
    return render(request, 'main/players/player_form.html', {'form': form})

def player_update(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == 'POST':
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
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

# Match Views
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
    if request.method == "POST":
        form = MatchEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.match = match
            event.save()
            return redirect("main:match_detail", pk=pk)
    else:
        form = MatchEventForm()
        form.fields['player'].queryset = match.starting_players.all() | match.bench_players.all()
    return render(request, "main/matches/match_detail.html", {"match": match, "events": events, "form": form, 'goal_form': GoalForm,
    'assist_form': AssistForm,
    'card_form': CardForm,})

def match_create(request):
    if request.method == "POST":
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save()
            for player in form.cleaned_data['starting_players']:
                player.appearances += 1
                player.save()
            return redirect("main:match_list")
    else:
        form = MatchForm(request.GET or None)  # Omogućuje učitavanje kategorije iz GET-a
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

def match_delete(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.method == "POST":
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
        player.appearances += 1
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
        player.appearances += 1
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
        player.appearances += 1
        player.save()
    return redirect('main:match_detail', pk=match_id)
