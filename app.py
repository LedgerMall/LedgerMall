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


import time
from urllib.parse import urlparse, urljoin
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
import pycoinpayments

from config import config

from db import *  

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

from datetime import datetime

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    try:
        return datetime.fromtimestamp(float(value)).strftime(format)
    except Exception:
        return value

login_manager = LoginManager(app)
login_manager.login_view = "login"
bcrypt = Bcrypt(app)

users_db = Users(config.USERS_DB)
products_db = Products(config.PRODUCTS_DB)

crypto_client = pycoinpayments.CoinPayments(
    private_key=config.CP_PRIVATE_KEY,
    public_key=config.CP_PUBLIC_KEY,
)

class User(UserMixin):
    def __init__(self, username, password, balance=0, is_admin=False):
        self.id = username
        self.username = username
        self.password = password
        self.balance = balance
        self.is_admin = is_admin

    @staticmethod
    def get(username):
        data = users_db.get_by_username(username)
        if data:
            return User(username=data["username"],
                        password=data["password"],
                        balance=data.get("balance", 0),
                        is_admin=data.get("is_admin", False))
        return None

    @staticmethod
    def get_by_username(username):
        for u in users_db.get_all():
            if u.get("username") == username:
                return User(username=u["username"],
                            password=u["password"],
                            balance=u.get("balance", 0),
                            is_admin=u.get("is_admin", False))
        return None

@login_manager.user_loader
def load_user(username):
    return User.get(username)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users_db.get_by_username(username):
            flash("Username already exists!")
            return redirect(url_for("register"))
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        users_db.new(username, password=hashed, balance=0)
        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        next_page = request.form.get("next")
        if not next_page or next_page == "None":
            next_page = url_for("index")
        user = User.get_by_username(username)
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!")
            if not is_safe_url(next_page):
                next_page = url_for("index")
            return redirect(next_page)
        flash("Invalid username or password.")
        return redirect(url_for("login"))
    next_page = request.args.get("next")
    if next_page == "None":
        next_page = ""
    return render_template("login.html", next=next_page)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    cats = products_db.all_category()
    cats = products_db.all_category()
    return render_template("index.html", categories=cats)

@app.route("/shop/<category>")
@login_required
def shop_category(category):
    prod = products_db.all_product(category)
    return render_template("shop_category.html", category=category, products=prod)

@app.route("/product/<category>/<product_name>", methods=["GET", "POST"])
@login_required
def product_detail(category, product_name):
    prod = products_db.get_product(category, product_name)
    if not prod:
        flash("Product not found")
        return redirect(url_for("shop_category", category=category))
    if request.method == "POST":
        try:
            quantity = int(request.form["quantity"])
        except ValueError:
            flash("Invalid quantity")
            return redirect(url_for("product_detail", category=category, product_name=product_name))
        if quantity < 1 or quantity > prod["quantity"]:
            flash(f"Quantity must be between 1 and {prod['quantity']}")
            return redirect(url_for("product_detail", category=category, product_name=product_name))
        cart = session.get("cart", [])
        cart.append({
            "category": category,
            "product": product_name,
            "quantity": quantity,
            "price": prod["price"]
        })
        session["cart"] = cart
        flash("Product added to cart")
        return redirect(url_for("cart"))
    return render_template("product_detail.html", product=prod, category=category, product_name=product_name)

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] * item["quantity"] for item in cart)
    if request.method == "POST":
        if total > current_user.balance:
            flash("Insufficient balance, please add funds.")
            return redirect(url_for("wallet"))
        users_db.reduce_balance(current_user.id, total)
        purchased_accounts = []
        for item in cart:
            prod = products_db.get_product(item["category"], item["product"])
            accounts = prod["accounts"][:item["quantity"]]
            purchased_accounts.extend(accounts)
            products_db.rm_accounts(item["category"], item["product"], accounts)
        session["cart"] = []
        flash("Purchase successful! Your products will be delivered below.")
        return render_template("purchase_success.html", accounts=purchased_accounts)
    return render_template("cart.html", cart=cart, total=total)

@app.route("/cart/remove/<int:index>", methods=["POST"])
@login_required
def remove_cart_item(index):
    cart = session.get("cart", [])
    if 0 <= index < len(cart):
        removed_item = cart.pop(index)
        session["cart"] = cart
        flash(f"Removed {removed_item['product']} from your cart.")
    else:
        flash("Invalid item index.")
    return redirect(url_for("cart"))

@app.route("/support")
@login_required
def support():
    return render_template("support.html")

@app.route("/admin/support")
@login_required
def admin_support():
    if not current_user.is_admin:
        abort(403)
    return render_template("admin_support.html", support_chats=support_messages)

