import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Member


@login_required
def export_members_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="members.csv"'
    writer = csv.writer(response)
    writer.writerow(['Username', 'First Name', 'Last Name', 'Email', 'Phone', 'Role', 'Joined', 'Monthly Dues', 'Active'])
    for m in Member.objects.all():
        writer.writerow([m.username, m.first_name, m.last_name, m.email, m.phone, m.role, m.join_date, m.monthly_dues, m.is_active_member])
    return response
