from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Customer, TicketDetails, TicketHistory

def home(request):
    return render(request, 'parature/home.html')

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(TicketDetails, pk=pk)
    return render(request, 'parature/ticket_detail.html', {'ticket': ticket})

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    tickets = customer.ticketdetails_set.all()
    return render(request, 'parature/customer_detail.html', {'customer': customer, 'tickets': tickets})

@login_required
def comment_detail(request, pk):
    comment = get_object_or_404(TicketHistory, pk=pk)
    return render(request, 'parature/comment_detail.html', {'comment': comment})

@login_required
def ticket_search(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
        tickets = TicketDetails.objects.filter(details__icontains=q).order_by('id')
        return render(request, 'parature/ticket_list_with_search.html', {'tickets': tickets, 'query': q})
    else:
        return render(request, 'parature/ticket_list_with_search.html')

@login_required
def customer_search(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
        customers = Customer.objects.filter(netid__icontains=q).order_by('netid')
        return render(request, 'parature/customer_list_and_search.html', {'customers': customers, 'query': q})
    else:
        return render(request, 'parature/customer_list_and_search.html')

@login_required
def comment_search_by_csr(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
        comments = TicketHistory.objects.filter(performed_by_csr__icontains=q).filter(action_name='Post Internal Comment').order_by('id')
        return render(request, 'parature/comments_by_csr.html', {'comments': comments, 'query': q})
    else:
        return render(request, 'parature/comments_by_csr.html')
