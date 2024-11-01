from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SubscriptionPlan, SubscriptionFeature

@receiver(post_save, sender=SubscriptionFeature)
def add_new_features_to_free_plan(sender, instance, created, **kwargs):
    """
    Triggered after saving a SubscriptionFeature instance.
    Adds any new feature to the 'Test Plan' if it doesn't already have it.
    """
    if created:
        free_plan = SubscriptionPlan.objects.filter(name="Test Plan").first()

        if free_plan:
            all_features = SubscriptionFeature.objects.all()
            free_plan_features = free_plan.features.all()
            new_features = all_features.difference(free_plan_features)
            if new_features:
                free_plan.features.add(*new_features)
                free_plan.save()