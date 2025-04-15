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


import yaml

class Config(object):
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as stream:
            config_data = yaml.safe_load(stream)

        self.DEBUG = config_data.get("DEBUG", False)

        self.BUYER_EMAIL = config_data.get("secret_key", "")
        self.SECRET_KEY = config_data.get("secret_key", "")
        
        self.MONGO_DB_URI = config_data.get("database", {}).get("mongo_uri", "mongodb://localhost:27017/")
        self.USERS_DB = config_data.get("database", {}).get("users_db", "users")
        self.PRODUCTS_DB = config_data.get("database", {}).get("products_db", "products")

        cp_config = config_data.get("coinpayments", {})
        self.CP_PRIVATE_KEY = cp_config.get("private_key", "")
        self.CP_PUBLIC_KEY = cp_config.get("public_key", "")

        self.COIN_MAPPING = config_data.get("coin_mapping", {})

config = Config()
