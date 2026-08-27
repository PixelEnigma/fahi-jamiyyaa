from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum


class Sponsor(models.Model):
    class Tier(models.TextChoices):
        PLATINUM = 'platinum', 'Platinum'
        GOLD = 'gold', 'Gold'
        SILVER = 'silver', 'Silver'
        BRONZE = 'bronze', 'Bronze'
        SUPPORTER = 'supporter', 'Supporter'

    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.SUPPORTER)
    logo = models.ImageField(upload_to='sponsors/', blank=True, null=True)
    total_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    event = models.ForeignKey(
        'events.Event', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sponsors'
    )

    class Meta:
        ordering = ['-total_contribution', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_tier_display()})"


class Contribution(models.Model):
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='contributions')
    event = models.ForeignKey(
        'events.Event', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sponsorships'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.sponsor} - {self.amount} ({self.date})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_sponsor_total()

    def delete(self, *args, **kwargs):
        sponsor_id = self.sponsor_id
        super().delete(*args, **kwargs)
        total = Contribution.objects.filter(sponsor_id=sponsor_id).aggregate(t=Sum('amount'))['t'] or 0
        Sponsor.objects.filter(pk=sponsor_id).update(total_contribution=total)

    def _update_sponsor_total(self):
        total = Contribution.objects.filter(sponsor=self.sponsor).aggregate(t=Sum('amount'))['t'] or 0
        Sponsor.objects.filter(pk=self.sponsor_id).update(total_contribution=total)
