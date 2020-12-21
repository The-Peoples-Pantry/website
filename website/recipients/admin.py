import collections
import uuid
from datetime import timedelta, date
from django.contrib import admin, messages
from django import forms
from django.utils.html import format_html, format_html_join
from core.models import GroceryPickupAddress
from django.urls import reverse
from .models import (
    MealRequest,
    MealRequestComment,
    GroceryRequest,
    GroceryRequestComment,
    MealDelivery,
    MealDeliveryComment,
    GroceryDelivery,
    GroceryDeliveryComment,
    Status,
    SendNotificationException,
)
from django.utils.translation import ngettext


def user_link(user):
    if user:
        display_text = user.volunteer.name or user
        url = reverse('admin:volunteers_volunteer_change', args=(user.id,))
        return format_html('<a href="%s">%s</a>' % (url, display_text))
    return user


def obj_link(obj, type, **kwargs):
    if obj:
        link_text = kwargs.get('link_text', str(obj))
        url = reverse('admin:recipients_%s_change' % type, args=(obj.id,))
        return format_html('<a href="%s">%s</a>' % (url, link_text))
    return obj


class StatusFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return Status.choices

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(delivery__status=self.value())
        return queryset


class LandlineFilter(admin.SimpleListFilter):
    title = 'Phone type'
    parameter_name = 'landline'

    def lookups(self, request, model_admin):
        return (
            (False, 'Landline'),
            (True, 'Cellphone')
        )

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(can_receive_texts=self.value())
        return queryset


class DeliveryLandlineFilter(admin.SimpleListFilter):
    title = 'Phone type'
    parameter_name = 'request_landline'

    def lookups(self, delivery, model_admin):
        return (
            (False, 'Landline'),
            (True, 'Cellphone')
        )

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(request__can_receive_texts=self.value())
        return queryset


class MealDeliveryInline(admin.TabularInline):
    model = MealDelivery


class GroceryDeliveryInline(admin.TabularInline):
    model = GroceryDelivery

# Assign the current user as author when saving comments from a model admin


