from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestEstateAccount(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Buyer"})
        cls.property_type = cls.env["estate.property.type"].create({
            "name": "Test Type",
        })

    def _create_property(self, **overrides):
        vals = {
            "name": "Test Property",
            "expected_price": 200000.00,
            "property_type_id": self.property_type.id,
        }
        vals.update(overrides)
        return self.env["estate.property"].create(vals)

    def _create_and_accept_offer(self, prop, price=200000.00):
        offer = self.env["estate.property.offer"].create({
            "property_id": prop.id,
            "price": price,
            "partner_id": self.partner.id,
        })
        offer.action_accept()
        return offer

    def test_invoice_created_on_sold(self):
        """Brief acceptance pseudocode: selling a property creates a draft invoice."""
        prop = self._create_property()
        self._create_and_accept_offer(prop)
        prop.action_sold()

        self.assertEqual(prop.invoice_count, 1)
        invoice = prop.invoice_ids
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertAlmostEqual(
            invoice.amount_untaxed,
            200000.00 * 0.06 + 100.00,
            places=2,
        )
        self.assertEqual(invoice.state, "draft")

    def test_invoice_has_two_lines(self):
        """Verify both invoice lines (commission + admin fee) are present."""
        prop = self._create_property()
        self._create_and_accept_offer(prop)
        prop.action_sold()

        invoice = prop.invoice_ids
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        commission = invoice.invoice_line_ids.filtered(lambda l: l.name == "Commission")
        admin_fee = invoice.invoice_line_ids.filtered(lambda l: l.name == "Administrative fee")
        self.assertEqual(len(commission), 1)
        self.assertEqual(len(admin_fee), 1)
        self.assertAlmostEqual(commission.price_unit, 12000.00, places=2)
        self.assertAlmostEqual(admin_fee.price_unit, 100.00, places=2)

    def test_sold_without_buyer_raises(self):
        """Brief constraint: selling without buyer_id must fail gracefully."""
        prop = self._create_property()
        # No offer accepted, so no buyer_id is set.
        with self.assertRaises(UserError):
            prop.action_sold()

    def test_already_sold_raises(self):
        """Brief constraint: re-running action_sold must not silently create a second invoice."""
        prop = self._create_property()
        self._create_and_accept_offer(prop)
        prop.action_sold()
        # First call succeeded; second call must raise.
        with self.assertRaises(UserError):
            prop.action_sold()
        # Idempotency check: still only one invoice exists.
        self.assertEqual(prop.invoice_count, 1)

    def test_invoice_journal_matches_property_company(self):
        """Multi-company correctness: invoice journal belongs to property's company."""
        prop = self._create_property()
        self._create_and_accept_offer(prop)
        prop.action_sold()

        invoice = prop.invoice_ids
        self.assertEqual(invoice.company_id, prop.company_id)
        self.assertEqual(invoice.journal_id.company_id, prop.company_id)
        self.assertEqual(invoice.journal_id.type, "sale")