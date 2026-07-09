from corptools.tests import CorptoolsTestCase
from eve_sde.models import Region

from pinger.models import DiscordWebhook, _webhook_passes_filters


class WebhookPassesFiltersTests(CorptoolsTestCase):
    """
    corp1 has no alliance.
    corp2 is in alli1.
    corp3 and corp4 are both in alli2.
    """

    def setUp(cls):
        super().setUp()
        cls.hook = DiscordWebhook.objects.create(
            nickname="Test Hook",
            discord_webhook="https://discord.com/api/webhooks/test",
        )
        cls.region = Region.objects.create(id=1, name="Region 1")

    def test_no_filters_configured_always_passes(self):
        self.assertTrue(
            _webhook_passes_filters(
                self.hook,
                corp_id=self.corp2.corporation_id,
                alli_id=self.alli1.alliance_id,
            )
        )
        self.assertTrue(_webhook_passes_filters(self.hook))

    def test_only_corp_filter_requires_corp_match(self):
        self.hook.corporation_filter.add(self.corp2)

        self.assertTrue(
            _webhook_passes_filters(self.hook, corp_id=self.corp2.corporation_id)
        )
        self.assertFalse(
            _webhook_passes_filters(self.hook, corp_id=self.corp3.corporation_id)
        )

    def test_only_alliance_filter_requires_alliance_match(self):
        self.hook.alliance_filter.add(self.alli1)

        self.assertTrue(
            _webhook_passes_filters(self.hook, alli_id=self.alli1.alliance_id)
        )
        self.assertFalse(
            _webhook_passes_filters(self.hook, alli_id=self.alli2.alliance_id)
        )

    def test_both_configured_corp_match_alone_passes(self):
        # corp3 is in alli2, but the hook only whitelists corp3 (not alli2).
        self.hook.corporation_filter.add(self.corp3)
        self.hook.alliance_filter.add(self.alli1)

        self.assertTrue(
            _webhook_passes_filters(
                self.hook,
                corp_id=self.corp3.corporation_id,
                alli_id=self.alli2.alliance_id,
            )
        )

    def test_both_configured_alliance_match_alone_passes(self):
        # corp4 is in alli2, hook whitelists alli2 but not corp4 specifically.
        self.hook.corporation_filter.add(self.corp2)
        self.hook.alliance_filter.add(self.alli2)

        self.assertTrue(
            _webhook_passes_filters(
                self.hook,
                corp_id=self.corp4.corporation_id,
                alli_id=self.alli2.alliance_id,
            )
        )

    def test_both_configured_neither_matches_fails(self):
        self.hook.corporation_filter.add(self.corp2)
        self.hook.alliance_filter.add(self.alli1)

        self.assertFalse(
            _webhook_passes_filters(
                self.hook,
                corp_id=self.corp4.corporation_id,
                alli_id=self.alli2.alliance_id,
            )
        )

    def test_corp_without_alliance_only_needs_corp_match(self):
        self.hook.corporation_filter.add(self.corp1)
        self.hook.alliance_filter.add(self.alli2)

        self.assertTrue(
            _webhook_passes_filters(
                self.hook, corp_id=self.corp1.corporation_id, alli_id=None
            )
        )

    def test_region_filter_is_independent_and_still_required(self):
        self.hook.corporation_filter.add(self.corp2)
        self.hook.region_filter.add(self.region)

        self.assertTrue(
            _webhook_passes_filters(
                self.hook,
                corp_id=self.corp2.corporation_id,
                region_id=self.region.id,
            )
        )
        self.assertFalse(
            _webhook_passes_filters(
                self.hook,
                corp_id=self.corp2.corporation_id,
                region_id=self.region.id + 1,
            )
        )
