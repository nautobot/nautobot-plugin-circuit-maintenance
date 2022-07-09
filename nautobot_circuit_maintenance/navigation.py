"""Navigation for Circuit Maintenance."""
from nautobot.extras.plugins import PluginMenuButton, PluginMenuItem
from nautobot.utilities.choices import ButtonColorChoices

menu_items = (
    PluginMenuItem(
        link="plugins:nautobot_circuit_maintenance:circuitmaintenance_overview",
        link_text="Circuit Maintenance Dashboard",
        permissions=["nautobot_circuit_maintenance.view_circuitmaintenance"],
    ),
    PluginMenuItem(
        link="plugins:nautobot_circuit_maintenance:circuitmaintenance_list",
        link_text="Circuit Maintenances",
        permissions=["nautobot_circuit_maintenance.view_circuitmaintenance"],
        buttons=(
            PluginMenuButton(
                link="plugins:nautobot_circuit_maintenance:circuitmaintenance_add",
                title="Add Circuit Maintenance",
                icon_class="mdi mdi-plus-thick",
                color=ButtonColorChoices.GREEN,
                permissions=["nautobot_circuit_maintenance.add_circuitmaintenance"],
            ),
            PluginMenuButton(
                link="plugins:nautobot_circuit_maintenance:circuitmaintenance_job",
                title="Job to update Circuit Maintenance",
                icon_class="mdi mdi-database-refresh",
                color=ButtonColorChoices.GREEN,
                permissions=["nautobot_circuit_maintenance.add_circuitmaintenance"],
            ),
        ),
    ),
    PluginMenuItem(
        link="plugins:nautobot_circuit_maintenance:rawnotification_list",
        link_text="Notifications",
        permissions=["nautobot_circuit_maintenance.view_circuitmaintenance"],
    ),
    PluginMenuItem(
        link="plugins:nautobot_circuit_maintenance:notificationsource_list",
        link_text="Notification Sources",
        permissions=["nautobot_circuit_maintenance.view_notificationsource"],
    ),
)
