import collections
from django.contrib import admin, messages
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html, format_html_join
from core.admin import user_link, obj_link

from .models import (
    MealRequest,
    MealRequestComment,
    MealDelivery,
    MealDeliveryComment,
    Status,
    SendNotificationException,
    GroceryRequest,
    GroceryRequestComment,
)
from django.utils.translation import ngettext


def short_time(time_obj):
    try:
        return time_obj.strftime('%-I %p')
    except ValueError:
        return time_obj.strftime('%I %p')
    except AttributeError:
        return 'None'


class CompletedFilter(admin.SimpleListFilter):
    title = 'Completed'
    parameter_name = 'completed'

    def queryset_kwargs(self):
        raise NotImplementedError

    def lookups(self, request, model_admin):
        return (
            ('Hide Completed', 'Hide Completed'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Hide Completed':
            queryset = queryset.exclude(**self.queryset_kwargs())
        return queryset


class MealRequestCompletedFilter(CompletedFilter):
    def queryset_kwargs(self):
        return {'delivery__status': Status.DELIVERED}


class MealDeliveryCompletedFilter(CompletedFilter):
    def queryset_kwargs(self):
        return {'status': Status.DELIVERED}


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


class MealDeliveryCommentInline(CommentInline):
    model = MealDeliveryComment


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
        'completed',
    )
    list_filter = (
        MealRequestCompletedFilter,
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
    search_fields = ('name', 'email', 'phone_number')
    list_select_related = (
        'delivery',
    )

    def edit_link(self, request):
        return 'Edit request %d' % request.id
    edit_link.short_description = 'Edit link'

    def delivery_date(self, obj):
        return obj.delivery.date
    delivery_date.admin_order_field = 'delivery__date'

    def status(self, obj):
        return obj.delivery.status
    status.admin_order_field = 'delivery__status'

    def completed(self, obj):
        try:
            return obj.delivery.status == Status.DELIVERED
        except ObjectDoesNotExist:
            return False
    completed.admin_order_field = 'delivery__status'
    completed.boolean = True

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

    def copy(self, request, queryset):
        for meal_request in queryset:
            new_meal_request = meal_request.copy()
            self.message_user(
                request,
                f"A copy of meal request {meal_request.id} has been created with new id {new_meal_request.id}",
                messages.SUCCESS,
            )
    copy.short_description = "Create a copy of selected meal request"


class MealDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        'edit_link',
        'request_link',
        'request_phone',
        'request_landline',
        'chef_link',
        'deliverer_link',
        'status',
        'date',
        'pickup_range',
        'dropoff_range',
        'completed',
    )

    list_filter = (
        MealDeliveryCompletedFilter,
        'status',
        DeliveryLandlineFilter
    )
    actions = (
        'notify_recipients_delivery',
        'notify_recipients_reminder',
        'notify_recipients_feedback',
        'notify_chefs_reminder',
        'notify_deliverers_reminder',
        'notify_deliverers_details',
        'mark_as_delivered'
    )
    inlines = (
        MealDeliveryCommentInline,
    )
    search_fields = (
        'request__name',
        'chef__email',
        'chef__volunteer__name',
        'deliverer__email',
        'deliverer__volunteer__name',
    )
    list_select_related = (
        'request',
        'chef',
        'chef__volunteer',
        'deliverer',
        'deliverer__volunteer',
    )

    def request_phone(self, obj):
        return obj.request.phone_number
    request_phone.short_description = 'Requestor phone'

    def request_landline(self, obj):
        return 'No' if obj.request.can_receive_texts else 'Yes'
    request_landline.short_description = "Landline"

    def edit_link(self, delivery):
        return 'Edit delivery'
    edit_link.short_description = 'Edit link'

    def request_link(self, delivery):
        return obj_link(delivery.request, 'mealrequest')
    request_link.short_description = 'Request'

    def chef_link(self, delivery):
        return user_link(delivery.chef)
    chef_link.short_description = 'Chef'
    chef_link.admin_order_field = 'chef__volunteer__name'

    def deliverer_link(self, delivery):
        return user_link(delivery.deliverer)
    deliverer_link.short_description = 'Deliverer'
    deliverer_link.admin_order_field = 'deliverer__volunteer__name'

    def pickup_range(self, delivery):
        return short_time(delivery.pickup_start) + ' - ' + short_time(delivery.pickup_end)
    pickup_range.short_description = 'Pickup range'

    def dropoff_range(self, delivery):
        return short_time(delivery.dropoff_start) + ' - ' + short_time(delivery.dropoff_end)
    dropoff_range.short_description = 'Dropoff range'

    def completed(self, obj):
        return obj.status == Status.DELIVERED
    completed.admin_order_field = 'status'
    completed.boolean = True

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

    def notify_recipients_delivery(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_delivery_notification')
    notify_recipients_delivery.short_description = "Send text to recipients about delivery window"

    def notify_recipients_reminder(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_reminder_notification')
    notify_recipients_reminder.short_description = "Send text to recipients reminding them about TODAY's request"

    def notify_recipients_feedback(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_feedback_request')
    notify_recipients_feedback.short_description = "Send text to recipients requesting their feedback through form"

    def notify_chefs_reminder(self, request, queryset):
        self.send_notifications(request, queryset, 'send_chef_reminder_notification')
    notify_chefs_reminder.short_description = "Send text to chefs reminding them about the request"

    def notify_deliverers_reminder(self, request, queryset):
        self.send_notifications(request, queryset, 'send_deliverer_reminder_notification')
    notify_deliverers_reminder.short_description = "Send text to deliverers reminding them about the request"

    def notify_deliverers_details(self, request, queryset):
        self.send_notifications(request, queryset, 'send_detailed_deliverer_notification')
    notify_deliverers_details.short_description = "Send text to deliverers with details about TODAY's request"


class GroceryRequestCommentInline(CommentInline):
    model = GroceryRequestComment


class GroceryRequestAdmin(admin.ModelAdmin):
    list_display = (
        'edit_link',
        'name',
        'phone_number',
        'landline',
        'city',
        'gift_card',
        'physical_gift_card',
        'created_at',
        'delivery_date',
        'completed',
    )
    list_filter = (
        'completed',
        LandlineFilter,
        'created_at',
        'gift_card',
        'physical_gift_card',
    )
    inlines = (
        GroceryRequestCommentInline,
    )
    search_fields = (
        'name',
        'email',
        'phone_number'
    )
    actions = (
        'mark_complete',
        'notify_recipients_scheduled',
        'notify_recipients_allergies',
        'notify_recipients_reminder',
        'notify_recipients_rescheduled',
    )

    def edit_link(self, request):
        return 'Edit request G%d' % request.id
    edit_link.short_description = 'Edit link'

    def landline(self, obj):
        return 'No' if obj.can_receive_texts else 'Yes'
    landline.short_description = "Landline"

    def send_notifications(self, request, queryset, method_name):
        """
        Helper utility for invoking notification sending methods

        This is more complex than usual because we need to account for situations where we send a subset of notifications.
        Some notifications might succeed while others fail.
        If they all succeed, we simply emit the success message with a "Success" status
        If they partially fail, we emit info on both the successes and an error breakdown, with a "Warning" status
        If they all fail, we emit the error breakdown with a "Error" status

        method_name is the name of the method to invoke on each request instance.
        """
        successes, errors = [], []

        # Try to notify all recipients, capture any error messages that are received
        for grocery_request in queryset:
            try:
                send_notification_method = getattr(grocery_request, method_name)
                send_notification_method()
                successes.append(grocery_request)
            except SendNotificationException as e:
                errors.append(e.message)

        sent = len(successes)
        unsent = len(errors)
        total = sent + unsent

        prefix_message = ngettext(
            "%d request was selected",
            "%d requests were selected",
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

    def notify_recipients_scheduled(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_scheduled_notification')
    notify_recipients_scheduled.short_description = "Send text to recipients about scheduled date"

    def notify_recipients_allergies(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_allergy_notification')
    notify_recipients_allergies.short_description = "Send text to recipients with allergy explanation"

    def notify_recipients_reminder(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_reminder_notification')
    notify_recipients_reminder.short_description = "Send text to remind recipients of today's delivery"

    def notify_recipients_rescheduled(self, request, queryset):
        self.send_notifications(request, queryset, 'send_recipient_rescheduled_notification')
    notify_recipients_rescheduled.short_description = "Send text to recipients with rescheduled explanation"

    def mark_complete(self, request, queryset):
        updated = queryset.update(completed=True)
        self.message_user(request, ngettext(
            "%d grocery request has been marked complete",
            "%d grocery requests have been marked complete",
            updated,
        ) % updated, messages.SUCCESS)
    mark_complete.short_description = "Mark selected grocery requests as complete"


admin.site.register(MealRequest, MealRequestAdmin)
admin.site.register(MealDelivery, MealDeliveryAdmin)
admin.site.register(GroceryRequest, GroceryRequestAdmin)
