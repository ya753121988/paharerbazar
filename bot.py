import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "paharer_bazar_mega_key_99"

# --- মংগোডিবি কানেকশন (এখানে আপনার কানেকশন স্ট্রিং দিন) ---
MONGO_URI = "mongodb+srv://YOUR_USER:YOUR_PASS@cluster0.mongodb.net/shop_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client['paharer_bazar_v3']
products_col = db['products']
categories_col = db['categories']
users_col = db['users']
orders_col = db['orders']

# --- HTML/CSS/JS (সম্পূর্ণ ডিজাইন এক স্ট্রিং-এ) ---
LAYOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paharer Bazar | খাগড়াছড়ির বিশুদ্ধ পণ্য</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Hind Siliguri', sans-serif; background-color: #f3f4f6; color: #333; }
        .discount-badge {
            background: #e11d48; color: white; border-radius: 50%;
            width: 45px; height: 45px; display: flex; align-items: center;
            justify-content: center; font-size: 10px; font-weight: bold;
            position: absolute; top: 12px; right: 12px; line-height: 1.1;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 10; animation: pulse 2s infinite;
        }
        @keyframes pulse { 0% {transform: scale(1);} 50% {transform: scale(1.05);} 100% {transform: scale(1);} }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #e5e7eb; z-index: 100; display: flex; justify-content: space-around; padding: 10px 0; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
        .tab-btn.active { border-bottom: 3px solid #f97316; color: #f97316; font-weight: bold; }
        .sidebar { transition: 0.3s; z-index: 200; }
        .nav-icon { font-size: 20px; margin-bottom: 2px; }
    </style>
</head>
<body class="pb-20">

    <!-- Top Info -->
    <div class="bg-orange-600 text-white text-center py-1.5 text-[11px] font-semibold tracking-wide">
        স্বাগতম || খাগড়াছড়ি থেকে সারা বাংলাদেশে ক্যাশ অন ডেলিভারি
    </div>

    <!-- Main Header -->
    <header class="bg-white sticky top-0 z-50 shadow-sm">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <button onclick="toggleMenu()" class="text-2xl">☰</button>
            <a href="/" class="text-2xl font-black text-orange-600">Paharer<span class="text-gray-800">Bazar</span></a>
            <div class="relative">
                <span class="text-2xl">🛒</span>
                <span class="absolute -top-1 -right-2 bg-orange-600 text-white text-[10px] rounded-full h-4 w-4 flex items-center justify-center">0</span>
            </div>
        </div>
        <div class="px-4 pb-3">
            <div class="relative">
                <input type="text" placeholder="Search Product..." class="w-full border border-gray-200 rounded-full py-2 px-4 text-sm focus:outline-none focus:border-orange-500">
                <button class="absolute right-3 top-2 text-gray-400">🔍</button>
            </div>
        </div>
    </header>

    <!-- Drawer Menu -->
    <div id="drawer" class="sidebar fixed top-0 left-0 h-full w-72 bg-white shadow-2xl transform -translate-x-full overflow-y-auto">
        <div class="p-5 border-b flex justify-between items-center bg-gray-50">
            <span class="font-bold text-lg">সব ক্যাটাগরি</span>
            <button onclick="toggleMenu()" class="text-3xl">&times;</button>
        </div>
        <ul class="p-4 space-y-1">
            {% for cat in categories %}
            <li><a href="/category/{{ cat.name }}" class="flex items-center gap-3 p-3 hover:bg-orange-50 rounded-lg border-b border-gray-50">
                <span>{{ cat.icon }}</span> {{ cat.name }}
            </a></li>
            {% endfor %}
            <hr class="my-4">
            {% if session.get('user') %}
                <li class="p-3 font-bold text-orange-600">স্বাগতম, {{ session['user'] }}</li>
                {% if session.get('role') == 'admin' %}
                    <li><a href="/admin" class="block p-3 text-red-600 font-bold">Admin Panel</a></li>
                {% endif %}
                <li><a href="/logout" class="block p-3 text-gray-600">Logout</a></li>
            {% else %}
                <li><a href="/login" class="block p-3 text-blue-600 font-bold">Login / Register</a></li>
            {% endif %}
        </ul>
    </div>

    <!-- Notifications -->
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="bg-green-500 text-white p-3 text-center text-sm">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <div class="container mx-auto p-4">
    {% if page == 'home' %}
        <!-- Banner -->
        <div class="mb-6">
            <img src="https://i.ibb.co/L5Bf85m/banner.jpg" class="w-full rounded-xl shadow-md">
        </div>

        <!-- Product Grid -->
        <h2 class="text-center font-bold text-lg mb-5 flex items-center justify-center gap-2">
            <span class="h-px w-10 bg-gray-300"></span> All Products <span class="h-px w-10 bg-gray-300"></span>
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            {% for p in products %}
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 relative overflow-hidden flex flex-col">
                {% if p.discount %}
                <div class="discount-badge">{{ p.discount }}%<br>ছাড়</div>
                {% endif %}
                <a href="/product/{{ p._id }}">
                    <img src="{{ p.image }}" class="w-full h-44 object-cover">
                </a>
                <div class="p-3 flex-grow">
                    <a href="/product/{{ p._id }}">
                        <h3 class="text-[13px] font-semibold leading-tight h-9 overflow-hidden text-gray-700 hover:text-orange-600 transition">{{ p.name }}</h3>
                    </a>
                    <div class="mt-2 flex items-center gap-2">
                        <span class="text-gray-400 line-through text-[11px]">৳{{ p.price }}</span>
                        <span class="text-orange-600 font-bold text-sm">৳{{ p.sale_price }}</span>
                    </div>
                </div>
                <a href="/product/{{ p._id }}" class="bg-orange-500 text-white text-center py-2.5 text-xs font-bold uppercase tracking-wider">অর্ডার করুন</a>
            </div>
            {% endfor %}
        </div>

    {% elif page == 'product_detail' %}
        <!-- Details Page -->
        <div class="bg-white rounded-2xl shadow-sm p-4">
            <nav class="text-[10px] text-gray-400 mb-3">Home / {{ p.category }} / {{ p.name }}</nav>
            <div class="relative">
                {% if p.discount %} <div class="discount-badge">{{ p.discount }}%<br>ছাড়</div> {% endif %}
                <img src="{{ p.image }}" class="w-full max-h-72 object-contain mx-auto mb-4">
            </div>
            <h1 class="text-xl font-bold text-gray-800 leading-tight">{{ p.name }}</h1>
            <div class="text-2xl font-black text-orange-600 mt-2">৳ {{ p.sale_price }}</div>
            
            <div class="inline-flex items-center bg-emerald-600 text-white text-[10px] px-3 py-1 rounded mt-3 font-bold uppercase">
                প্রোডাক্ট কোড : {{ p.code }}
            </div>

            <div class="mt-5">
                <label class="text-xs font-bold text-gray-500 uppercase block mb-2">Size / Weight</label>
                <button class="border-2 border-orange-500 px-4 py-1.5 text-xs rounded-lg bg-orange-50 font-bold">{{ p.weight }} - ৳{{ p.sale_price }}</button>
            </div>

            <div class="mt-6 flex gap-3">
                <div class="flex border rounded-lg overflow-hidden bg-gray-50">
                    <button class="px-4 py-2 hover:bg-gray-200">-</button>
                    <input type="text" value="1" class="w-10 text-center bg-transparent font-bold" readonly>
                    <button class="px-4 py-2 hover:bg-gray-200">+</button>
                </div>
                <button class="flex-1 bg-emerald-600 text-white py-3 rounded-lg font-bold text-sm shadow-lg shadow-emerald-100">কার্টে যোগ করুন</button>
            </div>

            <a href="/checkout/{{ p._id }}" class="block w-full bg-orange-500 text-white text-center py-4 rounded-lg font-black mt-4 shadow-lg shadow-orange-100 text-lg">অর্ডার করুন</a>

            <div class="grid grid-cols-2 gap-2 mt-4">
                <a href="tel:01511820222" class="bg-gray-900 text-white py-2.5 rounded-lg text-center text-xs font-bold">📞 কল করুন</a>
                <a href="https://wa.me/8801511820222" class="bg-emerald-500 text-white py-2.5 rounded-lg text-center text-xs font-bold">💬 Whatsapp</a>
            </div>

            <!-- Delivery Info Table -->
            <div class="mt-8 border border-dashed border-gray-300 rounded-xl overflow-hidden">
                <div class="bg-gray-50 p-3 text-xs font-bold border-b">কুরিয়ার ডেলিভারি খরচ</div>
                <table class="w-full text-xs">
                    <tr class="border-b"><td class="p-3 text-gray-600">সর্বমোট ১ কেজি পর্যন্ত</td><td class="p-3 font-bold text-right">৳ ১৩০</td></tr>
                    <tr class="border-b"><td class="p-3 text-gray-600">সর্বমোট ২ কেজি পর্যন্ত</td><td class="p-3 font-bold text-right">৳ ১৫০</td></tr>
                    <tr><td class="p-3 text-gray-600">সর্বমোট ৫ কেজি পর্যন্ত</td><td class="p-3 font-bold text-right">৳ ২১০</td></tr>
                </table>
            </div>

            <!-- Tabs System -->
            <div class="mt-10">
                <div class="flex border-b text-sm">
                    <button onclick="setTab('desc')" id="t-desc" class="tab-btn active px-5 py-3">Description</button>
                    <button onclick="setTab('pol')" id="t-pol" class="tab-btn px-5 py-3">Policy</button>
                    <button onclick="setTab('rev')" id="t-rev" class="tab-btn px-5 py-3">Reviews</button>
                </div>
                <div id="c-desc" class="py-6 text-sm text-gray-600 leading-relaxed space-y-2">
                    <h3 class="font-bold text-gray-800 text-base mb-3">পণ্যের বিস্তারিত:</h3>
                    {{ p.description | safe }}
                </div>
                <div id="c-pol" class="hidden py-6 text-sm text-gray-600">
                    <h3 class="font-bold text-gray-800 text-base mb-3">অর্ডার ও ডেলিভারি নিয়ম:</h3>
                    {{ p.order_policy | safe }}
                </div>
                <div id="c-rev" class="hidden py-12 text-center text-gray-400">
                    <div class="text-4xl mb-2">📝</div>
                    <p>এখনো কোনো রিভিউ দেওয়া হয়নি।</p>
                </div>
            </div>
        </div>

    {% elif page == 'checkout' %}
        <!-- Checkout Page -->
        <div class="max-w-md mx-auto bg-white p-6 rounded-2xl shadow-sm">
            <h2 class="text-xl font-bold mb-5 border-b pb-3">অর্ডার কনফার্ম করুন</h2>
            <div class="flex gap-4 mb-6 bg-gray-50 p-3 rounded-lg">
                <img src="{{ p.image }}" class="w-16 h-16 rounded object-cover">
                <div>
                    <p class="text-sm font-bold">{{ p.name }}</p>
                    <p class="text-orange-600 font-bold">৳ {{ p.sale_price }}</p>
                </div>
            </div>
            <form action="/place-order" method="POST" class="space-y-4">
                <input type="hidden" name="p_id" value="{{ p._id }}">
                <div>
                    <label class="text-xs font-bold text-gray-500">আপনার নাম *</label>
                    <input type="text" name="name" class="w-full border p-3 rounded-lg mt-1" required>
                </div>
                <div>
                    <label class="text-xs font-bold text-gray-500">মোবাইল নাম্বার *</label>
                    <input type="text" name="phone" class="w-full border p-3 rounded-lg mt-1" required>
                </div>
                <div>
                    <label class="text-xs font-bold text-gray-500">পূর্ণ ঠিকানা *</label>
                    <textarea name="address" class="w-full border p-3 rounded-lg mt-1 h-20" required></textarea>
                </div>
                <div>
                    <label class="text-xs font-bold text-gray-500">পেমেন্ট মেথড</label>
                    <select name="payment" class="w-full border p-3 rounded-lg mt-1 bg-white">
                        <option value="Cash on Delivery">ক্যাশ অন ডেলিভারি (COD)</option>
                        <option value="Bkash">বিকাশ (Bkash)</option>
                        <option value="Nagad">নগদ (Nagad)</option>
                        <option value="Rocket">রকেট / উপায়</option>
                    </select>
                </div>
                <button class="w-full bg-orange-600 text-white py-4 rounded-xl font-black text-lg shadow-lg">অর্ডার প্লেস করুন</button>
            </form>
        </div>

    {% elif page == 'admin' %}
        <!-- Admin Panel -->
        <div class="max-w-2xl mx-auto space-y-8">
            <div class="bg-white p-6 rounded-xl shadow-sm border">
                <h2 class="font-bold text-lg mb-4 text-emerald-600">নতুন ক্যাটাগরি যোগ করুন</h2>
                <form action="/admin/add-cat" method="POST" class="flex gap-3">
                    <input type="text" name="icon" placeholder="Emoji (🥭)" class="w-20 border p-3 rounded-lg text-center">
                    <input type="text" name="name" placeholder="ক্যাটাগরি নাম" class="flex-1 border p-3 rounded-lg">
                    <button class="bg-emerald-600 text-white px-6 rounded-lg font-bold">Add</button>
                </form>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-sm border">
                <h2 class="font-bold text-lg mb-4 text-orange-600">নতুন প্রোডাক্ট আপলোড</h2>
                <form action="/admin/add-product" method="POST" class="space-y-4 text-sm">
                    <input type="text" name="name" placeholder="প্রোডাক্টের নাম" class="w-full border p-3 rounded-lg" required>
                    <div class="grid grid-cols-2 gap-3">
                        <input type="text" name="img" placeholder="Image URL (Imgur link)" class="border p-3 rounded-lg">
                        <select name="cat" class="border p-3 rounded-lg bg-white">
                            {% for c in categories %} <option>{{ c.name }}</option> {% endfor %}
                        </select>
                    </div>
                    <div class="grid grid-cols-3 gap-3">
                        <input type="number" name="price" placeholder="মূল দাম" class="border p-3 rounded-lg">
                        <input type="number" name="disc" placeholder="ডিস্কাউন্ট %" class="border p-3 rounded-lg">
                        <input type="text" name="code" placeholder="কোড (যেমন: P-101)" class="border p-3 rounded-lg">
                    </div>
                    <input type="text" name="weight" placeholder="ওজন (যেমন: ৫০০ গ্রাম)" class="w-full border p-3 rounded-lg">
                    <textarea name="desc" placeholder="পণ্যের বিস্তারিত (পয়েন্ট আকারে লিখুন)" class="w-full border p-3 rounded-lg h-32"></textarea>
                    <textarea name="pol" placeholder="অর্ডার করার নিয়ম" class="w-full border p-3 rounded-lg h-24"></textarea>
                    <button class="w-full bg-orange-600 text-white py-4 rounded-xl font-bold text-lg">পণ্যটি পাবলিশ করুন</button>
                </form>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-sm border">
                <h2 class="font-bold mb-4">সব অর্ডার তালিকা</h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <tr class="bg-gray-100"><th class="p-2">কাস্টমার</th><th class="p-2">পণ্য</th><th class="p-2">ঠিকানা</th><th class="p-2">স্ট্যাটাস</th></tr>
                        {% for o in orders %}
                        <tr class="border-b">
                            <td class="p-2 font-bold">{{ o.name }}<br><span class="text-blue-600">{{ o.phone }}</span></td>
                            <td class="p-2">ID: {{ o.p_id }}<br>{{ o.payment }}</td>
                            <td class="p-2 text-gray-500">{{ o.address }}</td>
                            <td class="p-2"><span class="bg-yellow-100 text-yellow-700 px-2 py-1 rounded">Pending</span></td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
            </div>
        </div>

    {% elif page == 'login' %}
        <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-sm text-center">
            <h2 class="text-2xl font-bold mb-6">লগইন করুন</h2>
            <form action="/auth/login" method="POST" class="space-y-4">
                <input type="text" name="user" placeholder="Username" class="w-full border p-3 rounded-lg" required>
                <input type="password" name="pass" placeholder="Password" class="w-full border p-3 rounded-lg" required>
                <button class="w-full bg-orange-600 text-white py-3 rounded-lg font-bold">Login</button>
            </form>
            <p class="mt-4 text-sm text-gray-500">অ্যাকাউন্ট নেই? <a href="/register" class="text-orange-600 font-bold">রেজিস্ট্রেশন করুন</a></p>
        </div>

    {% elif page == 'register' %}
        <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-sm text-center">
            <h2 class="text-2xl font-bold mb-6">নতুন অ্যাকাউন্ট</h2>
            <form action="/auth/register" method="POST" class="space-y-4">
                <input type="text" name="user" placeholder="Username" class="w-full border p-3 rounded-lg" required>
                <input type="password" name="pass" placeholder="Password" class="w-full border p-3 rounded-lg" required>
                <button class="w-full bg-blue-600 text-white py-3 rounded-lg font-bold">Register Now</button>
            </form>
        </div>
    {% endif %}
    </div>

    <!-- Footer -->
    <footer class="bg-[#f0f3f0] p-10 mt-10 text-center">
        <div class="text-2xl font-black text-orange-600">Paharer Bazar</div>
        <p class="text-xs text-gray-500 mt-2 leading-relaxed">Address: Muslimpara, Khagrachhari Sadar.<br>Hotline: +8801511820222</p>
        <div class="flex justify-center gap-4 my-6">
            <span class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs">f</span>
            <span class="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-xs">w</span>
            <span class="w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center text-xs">y</span>
        </div>
        <div class="grid grid-cols-2 gap-10 text-left max-w-sm mx-auto text-xs font-semibold text-gray-600 border-t border-gray-200 pt-6">
            <ul class="space-y-2">
                <li class="font-bold text-gray-800">Useful Links</li>
                <li>Contact Us</li><li>Delivery Rules</li><li>Return Policy</li>
            </ul>
            <ul class="space-y-2">
                <li class="font-bold text-gray-800">Company</li>
                <li>All Products</li><li>Terms & Cond.</li><li>Privacy Policy</li>
            </ul>
        </div>
        <div class="bg-orange-600 text-white p-4 text-[10px] mt-10 -mx-10 -mb-10">
            Copyright © 2026 Paharer Bazar. All rights reserved | Designed by Khagrachhari Plus
        </div>
    </footer>

    <!-- Bottom Navigation Bar -->
    <nav class="bottom-nav">
        <button onclick="toggleMenu()" class="flex flex-col items-center text-[10px] text-gray-500">
            <span class="nav-icon">☰</span><span>Category</span>
        </button>
        <a href="https://wa.me/8801511820222" class="flex flex-col items-center text-[10px] text-gray-500">
            <span class="nav-icon text-emerald-500">💬</span><span>Whatsapp</span>
        </a>
        <a href="/" class="flex flex-col items-center -mt-8">
            <div class="bg-orange-500 text-white p-3.5 rounded-full shadow-lg text-xl">🏠</div>
            <span class="text-[10px] mt-1 font-bold text-orange-600 uppercase">Home</span>
        </a>
        <div class="flex flex-col items-center text-[10px] text-gray-500 relative">
            <span class="nav-icon">🛒</span><span>Cart (0)</span>
        </div>
        <a href="/login" class="flex flex-col items-center text-[10px] text-gray-500">
            <span class="nav-icon">👤</span><span>Login</span>
        </a>
    </nav>

    <script>
        function toggleMenu() { document.getElementById('drawer').classList.toggle('-translate-x-full'); }
        function setTab(name) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('[id^="c-"]').forEach(c => c.classList.add('hidden'));
            document.getElementById('t-'+name).classList.add('active');
            document.getElementById('c-'+name).classList.remove('hidden');
        }
    </script>
