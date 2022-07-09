"""URLS for Circuit Maintenance."""
from django.urls import path
from nautobot.extras.views import ObjectChangeLogView

from . import views
from .models import CircuitMaintenance, CircuitImpact, Note, NotificationSource

urlpatterns = [
    # Overview
    # path("config-compliance/overview/", views.ConfigComplianceOverview.as_view(), name="configcompliance_report"),
    path("maintenance/overview/", views.CircuitMaintenanceOverview.as_view(), name="circuitmaintenance_overview"),
    #
    #  Maintenance
    path("maintenance/", views.CircuitMaintenanceListView.as_view(), name="circuitmaintenance_list"),
    path("maintenance/add/", views.CircuitMaintenanceEditView.as_view(), name="circuitmaintenance_add"),
    path("maintenance/import/", views.CircuitMaintenanceBulkImportView.as_view(), name="circuitmaintenance_import"),
    path("maintenance/edit/", views.CircuitMaintenanceBulkEditView.as_view(), name="circuitmaintenance_bulk_edit"),
    path(
        "maintenance/delete/", views.CircuitMaintenanceBulkDeleteView.as_view(), name="circuitmaintenance_bulk_delete"
    ),
    path("maintenance/<uuid:pk>/", views.CircuitMaintenanceView.as_view(), name="circuitmaintenance"),
    path("maintenance/<uuid:pk>/edit/", views.CircuitMaintenanceEditView.as_view(), name="circuitmaintenance_edit"),
    path(
        "maintenance/<uuid:pk>/delete/", views.CircuitMaintenanceDeleteView.as_view(), name="circuitmaintenance_delete"
    ),
    path(
        "maintenance/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="circuitmaintenance_changelog",
        kwargs={"model": CircuitMaintenance},
    ),
    path("maintenance/job/", views.CircuitMaintenanceJobView.as_view(), name="circuitmaintenance_job"),
    # Circuit Impact
    path("impact/", views.CircuitImpactListView.as_view(), name="circuitimpact_list"),
    path(
        "impact/add/",
        views.CircuitImpactEditView.as_view(),
        name="circuitimpact_add",
    ),
    path(
        "impact/<uuid:pk>/",
        views.CircuitImpactView.as_view(),
        name="circuitimpact",
    ),
    path(
        "impact/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="circuitimpact_changelog",
        kwargs={"model": CircuitImpact},
    ),
    path(
        "impact/<uuid:pk>/edit/",
        views.CircuitImpactEditView.as_view(),
        name="circuitimpact_edit",
    ),
    path(
        "impact/<uuid:pk>/delete/",
        views.CircuitImpactDeleteView.as_view(),
        name="circuitimpact_delete",
    ),
    path("impact/edit/", views.CircuitImpactBulkEditView.as_view(), name="circuitimpact_bulk_edit"),
    path("impact/delete/", views.CircuitImpactBulkDeleteView.as_view(), name="circuitimpact_bulk_delete"),
    path("impact/import/", views.CircuitImpactBulkImportView.as_view(), name="circuitimpact_import"),
    # Notes
    path(
        "note/add/",
        views.NoteEditView.as_view(),
        name="note_add",
    ),
    path(
        "note/<uuid:pk>/edit/",
        views.NoteEditView.as_view(),
        name="note_edit",
    ),
    path("note/", views.NoteListView.as_view(), name="note_list"),
    path(
        "note/<uuid:pk>/delete/",
        views.NoteDeleteView.as_view(),
        name="note_delete",
    ),
    path("note/<uuid:pk>/", views.NoteView.as_view(), name="note"),
    path("note/edit/", views.NoteBulkEditView.as_view(), name="note_bulk_edit"),
    path("note/delete/", views.NoteBulkDeleteView.as_view(), name="note_bulk_delete"),
    path("note/import/", views.NoteBulkImportView.as_view(), name="note_import"),
    path(
        "note/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="note_changelog",
        kwargs={"model": Note},
    ),
    # Raw Notification
    path("rawnotification/", views.RawNotificationListView.as_view(), name="rawnotification_list"),
    path("rawnotification/<uuid:pk>/", views.RawNotificationView.as_view(), name="rawnotification"),
    path("rawnotification/<uuid:pk>/delete/", views.RawNotificationDeleteView.as_view(), name="rawnotification_delete"),
    path(
        "rawnotification/delete/",
        views.RawNotificationBulkDeleteView.as_view(),
        name="rawnotification_bulk_delete",
    ),
    # Parsed Notification
    path(
        "parsednotification/<uuid:pk>/",
        views.ParsedNotificationView.as_view(),
        name="parsednotification",
    ),
    # Notification Source
    path("source/", views.NotificationSourceListView.as_view(), name="notificationsource_list"),
    path("source/google_authorize/<slug:slug>/", views.google_authorize, name="google_authorize"),
    path("source/google_oauth2callback/", views.google_oauth2callback, name="google_oauth2callback"),
    path("source/edit/", views.NotificationSourceBulkEditView.as_view(), name="notificationsource_bulk_edit"),
    path("source/<slug:slug>/edit/", views.NotificationSourceEditView.as_view(), name="notificationsource_edit"),
    path("source/<slug:slug>/", views.NotificationSourceView.as_view(), name="notificationsource"),
    path(
        "source/<slug:slug>/validate/", views.NotificationSourceValidate.as_view(), name="notificationsource_validate"
    ),
    path(
        "source/<slug:slug>/changelog/",
        ObjectChangeLogView.as_view(),
        name="notificationsource_changelog",
        kwargs={"model": NotificationSource},
    ),
]
