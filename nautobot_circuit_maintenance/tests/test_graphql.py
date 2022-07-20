"""GraphQL tests."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from nautobot.core.graphql import execute_query
from nautobot.utilities.testing.utils import create_test_user
from nautobot.circuits.models import Circuit, CircuitType, Provider
from nautobot_circuit_maintenance.models import (
    CircuitMaintenance,
    CircuitImpact,
)

# Use the proper swappable User model
User = get_user_model()


class GraphQLTestCase(TestCase):
    """GraphQL tests."""

    @classmethod
    def setUp(cls):  # pylint: disable=arguments-differ
        """Prepare GraphQL test setup."""
        cls.user = create_test_user("graphql_testuser")

        providers = (
            Provider(name="Provider 3", slug="provider-3"),
            Provider(name="Provider 4", slug="provider-4"),
        )
        Provider.objects.bulk_create(providers)

        circuit_types = (
            CircuitType(name="Circuit Type 3", slug="circuit-type-3"),
            CircuitType(name="Circuit Type 4", slug="circuit-type-4"),
        )
        CircuitType.objects.bulk_create(circuit_types)

        circuits = (
            Circuit(cid="Circuit 4", provider=providers[0], type=circuit_types[0]),
            Circuit(cid="Circuit 5", provider=providers[1], type=circuit_types[1]),
            Circuit(cid="Circuit 6", provider=providers[1], type=circuit_types[0]),
            Circuit(cid="Circuit 7", provider=providers[1], type=circuit_types[0]),
            Circuit(cid="Circuit 8", provider=providers[1], type=circuit_types[0]),
        )
        Circuit.objects.bulk_create(circuits)

        existing_maintenance = [
            CircuitMaintenance(name="UT-TEST-3", start_time="2020-10-04 10:00:00", end_time="2020-10-04 12:00:00"),
            CircuitMaintenance(name="UT-TEST-4", start_time="2020-10-05 10:00:00", end_time="2020-10-05 12:00:00"),
        ]
        CircuitMaintenance.objects.bulk_create(existing_maintenance)

        circuit_impacts = [
            CircuitImpact(
                maintenance=existing_maintenance[0],
                circuit=circuits[0],
            ),
            CircuitImpact(
                maintenance=existing_maintenance[1],
                circuit=circuits[0],
                impact="NO-IMPACT",
            ),
        ]
        CircuitImpact.objects.bulk_create(circuit_impacts)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_execute_query_circuit_maintenance(self):
        "Test basic query for Circuit Maintenances."
        query = "{ query: circuit_maintenances {name} }"
        resp = execute_query(query, user=self.user).to_dict()
        self.assertFalse(resp["data"].get("error"))
        self.assertEqual(len(resp["data"]["query"]), 2)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_execute_query_with_variable_circuit_maintenance(self):
        "Test filtered query for Circuit Maintenances."
        query = "query ($name: [String!]) { circuit_maintenances(name:$name) {name} }"
        resp = execute_query(query, user=self.user, variables={"name": "UT-TEST-3"}).to_dict()
        self.assertFalse(resp.get("error"))
        self.assertEqual(len(resp["data"]["circuit_maintenances"]), 1)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_execute_query_circuit_impact(self):
        "Test basic query for Circuit Impacts."
        query = "{ query: circuit_impacts {impact} }"
        resp = execute_query(query, user=self.user).to_dict()
        self.assertFalse(resp["data"].get("error"))
        self.assertEqual(len(resp["data"]["query"]), 2)

    @override_settings(EXEMPT_VIEW_PERMISSIONS=["*"])
    def test_execute_query_with_variable_circuit_impact(self):
        "Test filtered query for Circuit Impacts."
        query = "query ($impact: String) { circuit_impacts(impact:$impact) {impact} }"
        resp = execute_query(query, user=self.user, variables={"impact": "OUTAGE"}).to_dict()
        self.assertFalse(resp.get("error"))
        self.assertEqual(len(resp["data"]["circuit_impacts"]), 1)
