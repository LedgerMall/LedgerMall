# LedgerMall: Next-Gen Crypto Digital Marketplace
# Copyright (C) 2025 Samrat Talukdar
#
# This file is part of LedgerMall.
#
# LedgerMall is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LedgerMall is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LedgerMall. If not, see <https://www.gnu.org/licenses/>.
#
# This software applies the provisions of the GNU Affero General Public License
# to any service that uses it. If you run this software over a network, you must
# make the source code of any modifications available to users of the service.
#
# Attribution Notice:
# If you use, modify, or distribute this software, you must include an appropriate
# credit to the original author, Samrat Talukdar, in all copies or substantial
# portions of the software. This credit should appear in the documentation, source code,
# or user interface in a manner that makes it clear Samrat Talukdar is the original author.
#
# For further details on the license, visit: https://www.gnu.org/licenses/agpl-3.0.html


import unittest
from app import app, users_db, products
from flask import session

class TestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        self.test_username = "testuser"
        self.test_password = "test123"
        test_user = users_db.get_by_username(self.test_username)
        if not test_user:
            from flask_bcrypt import Bcrypt
            bcrypt = Bcrypt(app)
            hashed = bcrypt.generate_password_hash(self.test_password).decode("utf-8")
            self.test_user_id = 99999
            users_db.new(self.test_user_id, self.test_username, password=hashed, balance=100)
        else:
            self.test_user_id = test_user.id

    def tearDown(self):
        self.ctx.pop()

    def login(self):
        return self.app.post("/login", data={
            "username": self.test_username,
            "password": self.test_password
        }, follow_redirects=True)

    def test_add_funds(self):
        response = self.login()
        self.assertIn(b"Logged in successfully", response.data)
        with self.app.session_transaction() as sess:
            sess["current_txn"] = {"txn_id": "dummy_tx", "address": "dummy_address", "amount": "0.001", "qrcode_url": ""}
            sess["deposit_amount"] = 50
        from unittest.mock import patch
        with patch("app.crypto_client.get_tx_info") as mock_get_tx:
            mock_get_tx.return_value = {
                "status": 1,
                "status_text": "Payment Received",
                "txn_id": "dummy_tx",
                "payment_address": "dummy_address",
                "amountf": "0.001",
                "recv_confirms": 3,
                "time_expires": 9999999999
            }
            response = self.app.get("/payment/refresh", follow_redirects=True)
            self.assertIn(b"Your top-up is successful", response.data)

    def test_purchase_flow(self):
        self.login()
        products.new_category("TestCat")
        products.new_product("TestCat", "TestProduct", price=10)
        products.add_accounts("TestCat", "TestProduct", ["account1", "account2"])
        response = self.app.post("/product/TestCat/TestProduct", data={"quantity": 1}, follow_redirects=True)
        self.assertIn(b"Product added to cart", response.data)
        response = self.app.post("/cart", follow_redirects=True)
        self.assertIn(b"Purchase successful", response.data)
        self.assertIn(b"account1", response.data)

if __name__ == "__main__":
    unittest.main()
