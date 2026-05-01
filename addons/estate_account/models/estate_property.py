from odoo import api, fields, models
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _inherit = "estate.property"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    invoice_ids = fields.One2many("account.move", "property_id", string="Invoices")
    invoice_count = fields.Integer(compute="_compute_invoice_count")

    @api.depends("invoice_ids")
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    def action_sold(self):
        for record in self:
            # Validation gates — fail before creating anything
            if record.state == "sold":
                raise UserError(
                    "This property is already sold; an invoice already exists."
                )
            if not record.buyer_id:
                raise UserError("Cannot sell a property without a buyer.")

            # Resolve company-specific sales journal
            journal = self.env["account.journal"].search(
                [
                    ("company_id", "=", record.company_id.id),
                    ("type", "=", "sale"),
                ],
                limit=1,
            )
            if not journal:
                raise UserError(
                    "No sales journal found for company %s." % record.company_id.name
                )

            # Create draft invoice with company context for default account resolution
            self.env["account.move"].with_company(record.company_id).create({
                "move_type": "out_invoice",
                "partner_id": record.buyer_id.id,
                "company_id": record.company_id.id,
                "journal_id": journal.id,
                "property_id": record.id,
                "invoice_line_ids": [
                    (0, 0, {
                        "name": "Commission",
                        "quantity": 1,
                        "price_unit": record.selling_price * 0.06,
                    }),
                    (0, 0, {
                        "name": "Administrative fee",
                        "quantity": 1,
                        "price_unit": 100.00,
                    }),
                ],
            })

        # Call super to flip state — happens after invoice creation succeeds
        return super().action_sold()

    def action_view_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Invoices",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("property_id", "=", self.id)],
            "context": {"default_property_id": self.id},
        }