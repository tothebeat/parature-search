from functools import reduce
import operator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Customer, TicketDetails, TicketHistory
from re import match as re_match

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(TicketDetails, pk=pk)
    return render(request, 'parature/ticket_detail.html', {'ticket': ticket})

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if 'q' in request.GET and request.GET['q']:
        query = request.GET['q']
        # Hard-coding the ticket search to only search details, summary, and solution. Comments sometimes crashes it, not an indexed column.
        search_fields = {'ticket_details': True,
                        'ticket_summary': True,
                        'ticket_solution': True,
                        'ticket_comments': False}
        tickets = __ticket_search(query, search_fields, customer)
        return render(request, 'parature/customer_detail.html', {'customer': customer, 'tickets': tickets, 'query': query})
    else:
        tickets = customer.ticketdetails_set.all().order_by('-id')
        return render(request, 'parature/customer_detail.html', {'customer': customer, 'tickets': tickets})

@login_required
def comment_detail(request, pk):
    comment = get_object_or_404(TicketHistory, pk=pk)
    return render(request, 'parature/comment_detail.html', {'comment': comment})

@login_required
def customer_search(request):
    query_filters = []
    queries = {'Name': '', 'NetID': '', 'Email': ''}
    if request.GET.get('q_netid'):
        queries['NetID'] = request.GET.get('q_netid')
        query_filters.append(Q(netid__icontains=queries['NetID']))
    if request.GET.get('q_name'):
        queries['Name'] = request.GET.get('q_name')
        query_filters.append(Q(first_name__icontains=queries['Name']) or Q(last_name__icontains=queries['Name']))
    if request.GET.get('q_email'):
        queries['Email'] = request.GET.get('q_email')
        query_filters.append(Q(email__icontains=queries['Email']))
    if len(query_filters) > 0:
        customers = Customer.objects.filter(reduce(operator.and_, query_filters)).distinct().order_by('netid')
        query_string = ', '.join((k + ':' + v for k,v in queries.items()))
        return render(request, 'parature/customer_search.html', {'customers': customers, 'query_string': query_string, 'queries': queries})
    else:
        return render(request, 'parature/customer_search.html')

@login_required
def csr_list(request):
    csrs = sorted(TicketHistory.objects.values_list('performed_by_csr', flat=True).distinct())
    return render(request, 'parature/csr_list.html', {'csrs': csrs})

@login_required
def csr_detail(request, csr):
    Q_csr = Q(performed_by_csr__exact=csr)
    Q_csr_assigned = Q(assignedto__exact=csr)
    Q_comment = Q(action_name__exact='Post External Comment') | Q(action_name__exact='Post Internal Comment')
    Q_solution = Q(action_name__exact='Solve')

    solved_count = TicketHistory.objects.filter(Q_solution, Q_csr).values_list('ticket_id', flat=True).distinct().count()
    commented_count = TicketHistory.objects.filter(Q_comment, Q_csr).values_list('ticket_id', flat=True).distinct().count()
    touched_count = TicketHistory.objects.filter(Q_csr).values_list('ticket_id', flat=True).distinct().count()

    oldest_action = TicketHistory.objects.filter(Q_csr).filter(action_date__isnull=False).earliest('action_date')
    newest_action = TicketHistory.objects.filter(Q_csr).filter(action_date__isnull=False).latest('action_date')

    tickets_solved_list = TicketDetails.objects.filter(Q_csr_assigned).order_by('-ticketid')

    ticket_created_dates = tickets_solved_list.values_list('datecreated', flat=True)

    paginator = Paginator(tickets_solved_list, 10) # show 10 tickets per page
    page = request.GET.get('page')
    try:
        tickets_solved = paginator.page(page)
    except PageNotAnInteger:
        # if page is not an integer, deliver first page.
        tickets_solved = paginator.page(1)
    except EmptyPage:
        # if page is out of range (e.g. 9999), deliver last page of results.
        tickets_solved = paginator.page(paginator.num_pages)

    return render(request, 'parature/csr.html', {'csr': csr, 'solved_count': solved_count, 'commented_count': commented_count, 'touched_count': touched_count, 'oldest_action': oldest_action, 'newest_action': newest_action, 'tickets_solved': tickets_solved, 'ticket_created_dates': ticket_created_dates})

def __ticket_search(query, search_fields=None, customer=None):
    if search_fields:
        query_filters = []
        if search_fields.get('ticket_details'):
            query_filters.append(Q(details__icontains=query))
        if search_fields.get('ticket_summary'):
            query_filters.append(Q(summary__icontains=query))
        if search_fields.get('ticket_solution'):
            query_filters.append(Q(solution__icontains=query))
        if search_fields.get('ticket_comments'):
            query_filters.append(Q(tickethistory__comments__icontains=query))
        # Will not be looking for a specific customer unless a search is being invoked too
        if customer:
            tickets = customer.ticketdetails_set.filter(reduce(operator.or_, query_filters)).distinct().order_by('-id')
        else:
            tickets = TicketDetails.objects.filter(reduce(operator.or_, query_filters)).distinct().order_by('-id')
    else:
        tickets = []
    return tickets

@login_required
def ticket_search(request):
    if 'q' in request.GET and request.GET['q']:
        query = request.GET['q']
        search_fields = {'ticket_details': request.GET.get('search_ticket_details') == 'on',
                        'ticket_summary': request.GET.get('search_ticket_summary') == 'on',
                        'ticket_solution': request.GET.get('search_ticket_solution') == 'on',
                        'ticket_comments': request.GET.get('search_ticket_history') == 'on'}
        tickets = __ticket_search(query, search_fields)
        return render(request, 'parature/ticket_search.html', {'tickets': tickets, 'query': query})
    elif 'ticket_id' in request.GET and request.GET['ticket_id']:
        ticket_id = request.GET['ticket_id']
        # Fixing issue #34, need to remove spaces in beginning or end of ticket_id string
        ticket_id = ticket_id.strip()
        # Fixing issue #35, need to handle ticket_id entries that are not valid ticket IDs
        if not re_match(r'^(?:\d{8}|5525-\d{8})$', ticket_id):
            # invalid ticket_id
            return render(request, 'parature/ticket_search.html')
        if ticket_id.startswith('5525-'):
            ticket_id = ticket_id[len('5525-'):]
        # Redirect to the URL for the ticket with this parameter
        return redirect('ticket_detail', pk=ticket_id)
    else:
        return render(request, 'parature/ticket_search.html')

@login_required
def loaner_tickets(request):
    tickets = TicketDetails.objects.filter(Q(service__exact="Loaner Computers & Accessories")).exclude(Q(status__exact="Closed")).order_by('-id')
    return render(request, 'parature/ticket_loaners.html', {'tickets': tickets})
