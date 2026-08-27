from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Member(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        BOARD = 'board', 'Board Member'
        TREASURER = 'treasurer', 'Treasurer'
        MANAGER = 'manager', 'Manager'
        MEMBER = 'member', 'Member'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    phone = models.CharField(max_length=20, blank=True)
    join_date = models.DateField(default=timezone.now)
    monthly_dues = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active_member = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, help_text="Telegram user ID for bot linking")
    telegram_link_code = models.CharField(max_length=8, blank=True, null=True, help_text="Temporary code for linking Telegram")

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='member_set',
        blank=True,
        help_text='The groups this member belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='member_set',
        blank=True,
        help_text='Specific permissions for this member.',
    )

    class Meta:
        ordering = ['-is_active_member', 'first_name']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def service_years(self):
        return timezone.now().year - self.join_date.year

    @property
    def service_stars(self):
        return self.service_years // 3

    @property
    def effective_monthly_dues(self):
        if self.monthly_dues and self.monthly_dues > Decimal('0.00'):
            return self.monthly_dues
        from core.models import Setting
        return Setting.get_decimal('default_monthly_dues', 0)

    @property
    def current_dues_amount(self):
        from finances.models import Payment
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        paid = Payment.total_for_member_month(self, month_start)
        return max(self.effective_monthly_dues - paid, Decimal('0.00'))
