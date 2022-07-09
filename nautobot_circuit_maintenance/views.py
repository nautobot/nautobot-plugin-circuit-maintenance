"""Views for Circuit Maintenance."""
from datetime import datetime as datet
import datetime
import logging

import google_auth_oauthlib

from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from nautobot.core.views import generic
from nautobot.circuits.models import Circuit, Provider
from nautobot_circuit_maintenance import filters, forms, models, tables
from nautobot_circuit_maintenance.handle_notifications.sources import RedirectAuthorize, Source
from nautobot_circuit_maintenance.models import CircuitMaintenance


logger = logging.getLogger(__name__)


class CircuitMaintenanceOverview(generic.ObjectListView):
    """View for an overview dashboard of summary view."""

    action_buttons = ("export",)
    filterset = filters.CircuitMaintenanceFilterSet
    filterset_form = forms.CircuitMaintenanceFilterForm
    table = tables.CircuitMaintenanceTable
    template_name = "nautobot_circuit_maintenance/circuit_maintenance_overview.html"
    queryset = models.CircuitMaintenance.objects.all()  # Needs to remain all objects, otherwise other calcs will fail.

    def setup(self, request, *args, **kwargs):
        """Using request object to perform filtering based on query params."""
        super().setup(request, *args, **kwargs)
        upcoming_days_maintenances = self.get_maintenances_next_n_days(n_days=7)

        # Get historical matrix for number of maintenances, includes calculating the average number per month
        historical_matrix = self._get_historical_matrix()

        ###############################################################
        # Get Average duration for the maintenances
        ###############################################################
        total_duration_in_minutes = 0

        for ckt_maint in self.queryset:
            duration = ckt_maint.end_time - ckt_maint.start_time
            total_duration_in_minutes += round(duration.seconds / 60.0, 0)

        circuit_maint_count = CircuitMaintenance.objects.count()
        if circuit_maint_count > 0:
            average_maintenance_duration = str(round(total_duration_in_minutes / circuit_maint_count, 2)) + " minutes"
        else:
            average_maintenance_duration = "No maintenances found."

        # Get count of upcoming maintenances
        upcoming_maintenance_count = self.calculate_future_maintenances()

        # Build up a dictionary of metrics to pass into the loop within the template
        metric_values = {
            "7 Day Upcoming Maintenances": len(upcoming_days_maintenances),
            "Historical - 7 Day": len(historical_matrix["past_7_days_maintenance"]),
            "Historical - 30 Days": len(historical_matrix["past_30_days_maintenance"]),
            "Historical - 365 Days": len(historical_matrix["past_365_days_maintenance"]),
            "Average Duration of Maintenances": average_maintenance_duration,
            "Future Maintenances": upcoming_maintenance_count,
            "Average Number of Maintenances Per Month": round(self.get_maintenances_per_month(), 1),
            "Next 30 Days, Maintenance to Circuit Ratio": round(
                len(self.get_maintenances_next_n_days(n_days=30)) / Circuit.objects.count(), 2
            ),
        }

        # Build out the extra content, but this does require that there is a method of `extra_content` to be created.
        # If this method is not defined, and returning the extra_content value, then the data will not be passed to the
        # template.
        self.extra_content = {
            "upcoming_maintenances": upcoming_days_maintenances,
            "circuit_maint_metric_data": metric_values,
        }

    def extra_context(self):
        """Extra content method on."""
        # add global aggregations to extra context.

        return self.extra_content

    def get_maintenances_next_n_days(self, n_days: int):
        """Gets maintenances in the next n number of days.

        Args:
            n_days (int): Number of days up coming

        Returns:
            Set: Set of maintenances that are up coming
        """
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=n_days)
        maintenances = self.queryset
        return_list = []
        for maintenance in maintenances:
            if today <= maintenance.start_time.date() <= end_date:
                return_list.append(maintenance)

        return return_list

    def get_maintenance_past_n_days(self, n_days: int):
        """Gets maintenances in the past n number of days.

        Args:
            n_days (int): Should be a negative number for the number of days.
        """
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=n_days)
        maintenances = self.queryset
        return_list = []
        for maintenance in maintenances:
            if end_date <= maintenance.start_time.date() < today:
                return_list.append(maintenance)

        return return_list

    def _get_historical_matrix(self):
        """Gets the historical matrix of the past maintenances.

        Returns:
            dict: A dictionary that represents the historical matrix maintenance record data.

            {
                "7 Days": count of past 7 days of maintenance,
                "30 Days": count of past 30 days of maintenance,
                "365 Days": count of past 30 days of maintenances
            }
        """
        # TODO: Move to a generic function set up, since this is something that should be exposed via the Capacity
        #       Metrics plugin when enabled.
        return_dict = {
            "past_7_days_maintenance": self.get_maintenance_past_n_days(-7),
            "past_30_days_maintenance": self.get_maintenance_past_n_days(-30),
            "past_365_days_maintenance": self.get_maintenance_past_n_days(-365),
        }
        return return_dict

    def calculate_future_maintenances(self):
        """Method to calculate future maintenances.

        Returns:
            int: Count of future maintenances
        """
        today = datetime.date.today()
        count = 0
        for ckt_maint in self.queryset:
            if ckt_maint.start_time.date() > today:
                count += 1

        return count

    @staticmethod
    def get_month_list():
        """Gets the list of months that circuit maintenances have happened.

        In order to know which months there are needed for a calculate average number of maintenances per month.

        Returns:
            list: List of months from first to last maintenance.
        """
        ordered_ckt_maintenance = CircuitMaintenance.objects.order_by("start_time")
        dates = [
            str(ordered_ckt_maintenance.first().start_time.date()),
            str(ordered_ckt_maintenance.last().start_time.date()),
        ]
        start, end = [datet.strptime(_, "%Y-%m-%d") for _ in dates]
        total_months = lambda dt: dt.month + 12 * dt.year  # noqa
        month_list = []
        for tot_m in range(total_months(start) - 1, total_months(end)):
            year, month = divmod(tot_m, 12)
            month_list.append(datet(year, month + 1, 1).strftime("%Y-%m"))
        return month_list

    def get_maintenances_per_month(self):
        """Calculates the number of circuit maintenances per month.

        Returns:
            float: Average maintenances per month
        """
        # Initialize each month of maintenances
        months = self.get_month_list()

        if len(months) == 0:
            return 0

        return len(self.queryset) / len(months)


