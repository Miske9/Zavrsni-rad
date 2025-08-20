from datetime import timedelta, date
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum, Count, F
from .models import *
from .forms import *

def index(request):
    return render(request, 'main/index.html')

def player_list(request):
    players = Player.objects.all().order_by('category', 'last_name')

    filters = ['category', 'first_name', 'last_name', 'date_of_birth', 'position', 'status']
    filter_values = {f: request.GET.get(f) for f in filters}
    
    if filter_values['category']:
        players = players.filter(category=filter_values['category'])
    if filter_values['first_name']:
        players = players.filter(first_name__icontains=filter_values['first_name'])
    if filter_values['last_name']:
        players = players.filter(last_name__icontains=filter_values['last_name'])
    if filter_values['date_of_birth']:
        players = players.filter(date_of_birth=filter_values['date_of_birth'])
    if filter_values['position']:
        players = players.filter(position=filter_values['position'])
    if filter_values['status'] == 'active':
        players = players.filter(is_active_member=True)
    elif filter_values['status'] == 'inactive':
        players = players.filter(is_active_member=False)

    return render(request, 'main/players/player_list.html', {
        'players': players,
        'filter_values': filter_values,
        'categories': CATEGORIES,
        'positions': POSITIONS,
    })

def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    history = player.category_history.order_by('-changed_at')
    
    player_matches = Match.objects.filter(
        Q(starting_players=player) | Q(bench_players=player)
    ).distinct()
    real_appearances = player_matches.count()
    real_goals = Goal.objects.filter(player=player).count()
    real_assists = Assist.objects.filter(player=player).count()
    real_yellow_cards = Card.objects.filter(player=player, card_type='Y').count()
    real_red_cards = Card.objects.filter(player=player, card_type='R').count()
    
    return render(request, 'main/players/player_detail.html', {
        'player': player,
        'category_history': history,
        'real_appearances': real_appearances,
        'real_goals': real_goals,
        'real_assists': real_assists,
        'real_yellow_cards': real_yellow_cards,
        'real_red_cards': real_red_cards,
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
    
    def format_data(queryset):
        return [
            {
                "name": f"{item.get('first_name') or item.get('player__first_name')} {item.get('last_name') or item.get('player__last_name')}",
                "value": item.get('total') or 0,
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
        "filter_values": {"category": category, "date": date},
        'categories': CATEGORIES
    })

def match_detail(request, pk):
    match = get_object_or_404(Match, pk=pk)
    
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

    forms = {}
    for form_name, form_class in [('goal_form', GoalEventForm), ('assist_form', AssistEventForm), ('card_form', CardEventForm)]:
        forms[form_name] = form_class()
        forms[form_name].fields['player'].queryset = active_valid_players.distinct()

    return render(request, "main/matches/match_detail.html", {
        "match": match,
        "form": form,
        **forms
    })

def match_create(request):
    category = request.GET.get('category') or request.POST.get('category')
    valid_players = Player.objects.filter(category=category) if category else Player.objects.none()
    
    formset_kwargs = {'form_kwargs': {'valid_players': valid_players}}
    
    if request.method == "POST":
        form = MatchForm(request.POST)
        formsets = {
            'goals': GoalFormSet(request.POST, prefix='goals', **formset_kwargs),
            'assists': AssistFormSet(request.POST, prefix='assists', **formset_kwargs),
            'cards': CardFormSet(request.POST, prefix='cards', **formset_kwargs)
        }
        
        if form.is_valid():
            event_errors = form.validate_events(formsets['goals'], formsets['assists'], formsets['cards'])
            if not event_errors and all(fs.is_valid() for fs in formsets.values()):
                match = form.save()
                
                all_players = form.cleaned_data['starting_players'] | form.cleaned_data.get('bench_players', Player.objects.none())
                for player in all_players:
                    player.appearances += 1
                    player.save()
                
                for event_type, formset in formsets.items():
                    model_class = {'goals': Goal, 'assists': Assist, 'cards': Card}[event_type]
                    for event_form in formset:
                        if event_form.is_valid() and event_form.cleaned_data.get('player'):
                            event_data = event_form.cleaned_data.copy()
                            event_data.pop('DELETE', None)
                            event_data.pop('id', None)
                            model_class.objects.create(match=match, **event_data)
                
                return redirect("main:match_detail", pk=match.pk)
            else:
                for error in event_errors:
                    form.add_error(None, error)
    else:
        initial_data = {'category': category} if category else {}
        form = MatchForm(initial=initial_data)
        formsets = {
            'goals': GoalFormSet(prefix='goals', **formset_kwargs),
            'assists': AssistFormSet(prefix='assists', **formset_kwargs),
            'cards': CardFormSet(prefix='cards', **formset_kwargs)
        }
    
    return render(request, "main/matches/match_form.html", {
        "form": form,
        "goal_formset": formsets['goals'],
        "assist_formset": formsets['assists'],
        "card_formset": formsets['cards'],
    })

def match_update(request, pk):
    match = get_object_or_404(Match, pk=pk)
    valid_players = Player.objects.filter(category=match.category)
    formset_kwargs = {'form_kwargs': {'valid_players': valid_players}}

    if request.method == "POST":
        form = MatchForm(request.POST, instance=match)
        formsets = {
            'goals': GoalFormSet(request.POST, prefix='goals', **formset_kwargs),
            'assists': AssistFormSet(request.POST, prefix='assists', **formset_kwargs),
            'cards': CardFormSet(request.POST, prefix='cards', **formset_kwargs)
        }

        if form.is_valid() and all(fs.is_valid() for fs in formsets.values()):
            form.save()
            
            match.goals.all().delete()
            match.assists.all().delete()
            match.cards.all().delete()

            models_map = {'goals': Goal, 'assists': Assist, 'cards': Card}
            for event_type, formset in formsets.items():
                model_class = models_map[event_type]
                for event_form in formset:
                    if event_form.cleaned_data and not event_form.cleaned_data.get('DELETE'):
                        data = {k: v for k, v in event_form.cleaned_data.items() if k not in ['DELETE', 'id']}
                        model_class.objects.create(match=match, **data)

            return redirect("main:match_detail", pk=match.pk)
    else:
        form = MatchForm(instance=match)
        
        formsets = {
            'goals': GoalFormSet(
                prefix='goals',
                initial=[{'player': g.player, 'minute': g.minute} for g in match.goals.all()],
                **formset_kwargs
            ),
            'assists': AssistFormSet(
                prefix='assists',
                initial=[{'player': a.player, 'minute': a.minute} for a in match.assists.all()],
                **formset_kwargs
            ),
            'cards': CardFormSet(
                prefix='cards',
                initial=[{'player': c.player, 'minute': c.minute, 'card_type': c.card_type} for c in match.cards.all()],
                **formset_kwargs
            )
        }

    return render(request, "main/matches/match_form.html", {
        "form": form,
        "goal_formset": formsets['goals'],
        "assist_formset": formsets['assists'],
        "card_formset": formsets['cards'],
    })

def match_delete(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.method == "POST":
        for goal in match.goals.all():
            goal.player.goals = max(goal.player.goals - 1, 0)
            goal.player.save()

        for assist in match.assists.all():
            assist.player.assists = max(assist.player.assists - 1, 0)
            assist.player.save()

        for card in match.cards.all():
            if card.card_type == 'Y':
                card.player.yellow_cards = max(card.player.yellow_cards - 1, 0)
            elif card.card_type == 'R':
                card.player.red_cards = max(card.player.red_cards - 1, 0)
            card.player.save()

        for player in match.starting_players.all() | match.bench_players.all():
            player.appearances = max(player.appearances - 1, 0)
            player.save()

        match.delete()
        return redirect("main:match_list")

    return render(request, "main/matches/match_confirm_delete.html", {"match": match})

def add_event(request, match_id, event_type):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == 'POST':
        player_id = request.POST['player']
        player = get_object_or_404(Player, id=player_id)
        
        if not player.is_active_member:
            return redirect('main:match_detail', pk=match_id)
        
        minute = request.POST['minute']
        
        if event_type == 'goal':
            Goal.objects.create(match=match, player=player, minute=minute)
        elif event_type == 'assist':
            Assist.objects.create(match=match, player=player, minute=minute)
        elif event_type == 'card':
            card_type = request.POST['card_type']
            Card.objects.create(match=match, player=player, minute=minute, card_type=card_type)
    
    return redirect('main:match_detail', pk=match_id)

def add_goal(request, match_id):
    return add_event(request, match_id, 'goal')

def add_assist(request, match_id):
    return add_event(request, match_id, 'assist')

def add_card(request, match_id):
    return add_event(request, match_id, 'card')

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
    query = request.GET.get("q", "")
    meetings = Meeting.objects.all()

    if query:
        meetings = meetings.filter(
            Q(title__icontains=query) | Q(notes__icontains=query)
        )

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

    vrsta = request.GET.get("vrsta")
    if vrsta:
        equipment = equipment.filter(type=vrsta)

    context = {
        "equipment": equipment,
        "type_choices": Equipment.EQUIPMENT_TYPES,
    }
    return render(request, "main/equipment/equipment_list.html", context)

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