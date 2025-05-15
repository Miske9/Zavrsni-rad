from django.shortcuts import render, get_object_or_404, redirect
from .models import MatchPlayer, Player, Match, PlayerMatchStat, Category, StaffMember, Equipment, Meeting
from .forms import MatchWithPlayersForm, PlayerForm, MatchForm
from django.db.models import Q

def index(request):
    return render(request, 'main/index.html')
# POPIS IGRAČA
def player_list(request):
    players = Player.objects.all()

    # dohvat GET parametara
    search = request.GET.get("search")
    category = request.GET.get("category")
    position = request.GET.get("position")
    sort = request.GET.get("sort")

    # pretraga po imenu ili prezimenu
    if search:
        players = players.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    # filtriranje po kategoriji
    if category:
        players = players.filter(category__name=category)

    # filtriranje po poziciji
    if position:
        players = players.filter(position=position)

    # sortiranje
    if sort:
        players = players.order_by(sort)

    # sve kategorije za dropdown
    categories = (
        Player.objects.values_list('category__name', flat=True)
        .distinct()
        .order_by('category__name')
    )

    context = {
        'players': players,
        'categories': categories,
    }
    return render(request, 'main/players/player_list.html', context)


# DETALJI IGRAČA
def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    stats = PlayerMatchStat.objects.filter(player=player)
    return render(request, 'main/players/player_detail.html', {'player': player, 'stats': stats})

# DODAVANJE IGRAČA
def player_create(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:player_list')
    else:
        form = PlayerForm()
    return render(request, 'main/players/player_form.html', {'form': form})

# UREĐIVANJE IGRAČA
def player_edit(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == 'POST':
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            return redirect('main:player_list')
    else:
        form = PlayerForm(instance=player)
    return render(request, 'main/players/player_form.html', {'form': form})

# BRISANJE IGRAČA
def player_delete(request, pk):
    player = get_object_or_404(Player, pk=pk)
    player.delete()
    return redirect('main:player_list')


# POPIS UTAKMICA
def match_list(request):
    matches = Match.objects.all()
    return render(request, 'main/matches/match_list.html', {'matches': matches})

# DODAVANJE UTAKMICE
def match_add(request):
    category_id = request.GET.get('category')
    category = Category.objects.get(id=category_id) if category_id else None

    if request.method == 'POST':
        form = MatchWithPlayersForm(request.POST, category=category)
        if form.is_valid():
            match = form.save()
            # Spremi startere i klupu
            starters = form.cleaned_data['starters']
            substitutes = form.cleaned_data['substitutes']
            captain = form.cleaned_data['captain']

            for player in starters:
                MatchPlayer.objects.create(match=match, player=player, is_captain=(player == captain))

            for player in substitutes:
                if player not in starters:
                    MatchPlayer.objects.create(match=match, player=player, is_captain=(player == captain))

            return redirect('main:match_list')
    else:
        form = MatchWithPlayersForm(category=category)

    categories = Category.objects.all()
    return render(request, 'main/matches/match_form.html', {
        'form': form,
        'categories': categories,
        'selected_category': category_id
    })


def match_add_stats(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    players = match.players.all()

    if request.method == 'POST':
        scorers = request.POST.getlist('scorers')
        assistants = request.POST.getlist('assistants')

        # Define or import the add_match_stats function
        def add_match_stats(match, scorers, assistants):
            for scorer in scorers:
                PlayerMatchStat.objects.create(match=match, player_id=scorer, goals=1)

            for assistant in assistants:
                # Ako igrač već ima zapis za ovu utakmicu, samo povećaj asistencije
                stat, created = PlayerMatchStat.objects.get_or_create(match=match, player_id=assistant)
                if not created:
                    stat.assists += 1
                    stat.save()
                else:
                    stat.assists = 1
                    stat.save()


        add_match_stats(match, scorers, assistants)

        return redirect('main:match_detail', pk=match.id)

    return render(request, 'main/matches/match_add_stats.html', {
        'match': match,
        'players': players,
    })


# DETALJI, UREĐIVANJE, BRISANJE UTAKMICA (slični obrasci kao za igrače)
def match_detail(request, pk):
    match = get_object_or_404(Match, pk=pk)
    return render(request, 'main/matches/match_detail.html', {'match': match})

def match_edit(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            return redirect('main:match_list')
    else:
        form = MatchForm(instance=match)
    return render(request, 'main/matches/match_form.html', {'form': form})

def match_delete(request, pk):
    match = get_object_or_404(Match, pk=pk)
    match.delete()
    return redirect('main:match_list')

# ČLANOVI UPRAVE
def staff_list(request):
    staff = StaffMember.objects.all()
    return render(request, 'main/staff_list.html', {'staff': staff})

# OPREMA
def equipment_list(request):
    equipment = Equipment.objects.all()
    return render(request, 'main/equipment_list.html', {'equipment': equipment})

# SASTANCI
def meeting_list(request):
    meetings = Meeting.objects.all()
    return render(request, 'main/meeting_list.html', {'meetings': meetings})