class CircuitMaintenanceListView(generic.ObjectListView):
    """View for listing the config circuitmaintenance feature definition."""

    queryset = models.CircuitMaintenance.objects.order_by("-start_time")
    table = tables.CircuitMaintenanceTable
    filterset = filters.CircuitMaintenanceFilterSet
    filterset_form = forms.CircuitMaintenanceFilterForm
    action_buttons = ("add", "export")


class CircuitMaintenanceView(generic.ObjectView):
    """Detail view for specific circuit maintenances."""

    queryset = models.CircuitMaintenance.objects.all()

    def get_extra_context(self, request, instance):
        """Extend content of detailed view for Circuit Maintenance."""
        maintenance_note = models.Note.objects.filter(maintenance=instance)
        circuits = models.CircuitImpact.objects.filter(maintenance=instance)
        parsednotification = models.ParsedNotification.objects.filter(maintenance=instance).order_by(
            "-raw_notification__date"
        )

        return {
            "circuits": circuits,
            "maintenance_note": maintenance_note,
            "parsednotification": parsednotification,
        }


class CircuitMaintenanceEditView(generic.ObjectEditView):
    """View for editting circuit maintenances."""

    queryset = models.CircuitMaintenance.objects.all()
    model_form = forms.CircuitMaintenanceForm


class CircuitMaintenanceDeleteView(generic.ObjectDeleteView):
    """View for deleting circuit maintenances."""

    queryset = models.CircuitMaintenance.objects.all()


class CircuitMaintenanceBulkImportView(generic.BulkImportView):
    """View for bulk of circuit maintenances."""

    queryset = models.CircuitMaintenance.objects.all()
    model_form = forms.CircuitMaintenanceCSVForm
    table = tables.CircuitMaintenanceTable


class CircuitMaintenanceBulkEditView(generic.BulkEditView):
    """View for bulk editing circuitmaintenance features."""

    queryset = models.CircuitMaintenance.objects.all()
    table = tables.CircuitMaintenanceTable
    form = forms.CircuitMaintenanceBulkEditForm


class CircuitMaintenanceBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting circuitmaintenance features."""

    queryset = models.CircuitMaintenance.objects.all()
    table = tables.CircuitMaintenanceTable


class CircuitMaintenanceJobView(generic.ObjectView):
    """Special View to trigger the Job to look for new Circuit Maintenances."""

    queryset = models.CircuitMaintenance.objects.all()

    def get(self, request, *args, **kwargs):
        """Custom GET to run a the Job."""
        class_path = (
            "plugins/nautobot_circuit_maintenance.handle_notifications.handler/HandleCircuitMaintenanceNotifications"
        )

        return redirect(reverse("extras:job", kwargs={"class_path": class_path}))


class CircuitImpactListView(generic.ObjectListView):
    """View for listing all circuit impact."""

    table = tables.CircuitImpactTable
    queryset = models.CircuitImpact.objects.all()
    action_buttons = ("add", "export")


class CircuitImpactView(generic.ObjectView):
    """Detail view for specific Circuit Impact windows."""

    queryset = models.CircuitImpact.objects.all()


class CircuitImpactEditView(generic.ObjectEditView):
    """View for editting Circuit Impact."""

    queryset = models.CircuitImpact.objects.all()
    model_form = forms.CircuitImpactForm


class CircuitImpactDeleteView(generic.ObjectDeleteView):
    """View for deleting Circuit Impact."""

    queryset = models.CircuitImpact.objects.all()


class CircuitImpactBulkImportView(generic.BulkImportView):
    """View for bulk of circuit Impact."""

    queryset = models.CircuitImpact.objects.all()
    model_form = forms.CircuitImpactCSVForm
    table = tables.CircuitImpactTable


class CircuitImpactBulkEditView(generic.BulkEditView):
    """View for bulk editing circuit impact features."""

    queryset = models.CircuitImpact.objects.all()
    table = tables.CircuitImpactTable
    form = forms.CircuitImpactBulkEditForm


class CircuitImpactBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting circuit impact features."""

    queryset = models.CircuitImpact.objects.all()
    table = tables.CircuitImpactTable


class NoteListView(generic.ObjectListView):
    """View for listing all notes."""

    table = tables.NoteTable
    queryset = models.Note.objects.all()
    action_buttons = ("add", "export")


class NoteEditView(generic.ObjectEditView):
    """View for editing a maintenance note."""

    queryset = models.Note.objects.all()
    model_form = forms.NoteForm


class NoteView(generic.ObjectView):
    """View for maintenance note."""

    queryset = models.Note.objects.all()


class NoteDeleteView(generic.ObjectDeleteView):
    """View for deleting maintenance note."""

    queryset = models.Note.objects.all()


class NoteBulkImportView(generic.BulkImportView):
    """View for bulk of Notes."""

    queryset = models.Note.objects.all()
    model_form = forms.NoteCSVForm
    table = tables.NoteTable


class NoteBulkEditView(generic.BulkEditView):
    """View for bulk editing Notes."""

    queryset = models.Note.objects.all()
    table = tables.NoteTable
    form = forms.NoteBulkEditForm


class NoteBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting Notea."""

    queryset = models.Note.objects.all()
    table = tables.NoteTable


class RawNotificationView(generic.ObjectView):
    """Detail view for raw notifications."""

    queryset = models.RawNotification.objects.all()

    def get_extra_context(self, request, instance):
        """Extend content of detailed view for RawNotification."""
        if instance.parsed:
            parsed_notification = models.ParsedNotification.objects.filter(raw_notification=instance).last()
        else:
            parsed_notification = None
        try:
            if isinstance(instance.raw, bytes):
                raw_repr = instance.raw.decode("utf-8", "strict")
            else:
                raw_repr = instance.raw.tobytes().decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raw_repr = "Raw content was not able to be decoded with utf-8"
            logger.warning("%s: %s", raw_repr, exc)

        return {"parsed_notification": parsed_notification, "raw_repr": raw_repr}


class RawNotificationListView(generic.ObjectListView):
    """View for listing all raw notifications."""

    table = tables.RawNotificationTable
    queryset = models.RawNotification.objects.order_by("-stamp")
    filterset = filters.RawNotificationFilterSet
    filterset_form = forms.RawNotificationFilterSetForm
    action_buttons = ("export",)


class RawNotificationBulkDeleteView(generic.BulkDeleteView):
    """View for bulk deleting Circuit Maintenance Notifications entries."""

    queryset = models.RawNotification.objects.all()
    table = tables.RawNotificationTable


class RawNotificationDeleteView(generic.ObjectDeleteView):
    """View for deleting Raw Notification."""

    model = models.RawNotification
    queryset = models.RawNotification.objects.all()


class ParsedNotificationView(generic.ObjectView):
    """Detail view for parsed notifications."""

    queryset = models.ParsedNotification.objects.all()


class NotificationSourceListView(generic.ObjectListView):
    """View for Notification Source."""

    table = tables.NotificationSourceTable
    queryset = models.NotificationSource.objects.all()
    filterset = filters.NotificationSourceFilterSet
    filterset_form = forms.NotificationSourceFilterSetForm
    action_buttons = ("edit", "export")


class NotificationSourceView(generic.ObjectView):
    """View for NotificationSource."""

    queryset = models.NotificationSource.objects.all()

    def get_extra_context(self, request, instance):  # pylint: disable=unused-argument
        """Extend content of detailed view for NotificationSource."""
        source = Source.init(name=instance.name)
        return {
            "providers": Provider.objects.filter(pk__in=[provider.pk for provider in instance.providers.all()]),
            "account": source.get_account_id(),
            "source_type": source.__class__.__name__,
        }


class NotificationSourceEditView(generic.ObjectEditView):
    """View for editting NotificationSource."""

    model = models.NotificationSource
    queryset = models.NotificationSource.objects.all()
    model_form = forms.NotificationSourceForm


class NotificationSourceBulkEditView(generic.BulkEditView):
    """View for bulk editing NotificationSource."""

    queryset = models.NotificationSource.objects.all()
    table = tables.NotificationSourceTable
    form = forms.NotificationSourceBulkEditForm


class NotificationSourceValidate(generic.ObjectView):
    """View for validate NotificationSource authenticate."""

    queryset = models.NotificationSource.objects.all()

    def get(self, request, *args, **kwargs):
        """Custom GET to run a authentication validation."""
        instance = get_object_or_404(self.queryset, **kwargs)
        try:
            source = Source.init(name=instance.name)
            is_authenticated, mess_auth = source.test_authentication()

            message = "SUCCESS" if is_authenticated else "FAILED"
            message += f": {mess_auth}"
        except ValueError as exc:
            message = str(exc)
        except RedirectAuthorize as exc:
            try:
                return redirect(
                    reverse(
                        f"plugins:nautobot_circuit_maintenance:{str(exc.url_name)}",
                        kwargs={
                            "slug": exc.source_slug,
                        },
                    )
                )
            except NoReverseMatch:
                pass

        return render(
            request,
            self.get_template_name(),
            {
                "object": instance,
                "authentication_message": message,
                "providers": Provider.objects.filter(pk__in=[provider.pk for provider in instance.providers.all()]),
                "account": source.get_account_id(),
                "source_type": source.__class__.__name__,
            },
        )


def google_authorize(request, slug):
    """View to start the Google OAuth authorization flow."""
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    notification_source = models.NotificationSource.objects.get(slug=slug)
    source = Source.init(name=notification_source.name)
    request.session["CLIENT_SECRETS_FILE"] = source.credentials_file
    request.session["SCOPES"] = source.SCOPES + source.extra_scopes
    request.session["SOURCE_SLUG"] = slug

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        request.session["CLIENT_SECRETS_FILE"], scopes=request.session["SCOPES"]
    )
    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the Google Cloud Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.

    flow.redirect_uri = (
        request.scheme
        + "://"
        + request.get_host()
        + reverse("plugins:nautobot_circuit_maintenance:google_oauth2callback")
    )
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type="offline",
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
        # With "consent" as prompt option, we are going to ask for consent to authorize that the Application
        # that has been created in the API Console can read emails. The default option only asks about it one
        # time for different client usages, so if the Nautobot server was not the first one, it won't have the
        # necessary "refresh_token" in the response, that is used to automatically renew the token when expired,
        # without asking the user for login every time.
        prompt="consent",
    )
    # Store the state so the callback can verify the auth server response.
    request.session["state"] = state

    return redirect(authorization_url)


def google_oauth2callback(request):
    """View to receive the callback from Google OAuth authorization flow."""
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = request.session.get("state")
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        request.session.get("CLIENT_SECRETS_FILE"), scopes=request.session.get("SCOPES"), state=state
    )

    flow.redirect_uri = (
        request.scheme
        + "://"
        + request.get_host()
        + reverse("plugins:nautobot_circuit_maintenance:google_oauth2callback")
    )
    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.build_absolute_uri()

    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    credentials = flow.credentials
    source_slug = request.session.get("SOURCE_SLUG")

    try:
        notification_source = models.NotificationSource.objects.get(slug=source_slug)
        notification_source.token = credentials
        notification_source.save()
    except models.NotificationSource.DoesNotExist:
        logger.warning("Google OAuth callback for %s is not matching any existing NotificationSource", source_slug)

    return redirect(
        reverse(
            "plugins:nautobot_circuit_maintenance:notificationsource_validate",
            kwargs={"slug": source_slug},
        )
    )
