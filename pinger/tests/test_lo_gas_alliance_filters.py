from unittest.mock import patch

from corptools.models import BridgeOzoneLevel, CorpAsset, Structure
from corptools.tests import CorptoolsTestCase
from eve_sde.models import ItemType

from pinger.models import DiscordWebhook, Ping
from pinger.tasks import corporation_gas_check, corporation_lo_check

LO_STRUCTURE_TYPE_ID = 35841
GAS_STRUCTURE_TYPE_ID = 81826
GAS_ASSET_TYPE_ID = 81143


@patch("pinger.models.Ping.send_ping", new=lambda self: None)
class LoGasAllianceFilterTests(CorptoolsTestCase):
    """
    corp2 is in alli1. corp3 is in alli2 (see CorptoolsTestCase fixtures).
    These tasks resolve the corp's alliance and pass it into
    _webhook_passes_filters, so a webhook that only configures an
    alliance_filter (no corporation_filter) should still ping for a
    struct owned by a corp in that alliance.
    """

    def setUp(cls):
        super().setUp()
        cls.lo_type = ItemType.objects.create(
            id=LO_STRUCTURE_TYPE_ID, name="Athanor", published=True
        )
        cls.gas_type = ItemType.objects.create(
            id=GAS_STRUCTURE_TYPE_ID, name="Tatara", published=True
        )

    def _create_structure(self, corp_audit, structure_id, type_name):
        return Structure.objects.create(
            corporation=corp_audit,
            profile_id=1,
            reinforce_hour=12,
            state="shield_vulnerable",
            structure_id=structure_id,
            system_id=1,
            type_id=type_name.id,
            type_name=type_name,
            name=f"Structure {structure_id}",
        )

    def test_lo_check_pings_webhook_filtered_by_corps_alliance(self):
        struct = self._create_structure(self.cp2, 1000, self.lo_type)
        BridgeOzoneLevel.objects.create(
            station_id=str(struct.structure_id), quantity=100000
        )

        hook = DiscordWebhook.objects.create(
            nickname="Alliance Hook",
            discord_webhook="https://discord.com/api/webhooks/lo",
            lo_pings=True,
        )
        hook.alliance_filter.add(self.alli1)

        corporation_lo_check(self.corp2.corporation_id)

        self.assertTrue(
            Ping.objects.filter(hook=hook, notification_id=-1).exists()
        )

    def test_lo_check_skips_webhook_filtered_by_other_alliance(self):
        struct = self._create_structure(self.cp2, 1001, self.lo_type)
        BridgeOzoneLevel.objects.create(
            station_id=str(struct.structure_id), quantity=100000
        )

        hook = DiscordWebhook.objects.create(
            nickname="Wrong Alliance Hook",
            discord_webhook="https://discord.com/api/webhooks/lo2",
            lo_pings=True,
        )
        hook.alliance_filter.add(self.alli2)

        corporation_lo_check(self.corp2.corporation_id)

        self.assertFalse(Ping.objects.filter(hook=hook).exists())

    def test_gas_check_pings_webhook_filtered_by_corps_alliance(self):
        struct = self._create_structure(self.cp3, 2000, self.gas_type)
        CorpAsset.objects.create(
            corporation=self.cp3,
            singleton=False,
            item_id=1,
            location_flag="Hangar",
            location_id=struct.structure_id,
            location_type="item",
            quantity=1000,
            type_id=GAS_ASSET_TYPE_ID,
        )

        hook = DiscordWebhook.objects.create(
            nickname="Alliance Hook",
            discord_webhook="https://discord.com/api/webhooks/gas",
            gas_pings=True,
        )
        hook.alliance_filter.add(self.alli2)

        corporation_gas_check(self.corp3.corporation_id)

        self.assertTrue(
            Ping.objects.filter(hook=hook, notification_id=-2).exists()
        )

    def test_gas_check_skips_webhook_filtered_by_other_alliance(self):
        struct = self._create_structure(self.cp3, 2001, self.gas_type)
        CorpAsset.objects.create(
            corporation=self.cp3,
            singleton=False,
            item_id=2,
            location_flag="Hangar",
            location_id=struct.structure_id,
            location_type="item",
            quantity=1000,
            type_id=GAS_ASSET_TYPE_ID,
        )

        hook = DiscordWebhook.objects.create(
            nickname="Wrong Alliance Hook",
            discord_webhook="https://discord.com/api/webhooks/gas2",
            gas_pings=True,
        )
        hook.alliance_filter.add(self.alli1)

        corporation_gas_check(self.corp3.corporation_id)

        self.assertFalse(Ping.objects.filter(hook=hook).exists())

    def test_lo_check_pings_all_matching_webhooks(self):
        struct = self._create_structure(self.cp2, 1002, self.lo_type)
        BridgeOzoneLevel.objects.create(
            station_id=str(struct.structure_id), quantity=100000
        )

        hook1 = DiscordWebhook.objects.create(
            nickname="Hook 1",
            discord_webhook="https://discord.com/api/webhooks/lo3",
            lo_pings=True,
        )
        hook2 = DiscordWebhook.objects.create(
            nickname="Hook 2",
            discord_webhook="https://discord.com/api/webhooks/lo4",
            lo_pings=True,
        )

        corporation_lo_check(self.corp2.corporation_id)

        self.assertTrue(Ping.objects.filter(hook=hook1).exists())
        self.assertTrue(Ping.objects.filter(hook=hook2).exists())

    def test_gas_check_pings_all_matching_webhooks(self):
        struct = self._create_structure(self.cp3, 2002, self.gas_type)
        CorpAsset.objects.create(
            corporation=self.cp3,
            singleton=False,
            item_id=3,
            location_flag="Hangar",
            location_id=struct.structure_id,
            location_type="item",
            quantity=1000,
            type_id=GAS_ASSET_TYPE_ID,
        )

        hook1 = DiscordWebhook.objects.create(
            nickname="Hook 1",
            discord_webhook="https://discord.com/api/webhooks/gas3",
            gas_pings=True,
        )
        hook2 = DiscordWebhook.objects.create(
            nickname="Hook 2",
            discord_webhook="https://discord.com/api/webhooks/gas4",
            gas_pings=True,
        )

        corporation_gas_check(self.corp3.corporation_id)

        self.assertTrue(Ping.objects.filter(hook=hook1).exists())
        self.assertTrue(Ping.objects.filter(hook=hook2).exists())
