import logging
from ops.framework import StoredState
from ops.relation import ConsumerBase

LIBID = "1234"
LIBAPI = 1
LIBPATCH = 0
logger = logging.getLogger(__name__)


class PrometheusConsumer(ConsumerBase):
    _stored = StoredState()

    def __init__(self, charm, name, consumes, multi=False):
        super().__init__(charm, name, consumes, multi)
        self.charm = charm
        self.relation_name = name
        self._stored.set_default(targets={})
        events = self.charm.on[self.relation_name]
        self.framework.observe(events.relation_joined,
                               self._update_scrape_targets)

    def add_endpoint(self, address, rel_id=None):
        if rel_id is None:
            rel_id = super()._stored.relation_id

        targets = self._stored.targets.get(rel_id, {})
        if address in targets:
            return

        targets.append(address)
        self._update_targets(targets, rel_id)

    def remove_endpoint(self, address, rel_id=None):
        if rel_id is None:
            rel_id = super()._stored.relation_id

        targets = self._stored.targets.get(rel_id, {})
        if address not in targets:
            return

        targets.remove(address)
        self._update_targets(targets, rel_id)

    def _update_scrape_targets(self, event):
        rel_id = event.relation.id
        if not self._stored.targets.get(rel_id, []):
            return

        event.relation.data[rel_id]["targets"] = self._stored.targets[rel_id]

    def _update_targets(self, targets, rel_id):
        self._stored.targets[rel_id] = targets
        rel = self.framework.model.get_relation(self.relation_name, rel_id)
        rel.data[self.charm.app]["targets"] = targets