class CommentInlineFormSet(forms.models.BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super(CommentInlineFormSet, self).save_new(form, commit=False)
        obj.author = self.request.user
        if commit:
            obj.save()
        return obj


# Abstract for all comment inlines
class CommentInline(admin.TabularInline):
    extra = 0
    formset = CommentInlineFormSet
    readonly_fields = (
        'author',
    )

    # Add request to the formset so that we can access the logged-in user
    def get_formset(self, request, obj=None, **kwargs):
        formset = super(CommentInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset


class MealRequestCommentInline(CommentInline):
    model = MealRequestComment


class GroceryRequestCommentInline(CommentInline):
    model = GroceryRequestComment


class MealDeliveryCommentInline(CommentInline):
    model = MealDeliveryComment


class GroceryDeliveryCommentInline(CommentInline):
    model = GroceryDeliveryComment


class MealRequestAdmin(admin.ModelAdmin):
    list_display = (
        'edit_link',
        'name',
        'phone_number',
        'landline',
        'city',
        'created_at',
        'delivery_date',
        'status',
    )
    list_filter = (
        StatusFilter,
        LandlineFilter,
        'created_at',
    )
    inlines = (
        MealDeliveryInline,
        MealRequestCommentInline,
    )
    actions = (
        'confirm',
        'copy'
    )

    def edit_link(self, request):
        return obj_link(request, 'mealrequest', link_text='Edit&nbsp;request')

    def delivery_date(self, obj):
        return obj.delivery.date
    delivery_date.admin_order_field = 'delivery__date'

    def status(self, obj):
        return obj.delivery.status
    status.admin_order_field = 'delivery__status'

    def landline(self, obj):
        return 'No' if obj.can_receive_texts else 'Yes'
    landline.short_description = "Landline"

    def confirm(self, request, queryset):
        confirmed_uuids = [delivery.request.uuid for delivery in MealDelivery.objects.filter(status=Status.DATE_CONFIRMED)]
        queryset = queryset.exclude(uuid__in=confirmed_uuids)
        updated = 0

        # Updated all deliveries associated with given request
        for meal_request in queryset:
            updated += MealDelivery.objects.filter(request=meal_request).update(status=Status.DATE_CONFIRMED)

        if updated:
            self.message_user(request, ngettext(
                "%d delivery has been confirmed with recipient",
                "%d deliveries have been confirmed with recipient",
                updated,
            ) % updated, messages.SUCCESS)
        else:
            self.message_user(
                request,
                "No updates were made",
                messages.WARNING
            )
    confirm.short_description = "Mark deliveries as confirmed with recipient"

    def create_delivery_copy(self, original_delivery, meal_request):
        new_date = original_delivery.date + timedelta(days=7)
        today = date.today()
        while new_date <= today:
            new_date = new_date + timedelta(days=7)

        delivery = MealDelivery.objects.create(
            request=meal_request,
            chef=original_delivery.chef,
            status=Status.CHEF_ASSIGNED,
            date=new_date,
            pickup_start=original_delivery.pickup_start,
            pickup_end=original_delivery.pickup_end
        )
        return delivery

    def copy(self, request, queryset):
        for meal_request in queryset:
            original_id = meal_request.id
            original_delivery = MealDelivery.objects.get(request=meal_request)
            meal_request.pk = None
            meal_request.uuid = uuid.uuid4()
            meal_request.save()
            new_delivery = self.create_delivery_copy(original_delivery, meal_request)
            self.message_user(
                request,
                "A copy of meal request %d has been created with new id %d and delivery id %d" % (
                    original_id, meal_request.id, new_delivery.id
                ), messages.SUCCESS
            )
    copy.short_description = "Create a copy of selected meal request"


class GroceryRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'phone_number',
        'city',
        'status',
        'delivery_date',
        'pickup_address',
        'created_at',
    )
    list_filter = (
        'created_at',
    )
    inlines = (
        GroceryRequestCommentInline,
        GroceryDeliveryInline
    )

    def delivery_date(self, obj):
        return obj.delivery.date
    delivery_date.admin_order_field = 'delivery__date'

    def status(self, obj):
        return obj.delivery.status
    status.admin_order_field = 'delivery__status'

    def pickup_address(self, obj):
        return obj.delivery.pickup_address
    status.admin_order_field = 'delivery__pickup_address'

    def assign_address_action(self, address):
        def assign_to_address(modeladmin, request, queryset):
            for delivery_request in queryset:
                try:
                    delivery = delivery_request.delivery
                    delivery.pickup_address = address
                    delivery.save()
                except Exception:
                    delivery = GroceryDelivery.objects.create(
                        request=delivery_request,
                        pickup_address=address
                    )

            self.message_user(request, ngettext(
                "%s has been set as the pickup address for %d delivery",
                "%s has been set as the pickup address for %d deliveries",
                len(queryset)
            ) % (str(address), len(queryset)), messages.SUCCESS)
        name = "assign_to_address_%d" % address.pk
        desc = "Set pickup location to: %s" % str(address)
        return (name, (assign_to_address, name, desc))

    def get_actions(self, request):
        actions = {}

        # Dynamically create an action for every pickup address available
        for address in GroceryPickupAddress.objects.all():
            name, action = self.assign_address_action(address)
            actions[name] = action

        actions.update(super(GroceryRequestAdmin, self).get_actions(request))
        return actions


class BaseDeliveryAdmin(admin.ModelAdmin):
    def mark_as_delivered(self, request, queryset):
        queryset = queryset.exclude(status=Status.DELIVERED)

        # Updated all deliveries associated with given request
        for delivery in queryset:
            delivery.status = Status.DELIVERED
            delivery.save()

        if queryset:
            self.message_user(request, ngettext(
                "%d delivery has been marked as delivered",
                "%d deliveries have been marked as delivered",
                len(queryset),
            ) % len(queryset), messages.SUCCESS)
        else:
            self.message_user(
                request,
                "No updates were made",
                messages.WARNING
            )
    mark_as_delivered.short_description = "Mark deliveries as delivered"

    def send_notifications(self, request, queryset, method_name):
        """
        Helper utility for invoking notification sending methods

        This is more complex than usual because we need to account for situations where we send a subset of notifications.
        Some notifications might succeed while others fail.
        If they all succeed, we simply emit the success message with a "Success" status
        If they partially fail, we emit info on both the successes and an error breakdown, with a "Warning" status
        If they all fail, we emit the error breakdown with a "Error" status

        method_name is the name of the method to invoke on each delivery instance.
        """
        successes, errors = [], []

        # Try to notify all recipients, capture any error messages that are received
        for delivery in queryset:
            try:
                send_notification_method = getattr(delivery, method_name)
                send_notification_method()
                successes.append(delivery)
            except SendNotificationException as e:
                errors.append(e.message)

        sent = len(successes)
        unsent = len(errors)
        total = sent + unsent

        prefix_message = ngettext(
            "%d delivery was selected",
            "%d deliveries were selected",
            total,
        ) % total
        success_message = ngettext(
            "%d text message was sent",
            "%d text messages were sent",
            sent,
        ) % sent

        # An unordered list of grouped errors, along with the count of how many times the error happened
        error_messages = format_html_join(
            "\n", "<p><strong>{} message(s) not sent because: {}</strong></p>",
            ((count, error_message) for (error_message, count) in collections.Counter(errors).items()),
        )

        if sent and unsent:
            self.message_user(request, format_html("<p>{}</p><p>{}</p>{}", prefix_message, success_message, error_messages), messages.WARNING)
        elif sent:
            self.message_user(request, format_html("<p>{}</p><p>{}</p>", prefix_message, success_message), messages.SUCCESS)
        elif unsent:
            self.message_user(request, format_html("<p>{}</p>{}", prefix_message, error_messages), messages.ERROR)


class MealDeliveryAdmin(BaseDeliveryAdmin):
    list_display = (
        'edit_link',
        'date',
        'request_link',
        'request_phone',
        'request_landline',
        'chef_link',
        'deliverer_link',
        'status',
        'pickup_start',
        'pickup_end',
        'dropoff_start',
        'dropoff_end',
    )

    list_filter = (
        'status',
        DeliveryLandlineFilter
    )
    actions = (
        'notify_recipients_delivery',
        'notify_chefs_reminder',
        'notify_deliverers_reminder',
        'mark_as_delivered'
    )
    inlines = (
        MealDeliveryCommentInline,
    )

    def request_phone(self, obj):
        return obj.request.phone_number
    request_phone.short_description = 'Requestor phone'

    def request_landline(self, obj):
        return 'No' if obj.request.can_receive_texts else 'Yes'
    request_landline.short_description = "Landline"

    def edit_link(self, delivery):
        return obj_link(delivery, 'mealdelivery', link_text='Edit&nbsp;delivery')

    def request_link(self, delivery):
        return obj_link(delivery.request, 'mealrequest')
    request_link.short_description = 'Request'

    def chef_link(self, delivery):
        return user_link(delivery.chef)
    chef_link.short_description = 'Chef'

    def deliverer_link(self, delivery):
        return user_link(delivery.deliverer)
    deliverer_link.short_description = 'Deliverer'

    def notify_recipients_delivery(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_delivery_notification')
    notify_recipients_delivery.short_description = "Send text message notification to recipients about delivery window"

    def notify_chefs_reminder(self, request, queryset):
        self.send_notifications(request, queryset, 'send_chef_reminder_notification')
    notify_chefs_reminder.short_description = "Send text message notification to chefs reminding them about the request"

    def notify_deliverers_reminder(self, request, queryset):
        self.send_notifications(request, queryset, 'send_deliverer_reminder_notification')
    notify_deliverers_reminder.short_description = "Send text message notification to deliverers reminding them about the request"


class GroceryDeliveryAdmin(BaseDeliveryAdmin):
    list_display = (
        'id',
        'request',
        'status',
        'pickup_address',
        'deliverer',
        'date',
    )
    list_filter = (
        'status',
    )
    actions = (
        'mark_as_delivered',
        'notify_recipients_delivery',
        'notify_deliverers_reminder'
    )
    inlines = (
        GroceryDeliveryCommentInline,
    )

    def assign_address_action(self, address):
        def assign_to_address(modeladmin, request, queryset):
            for delivery in queryset:
                delivery.pickup_address = address
                delivery.save()

            self.message_user(request, ngettext(
                "%s has been set as the pickup address for %d delivery",
                "%s has been set as the pickup address for %d deliveries",
                len(queryset)
            ) % (str(address), len(queryset)), messages.SUCCESS)
        name = "assign_to_address_%d" % address.pk
        desc = "Set pickup location to: %s" % str(address)
        return (name, (assign_to_address, name, desc))

    def get_actions(self, request):
        actions = {}

        # Dynamically create an action for every pickup address available
        for address in GroceryPickupAddress.objects.all():
            name, action = self.assign_address_action(address)
            actions[name] = action

        actions.update(super(GroceryDeliveryAdmin, self).get_actions(request))
        return actions

    def notify_recipients_delivery(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_delivery_notification')
    notify_recipients_delivery.short_description = "Send text message notification to recipients about delivery window"

    def notify_deliverers_reminder(self, request, queryset):
        self.send_notifications(request, queryset, 'send_deliverer_reminder_notification')
    notify_deliverers_reminder.short_description = "Send text message notification to deliverers reminding them about the request"


admin.site.register(GroceryRequest, GroceryRequestAdmin)
admin.site.register(MealRequest, MealRequestAdmin)
admin.site.register(MealDelivery, MealDeliveryAdmin)
admin.site.register(GroceryDelivery, GroceryDeliveryAdmin)