@app.route("/admin/reply/<username>", methods=["POST"])
@login_required
def admin_reply(username):
    if not current_user.is_admin:
        abort(403)
    reply_text = request.form.get("reply")
    if reply_text:
        if username not in support_messages:
            support_messages[username] = []
        support_messages[username].append({
            "username": current_user.id,
            "message": reply_text,
            "timestamp": time.time()
        })
        flash(f"Reply sent to {username}!")
    return redirect(url_for("admin_support"))

@app.route("/rules")
@login_required
def rules():
    return render_template("rules.html")

@app.route("/profile")
@login_required
def profile():
    user = users_db.get_by_username(current_user.id)
    history = user.get("history", [])
    return render_template("profile.html", user=user, history=history)

@app.route("/product/<category>/<product_name>/review", methods=["POST"])
@login_required
def submit_review(category, product_name):
    rating = request.form.get("rating")
    review_text = request.form.get("review")
    if not rating or not review_text:
        flash("Please provide both rating and review text.")
        return redirect(url_for("product_detail", category=category, product_name=product_name))
    try:
        rating = int(rating)
    except ValueError:
        flash("Invalid rating value.")
        return redirect(url_for("product_detail", category=category, product_name=product_name))
    review = {
        "username": current_user.id,
        "rating": rating,
        "review": review_text,
        "timestamp": time.time()
    }
    products_db.add_review(category, product_name, review)
    flash("Review submitted successfully!")
    return redirect(url_for("product_detail", category=category, product_name=product_name))

@app.route("/admin/analytics")
@login_required
def admin_analytics():
    if not current_user.is_admin:
        abort(403)
    orders = []
    for user in users_db.get_all():
        orders.extend(user.get("history", []))
    total_orders = len(orders)
    total_revenue = sum(item["price"] * item["quantity"]
                        for order in orders
                        for item in order.get("items", []))
    avg_order = total_revenue / total_orders if total_orders > 0 else 0
    return render_template("admin_analytics.html",
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           avg_order=avg_order)

@app.route("/search")
@login_required
def search():
    query = request.args.get("q", "").lower()
    min_price = request.args.get("min", type=int)
    max_price = request.args.get("max", type=int)
    results = []
    for cat in products_db.all_category():
        cat_name = cat["category"]
        for pname, prod in cat["products"].items():
            if query in pname.lower():
                if min_price is not None and prod["price"] < min_price:
                    continue
                if max_price is not None and prod["price"] > max_price:
                    continue
                results.append({
                    "category": cat_name,
                    "product_name": pname,
                    "price": prod["price"],
                    "quantity": prod["quantity"],
                    "image_url": prod.get("image_url", "")
                })
    return render_template("search.html", results=results, query=query)

support_messages = {}

@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    user_id = current_user.id
    if user_id not in support_messages:
        support_messages[user_id] = []

    if request.method == "POST":
        message = request.form.get("message")
        if message:
            support_messages[user_id].append({
                "username": current_user.id,
                "message": message,
                "timestamp": time.time()
            })
            flash("Message sent!")
        return redirect(url_for("chat"))
    return render_template("chat.html", messages=support_messages[user_id])

@app.route("/addmoney", methods=["GET", "POST"])
@login_required
def addmoney():
    if request.method == "POST":
        try:
            amt = int(request.form["amount"])
        except ValueError:
            flash("Invalid amount")
            return redirect(url_for("addmoney"))
        if amt < 20 or amt > 10000:
            flash("Amount must be between 20 and 10,000 USD")
            return redirect(url_for("addmoney"))

        coin = request.form.get("coin")
        coin_mapping = config.COIN_MAPPING
        selected_coin = coin_mapping.get(coin)
        if not selected_coin:
            flash("Invalid coin selection")
            return redirect(url_for("addmoney"))
        try:
            txn = crypto_client.create_transaction({
                'amount': amt,
                'currency1': 'USD',
                'currency2': selected_coin["currency2"],
                'buyer_email': config.BUYER_EMAIL,
                'address': selected_coin["address"],
            })
        except Exception as e:
            print("Crypto API error:", e)
            flash("Payment API connection failed, try again later.")
            return redirect(url_for("wallet"))
        if txn.get("error") != "ok":
            flash("Payment API error, please contact support.")
            return redirect(url_for("wallet"))
        session["current_txn"] = txn
        session["deposit_amount"] = amt
        session["coin"] = coin
        session["qr_url"] = txn.get("qrcode_url", "")
        return render_template("payment.html", txn=txn, tx_id=txn["txn_id"], amt=amt, coin=coin, qr_url=txn.get("qrcode_url", ""))
    return render_template("addmoney.html")

