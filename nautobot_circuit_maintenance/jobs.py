"""Circuit Maintenance plugin jobs."""
# from nautobot.extras.models import Job

from .handle_notifications.handler import HandleCircuitMaintenanceNotifications


# class FindSitesWithoutRedundancy(Job):
#     """Nautobot Job definition for finding sites without redundant circuit for impactful maintenance.

#     Args:
#         Job (Nautobot Job): Nautobot Job import.
#     """

#     class Meta:
#         """Meta definition for the Job."""

#         name = "Find Sites Without Redundancy"
#         description = "Search for sites with multiple circuits, 1 or more circuit impacts."
#         read_only = True

#     def run(self, data=None, commit=None):
#         """Executes the Job.

#         Args:
#             data (_type_, optional): _description_. Defaults to None.
#             commit (_type_, optional): _description_. Defaults to None.
#         """
#         pass


jobs = [HandleCircuitMaintenanceNotifications]
