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

class Products:
    def __init__(self, col):
        self.collection = col

    def new_category(self, category, image_url=""):
        clist = dbase[self.collection]
        clist.insert_one({
            "category": category, 
            "count": 0, 
            "image_url": image_url,
            "products": {}
        })
        
    def rm_category(self, category):
        clist = dbase[self.collection]
        clist.delete_one({"category": category})  
        
    def all_category(self):
        clist = dbase[self.collection]
        return clist.find()
        
    def new_product(self, category, pname, price, image_url=""):
        clist = dbase[self.collection]
        plist = clist.find_one({"category": category})
        new_plist = plist["products"]
        new_plist[pname] = {"price": price, "quantity": 0, "accounts": [], "image_url": image_url, "reviews": []}
        clist.update_one({"category": category}, {"$set": {"products": new_plist}})
        
    def add_review(self, category, pname, review):
        clist = dbase[self.collection]
        doc = clist.find_one({"category": category})
        products_dict = doc["products"]
        product = products_dict.get(pname, {})
        reviews = product.get("reviews", [])
        reviews.append(review)
        product["reviews"] = reviews
        products_dict[pname] = product
        clist.update_one({"category": category}, {"$set": {"products": products_dict}})
        
    def rm_product(self, category, pname):
        clist = dbase[self.collection]
        plist = clist.find_one({"category": category})
        new_plist = plist["products"]
        if pname in new_plist:
            del new_plist[pname]
            clist.update_one({"category": category}, {"$set": {"products": new_plist}})
        
    def all_product_names(self, category):
        clist = dbase[self.collection]
        plist = clist.find_one({"category": category})
        return list(plist["products"].keys())     
        
    def all_product(self, category):
        clist = dbase[self.collection]
        plist = clist.find_one({"category": category})
        return plist["products"]     
        
    def add_accounts(self, category, pname, accs):    
        clist = dbase[self.collection]
        plist = clist.find_one({"category": category})
        products_dict = plist["products"]
        current_accounts = products_dict[pname]["accounts"]
        count = 0
        for x in accs:
            current_accounts.append(x)
            count += 1
        price = products_dict[pname]["price"]
        quantity = products_dict[pname]["quantity"] + count        
        products_dict[pname] = {"price": price, "quantity": quantity, "accounts": current_accounts, "image_url": products_dict[pname].get("image_url", "")}
        clist.update_one({"category": category}, {"$set": {"products": products_dict}}) 
          
    def rm_accounts(self, category, pname, accs):    
        clist = dbase[self.collection]
        plist = clist.find_one({"category": category})
        products_dict = plist["products"]
        current_accounts = products_dict[pname]["accounts"]
        count = 0
        for x in accs:
            try:
                current_accounts.remove(x)
                count += 1
            except Exception as e:
                raise e
        price = products_dict[pname]["price"]
        quantity = products_dict[pname]["quantity"] - count        
        products_dict[pname] = {"price": price, "quantity": quantity, "accounts": current_accounts, "image_url": products_dict[pname].get("image_url", "")}
        clist.update_one({"category": category}, {"$set": {"products": products_dict}})         
                
    def get(self, data):
        clist = dbase[self.collection]
        result = []
        if data:
            d = clist.find_one(data)
            if d:
                result.append(d)
            return result
        for x in clist.find():
            result.append(x)
        return result 
    
    def get_product(self, category, pname):
        clist = dbase[self.collection]
        d = clist.find_one({"category": category})
        return d["products"][pname]
    
    def delete(self, data):
        clist = dbase[self.collection]
        clist.delete_one(data)
    
    def get_all(self):
        clist = dbase[self.collection]
        return clist.find()
