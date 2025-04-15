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

 
from db import dbase

class Users:       
    def __init__(self, col):
        self.collection = col

    def new(self, username, password, balance=0, is_admin=False, history=None):
        if history is None:
            history = []
        clist = dbase[self.collection]
        clist.insert_one({
            "username": username, 
            "password": password,
            "balance": balance,
            "is_admin": is_admin,
            "history": history
        })

    def exists(self, username):
        clist = dbase[self.collection]
        return clist.find_one({"username": username}) is not None

    def get(self, username):
        clist = dbase[self.collection]
        return clist.find_one({"username": username})
    
    def get_by_username(self, username):
        return self.get(username)
    
    def get_all(self):
        clist = dbase[self.collection]
        return clist.find()
    
    def update_balance(self, username, amount_to_add):
        clist = dbase[self.collection]
        d = clist.find_one({"username": username})
        current_balance = d.get("balance", 0)
        clist.update_one({"username": username}, {"$set": {"balance": current_balance + amount_to_add}})
    
    def reduce_balance(self, username, amount_to_reduce):
        clist = dbase[self.collection]
        d = clist.find_one({"username": username})
        current_balance = d.get("balance", 0)
        clist.update_one({"username": username}, {"$set": {"balance": current_balance - amount_to_reduce}})
    
    def add_history(self, username, order):
        clist = dbase[self.collection]
        user = clist.find_one({"username": username})
        history = user.get("history", [])
        history.append(order)
        clist.update_one({"username": username}, {"$set": {"history": history}})