@app.route("/payment/refresh")
@login_required
def payment_refresh():
    txn = session.get("current_txn")
    coin = session.get("coin")
    qr_url = session.get("qr_url", "")
    if not txn:
        flash("No active transaction.")
        return redirect(url_for("wallet"))
    txid = txn["txn_id"]
    amt = session.get("deposit_amount", 0)
    txn_info = crypto_client.get_tx_info({'txid': txid})
    status_text = txn_info.get("status_text", "Unknown")
    if txn_info.get('status', 0) >= 1 or current_user.is_admin:
        users_db.update_balance(current_user.id, int(amt))
        flash("Your top-up is successful!")
        session.pop("current_txn", None)
        session.pop("deposit_amount", None)
        session.pop("coin", None)
        session.pop("qr_url", None)
        return redirect(url_for("wallet"))
    else:
        exp = txn_info.get("time_expires", time.time())
        now = time.time()
        remaining = exp - now
        if remaining < 0:
            time_msg = "Payment expired"
        else:
            hrs = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            time_msg = f"{hrs} hours {mins} mins remaining"
        return render_template("payment.html", txn=txn_info, tx_id=txid, amt=amt, status_text=status_text, time_msg=time_msg, coin=coin, qr_url=qr_url)

@app.route("/wallet")
@login_required
def wallet():
    user = users_db.get_by_username(current_user.id)
    return render_template("wallet.html", user=user)

@app.route("/wallet")
@login_required
def wallet_view():
    user = users_db.get_by_username(current_user.id)
    return render_template("wallet.html", user=user)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.get_by_username(username)
        if user and user.is_admin and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Welcome, admin!")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.")
        return redirect(url_for("admin_login"))
    return render_template("admin_login.html")

@app.route("/admin/logout")
@login_required
def admin_logout():
    if not current_user.is_admin:
        abort(403)
    logout_user()
    flash("Admin logged out")
    return redirect(url_for("login"))

@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    return render_template("admin_dashboard.html")

@app.route("/admin/categories")
@login_required
def admin_categories():
    if not current_user.is_admin:
        abort(403)
    cats = products_db.all_category()
    return render_template("admin_categories.html", categories=cats)

@app.route("/admin/addcategory", methods=["GET", "POST"])
@login_required
def admin_addcategory():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        cat = request.form["category"]
        image_url = request.form.get("image_url", "").strip()
        products_db.new_category(cat, image_url)
        flash(f"Added category: {cat}")
        return redirect(url_for("admin_categories"))
    return render_template("admin_addcategory.html")

@app.route("/admin/rmcategory", methods=["GET", "POST"])
@login_required
def admin_rmcategory():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        cat = request.form["category"]
        products_db.rm_category(cat)
        flash(f"Removed category: {cat}")
        return redirect(url_for("admin_categories"))
    cats = products_db.all_category()
    return render_template("admin_rmcategory.html", categories=cats)

@app.route("/admin/addproduct", methods=["GET", "POST"])
@login_required
def admin_addproduct():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        category = request.form["category"]
        product_name = request.form["product_name"]
        try:
            price = int(request.form["price"])
        except ValueError:
            flash("Invalid price")
            return redirect(url_for("admin_addproduct"))
        image_url = request.form.get("image_url", "").strip()
        products_db.new_product(category, product_name, price, image_url)
        flash(f"Added product: {product_name} in category {category}")
        return redirect(url_for("admin_dashboard"))
    cats = list(products_db.all_category())
    return render_template("admin_addproduct.html", categories=cats)

@app.route("/admin/rmproduct", methods=["GET", "POST"])
@login_required
def admin_rmproduct():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        category = request.form["category"]
        product_name = request.form["product_name"]
        products_db.rm_product(category, product_name)
        flash(f"Removed product: {product_name} from category {category}")
        return redirect(url_for("admin_dashboard"))
    cats = products_db.all_category()
    return render_template("admin_rmproduct.html", categories=cats)

@app.route("/admin/addaccounts", methods=["GET", "POST"])
@login_required
def admin_addaccounts():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        category = request.form["category"]
        product_name = request.form["product_name"]
        accounts_text = request.form["accounts"]
        accounts = accounts_text.strip().splitlines()
        products_db.add_accounts(category, product_name, accounts)
        flash(f"Added {len(accounts)} accounts to product {product_name}")
        return redirect(url_for("admin_dashboard"))
    cats = products_db.all_category()
    return render_template("admin_addaccounts.html", categories=cats)

@app.route("/admin/stats")
@login_required
def admin_stats():
    if not current_user.is_admin:
        abort(403)
    total_users = len(list(users_db.get_all()))
    funds_added = 0
    return render_template("admin_stats.html", total_users=total_users, funds_added=funds_added)

if __name__ == "__main__":
    app.run(debug=config.DEBUG)
