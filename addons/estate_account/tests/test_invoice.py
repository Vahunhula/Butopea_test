from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestEstateAccount(TransactionCase):
    pass