</body>
</html>
"""

# --- রাউটস ও লজিক ---

@app.route('/')
def index():
    cats = list(categories_col.find())
    prods = list(products_col.find())
    return render_template_string(LAYOUT_TEMPLATE, page='home', products=prods, categories=cats)

@app.route('/category/<name>')
def category_view(name):
    cats = list(categories_col.find())
    prods = list(products_col.find({"category": name}))
    return render_template_string(LAYOUT_TEMPLATE, page='home', products=prods, categories=cats)

@app.route('/product/<id>')
def product_detail(id):
    cats = list(categories_col.find())
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(LAYOUT_TEMPLATE, page='product_detail', p=p, categories=cats)

@app.route('/checkout/<id>')
def checkout(id):
    cats = list(categories_col.find())
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(LAYOUT_TEMPLATE, page='checkout', p=p, categories=cats)

@app.route('/place-order', methods=['POST'])
def place_order():
    order = {
        "p_id": request.form['p_id'],
        "name": request.form['name'],
        "phone": request.form['phone'],
        "address": request.form['address'],
        "payment": request.form['payment'],
        "date": datetime.now()
    }
    orders_col.insert_one(order)
    flash("অর্ডারটি সফল হয়েছে! আমরা আপনার সাথে শীঘ্রই যোগাযোগ করব।")
    return redirect('/')

@app.route('/login')
def login_page(): return render_template_string(LAYOUT_TEMPLATE, page='login', categories=list(categories_col.find()))

@app.route('/register')
def reg_page(): return render_template_string(LAYOUT_TEMPLATE, page='register', categories=list(categories_col.find()))

@app.route('/auth/register', methods=['POST'])
def auth_reg():
    users_col.insert_one({"user": request.form['user'], "pass": request.form['pass'], "role": "user"})
    flash("রেজিস্ট্রেশন সফল! লগইন করুন।")
    return redirect('/login')

@app.route('/auth/login', methods=['POST'])
def auth_login():
    u = users_col.find_one({"user": request.form['user'], "pass": request.form['pass']})
    if u:
        session['user'] = u['user']
        session['role'] = u.get('role', 'user')
        return redirect('/')
    flash("ভুল ইউজারনেম বা পাসওয়ার্ড!")
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- অ্যাডমিন রাউটস ---
@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return "এক্সেস ডিনাইড!"
    cats = list(categories_col.find())
    ords = list(orders_col.find().sort("date", -1))
    return render_template_string(LAYOUT_TEMPLATE, page='admin', categories=cats, orders=ords)

@app.route('/admin/add-cat', methods=['POST'])
def add_cat():
    categories_col.insert_one({"name": request.form['name'], "icon": request.form['icon']})
    return redirect('/admin')

@app.route('/admin/add-product', methods=['POST'])
def add_product():
    price = float(request.form['price'])
    disc = float(request.form['disc'] or 0)
    sale = int(price - (price * disc / 100))
    products_col.insert_one({
        "name": request.form['name'], "image": request.form['img'],
        "category": request.form['cat'], "price": price, "discount": disc,
        "sale_price": sale, "code": request.form['code'], "weight": request.form['weight'],
        "description": request.form['desc'].replace('\\n', '<br>'),
        "order_policy": request.form['pol'].replace('\\n', '<br>')
    })
    flash("পণ্য সফলভাবে যুক্ত হয়েছে!")
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
