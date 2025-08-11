from datetime import timedelta, date
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum, Avg, Count, F
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
    status = request.GET.get('status')  

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
    if status == 'active':
        players = players.filter(is_active_member=True)
    elif status == 'inactive':
        players = players.filter(is_active_member=False)

    return render(request, 'main/players/player_list.html', {
        'players': players,
        'filter_values': {
            'category': category,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': dob,
            'position': position,
            'status': status,
        },
        'categories': CATEGORIES,
        'positions': POSITIONS,
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
            if player.category:
                PlayerCategoryHistory.objects.create(player=player, category=player.category)
            return redirect('main:player_list')
    else:
        form = PlayerForm()
    return render(request, 'main/players/player_form.html', {'form': form})

def player_update(request, pk):
    player = get_object_or_404(Player, pk=pk)
    old_category = player.category  

    if request.method == 'POST':
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
            new_category = form.cleaned_data['category']
            if old_category != new_category and new_category:
                PlayerCategoryHistory.objects.create(player=player, category=new_category)
            
            if not form.cleaned_data['is_active_member'] and not form.cleaned_data.get('member_until'):
                player.member_until = date.today()
            
            form.save()
            return redirect('main:player_detail', pk=pk)
    else:
        form = PlayerForm(instance=player)
        
        if request.GET.get('deactivate') == 'true':
            form.initial['is_active_member'] = False
            form.initial['member_until'] = date.today()
        elif request.GET.get('activate') == 'true':
            form.initial['is_active_member'] = True
            form.initial['member_until'] = None  
            
    return render(request, 'main/players/player_form.html', {'form': form})

def player_delete(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == 'POST':
        player.delete()
        return redirect('main:player_list')
    return render(request, 'main/players/player_confirm_delete.html', {'player': player})

def stats_dashboard(request):
    selected_category = request.GET.get('category', '') 
    selected_period = request.GET.get('period', 'all')  
    today = date.today()
    date_filter = None
    
    if selected_period == 'month':
        date_filter = today - timedelta(days=30)
        period_label = "Zadnjih 30 dana"
    elif selected_period == 'year': 
        date_filter = today - timedelta(days=365)
        period_label = "Zadnjih godinu dana"
    else:
        period_label = "Od uvijek"
        
    matches = Match.objects.all()
    if date_filter:
        matches = matches.filter(date__gte=date_filter)
    if selected_category:
        matches = matches.filter(category=selected_category)

    players = Player.objects.all()
    if selected_category:
        players = players.filter(category=selected_category)
    
    goals_queryset = (
        Goal.objects.filter(match__in=matches)
        .values('player__id', 'player__first_name', 'player__last_name', 'player__category')
        .annotate(total=Count('id'))
        .order_by('-total')[:15]  
    )
    
    assists_queryset = (
        Assist.objects.filter(match__in=matches)
        .values('player__id', 'player__first_name', 'player__last_name', 'player__category')
        .annotate(total=Count('id'))
        .order_by('-total')[:15]
    )
    
    appearances_queryset = []
    for player in players:
        player_matches = matches.filter(
            Q(starting_players=player) | Q(bench_players=player)
        ).distinct()
        
        if player_matches.exists():
            appearances_queryset.append({
                'player__id': player.id,
                'player__first_name': player.first_name, 
                'player__last_name': player.last_name,
                'player__category': player.category,
                'total': player_matches.count()
            })
    
    appearances_queryset = sorted(appearances_queryset, key=lambda x: x['total'], reverse=True)[:15]
    
    yellow_cards_queryset = (
        Card.objects.filter(match__in=matches, card_type='Y')
        .values('player__id', 'player__first_name', 'player__last_name', 'player__category')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )
    
    red_cards_queryset = (
        Card.objects.filter(match__in=matches, card_type='R') 
        .values('player__id', 'player__first_name', 'player__last_name', 'player__category')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )
    
    total_matches = matches.count()
    total_goals_scored = Goal.objects.filter(match__in=matches).count()
    total_goals_conceded = matches.aggregate(Sum('away_score'))['away_score__sum'] or 0
    
    wins = matches.filter(home_score__gt=F('away_score')).count() if matches else 0
    draws = matches.filter(home_score=F('away_score')).count() if matches else 0
    losses = matches.filter(home_score__lt=F('away_score')).count() if matches else 0
    
    avg_goals_scored = round(total_goals_scored / total_matches, 2) if total_matches > 0 else 0
    avg_goals_conceded = round(total_goals_conceded / total_matches, 2) if total_matches > 0 else 0
    
    category_stats = []
    if not selected_category:
        for cat_code, cat_name in CATEGORIES:
            cat_matches = matches.filter(category=cat_code)
            if cat_matches.exists():
                cat_goals = Goal.objects.filter(match__in=cat_matches).count()
                category_stats.append({
                    'category': cat_name,
                    'matches': cat_matches.count(),
                    'goals': cat_goals,
                    'wins': cat_matches.filter(home_score__gt=F('away_score')).count(),
                })
    
    def format_data(queryset, value_field='total'):
        return [
            {
                "name": f"{item.get('first_name') or item.get('player__first_name')} {item.get('last_name') or item.get('player__last_name')}",
                "value": item.get(value_field) or 0,
                "category": item.get('category') or item.get('player__category', '')
            } for item in queryset
        ]
    
    context = {
        'categories': CATEGORIES,
        'selected_category': selected_category,
        'selected_period': selected_period,
        'period_label': period_label,
        'goals': format_data(goals_queryset),
        'assists': format_data(assists_queryset),
        'appearances': format_data(appearances_queryset),
        'yellow_cards': format_data(yellow_cards_queryset),
        'red_cards': format_data(red_cards_queryset),
        
        'club_stats': {
            'total_matches': total_matches,
            'wins': wins,
            'draws': draws, 
            'losses': losses,
            'win_percentage': round((wins / total_matches * 100), 1) if total_matches > 0 else 0,
            'total_goals_scored': total_goals_scored,
            'total_goals_conceded': total_goals_conceded,
            'goal_difference': total_goals_scored - total_goals_conceded,
            'avg_goals_scored': avg_goals_scored,
            'avg_goals_conceded': avg_goals_conceded,
        },
        'category_stats': category_stats,
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
    active_valid_players = valid_players.filter(is_active_member=True).exclude(member_until__lt=date.today())

    if request.method == "POST":
        form = MatchEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.match = match
            event.save()
            return redirect("main:match_detail", pk=pk)
    else:
        form = MatchEventForm()

    goal_form = GoalEventForm()
    goal_form.fields['player'].queryset = active_valid_players.distinct()

    assist_form = AssistEventForm()
    assist_form.fields['player'].queryset = active_valid_players.distinct()

    card_form = CardEventForm()
    card_form.fields['player'].queryset = active_valid_players.distinct()

    return render(request, "main/matches/match_detail.html", {
        "match": match,
        "events": events,
        "form": form,
        "goal_form": goal_form,
        "assist_form": assist_form,
        "card_form": card_form,
    })

def match_create(request):
    category = request.GET.get('category') or request.POST.get('category')
    valid_players = Player.objects.none()
    if category:
        valid_players = Player.objects.filter(category=category)
    
    if request.method == "POST":
        form = MatchForm(request.POST)
        goal_formset = GoalFormSet(
            request.POST, 
            prefix='goals',
            form_kwargs={'valid_players': valid_players}
        )
        assist_formset = AssistFormSet(
            request.POST, 
            prefix='assists',
            form_kwargs={'valid_players': valid_players}
        )
        card_formset = CardFormSet(
            request.POST, 
            prefix='cards',
            form_kwargs={'valid_players': valid_players}
        )
        if form.is_valid():
            event_errors = form.validate_events(goal_formset, assist_formset, card_formset)
            if not event_errors and goal_formset.is_valid() and assist_formset.is_valid() and card_formset.is_valid():
                match = form.save()
               
                for player in form.cleaned_data['starting_players']:
                    player.appearances += 1
                    player.save()
                for player in form.cleaned_data.get('bench_players', []):
                    player.appearances += 1
                    player.save()
               
                for goal_form in goal_formset:
                    if goal_form.is_valid() and goal_form.cleaned_data.get('player'):
                        goal_data = goal_form.cleaned_data
                        Goal.objects.create(
                            match=match,
                            player=goal_data['player'],
                            minute=goal_data['minute']
                        )
                        goal_data['player'].goals += 1
                        goal_data['player'].save()
                        
                for assist_form in assist_formset:
                    if assist_form.is_valid() and assist_form.cleaned_data.get('player'):
                        assist_data = assist_form.cleaned_data
                        Assist.objects.create(
                            match=match,
                            player=assist_data['player'],
                            minute=assist_data['minute']
                        )
                        assist_data['player'].assists += 1
                        assist_data['player'].save()
                
                for card_form in card_formset:
                    if card_form.is_valid() and card_form.cleaned_data.get('player'):
                        card_data = card_form.cleaned_data
                        Card.objects.create(
                            match=match,
                            player=card_data['player'],
                            card_type=card_data['card_type'],
                            minute=card_data['minute']
                        )
                        if card_data['card_type'] == 'Y':
                            card_data['player'].yellow_cards += 1
                        elif card_data['card_type'] == 'R':
                            card_data['player'].red_cards += 1
                        card_data['player'].save()
                return redirect("main:match_detail", pk=match.pk)
            else:
                for error in event_errors:
                    form.add_error(None, error)
    else:
        initial_data = {}
        if category:
            initial_data['category'] = category
        form = MatchForm(initial=initial_data)
        goal_formset = GoalFormSet(
            prefix='goals',
            form_kwargs={'valid_players': valid_players}
        )
        assist_formset = AssistFormSet(
            prefix='assists',
            form_kwargs={'valid_players': valid_players}
        )
        card_formset = CardFormSet(
            prefix='cards',
            form_kwargs={'valid_players': valid_players}
        )
    
    return render(request, "main/matches/match_form.html", {
        "form": form,
        "goal_formset": goal_formset,
        "assist_formset": assist_formset,
        "card_formset": card_formset,
    })

def match_update(request, pk):
    match = get_object_or_404(Match, pk=pk)
    valid_players = Player.objects.filter(category=match.category)

    if request.method == "POST":
        form = MatchForm(request.POST, instance=match)
        goal_formset = GoalFormSet(request.POST, prefix='goals', form_kwargs={'valid_players': valid_players})
        assist_formset = AssistFormSet(request.POST, prefix='assists', form_kwargs={'valid_players': valid_players})
        card_formset = CardFormSet(request.POST, prefix='cards', form_kwargs={'valid_players': valid_players})

        if form.is_valid() and goal_formset.is_valid() and assist_formset.is_valid() and card_formset.is_valid():
            form.save()
            match.goals.all().delete()
            match.assists.all().delete()
            match.cards.all().delete()

            for gf in goal_formset:
                if gf.cleaned_data and not gf.cleaned_data.get('DELETE'):
                    data = {k: v for k, v in gf.cleaned_data.items() if k not in ['DELETE', 'id']}
                    Goal.objects.create(match=match, **data)

            for af in assist_formset:
                if af.cleaned_data and not af.cleaned_data.get('DELETE'):
                    data = {k: v for k, v in af.cleaned_data.items() if k not in ['DELETE', 'id']}
                    Assist.objects.create(match=match, **data)

            for cf in card_formset:
                if cf.cleaned_data and not cf.cleaned_data.get('DELETE'):
                    data = {k: v for k, v in cf.cleaned_data.items() if k not in ['DELETE', 'id']}
                    Card.objects.create(match=match, **data)

            return redirect("main:match_detail", pk=match.pk)
    else:
        form = MatchForm(instance=match)
        goal_formset = GoalFormSet(
            prefix='goals',
            initial=[
                {'player': g.player, 'minute': g.minute}
                for g in match.goals.all()
            ],
            form_kwargs={'valid_players': valid_players}
        )

        assist_formset = AssistFormSet(
            prefix='assists',
            initial=[
                {'player': a.player, 'minute': a.minute}
                for a in match.assists.all()
            ],
            form_kwargs={'valid_players': valid_players}
        )

        card_formset = CardFormSet(
            prefix='cards',
            initial=[
                {'player': c.player, 'minute': c.minute, 'card_type': c.card_type}
                for c in match.cards.all()
            ],
            form_kwargs={'valid_players': valid_players}
        )


        return render(request, "main/matches/match_form.html", {
            "form": form,
            "goal_formset": goal_formset,
            "assist_formset": assist_formset,
            "card_formset": card_formset,
        })


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
        player = get_object_or_404(Player, id=player_id)
        
       
        if not player.is_active_member:
            return redirect('main:match_detail', pk=match_id)
        
        minute = request.POST['minute']
        Goal.objects.create(match=match, player=player, minute=minute)
        player.goals += 1
        player.save()
        return redirect('main:match_detail', pk=match_id)

def add_assist(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == 'POST':
        player_id = request.POST['player']
        player = get_object_or_404(Player, id=player_id)
        
       
        if not player.is_active_member:
            return redirect('main:match_detail', pk=match_id)
        
        minute = request.POST['minute']
        Assist.objects.create(match=match, player=player, minute=minute)
        player.assists += 1
        player.save()
    return redirect('main:match_detail', pk=match_id)

def add_card(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == 'POST':
        player_id = request.POST['player']
        player = get_object_or_404(Player, id=player_id)
        
       
        if not player.is_active_member:
            return redirect('main:match_detail', pk=match_id)
        
        minute = request.POST['minute']
        card_type = request.POST['card_type']
        Card.objects.create(match=match, player=player, minute=minute, card_type=card_type)
        if card_type == 'Y':
            player.yellow_cards += 1
        elif card_type == 'R':
            player.red_cards += 1
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