import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "paharer_bazar_professional_99"

# --- মংগোডিবি কানেকশন (এখানে আপনার কানেকশন স্ট্রিং দিন) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['paharer_bazar_vfinal']
products_col = db['products']
categories_col = db['categories']
orders_col = db['orders']
users_col = db['users']

# --- সম্পূর্ণ ডিজাইন ও ফাংশনালিটি ---
MASTER_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paharer Bazar | পাহাড়ের বিশুদ্ধ পণ্য</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Hind Siliguri', sans-serif; background-color: #f7f8fa; }
        
        /* লাল গোল প্রিমিয়াম অটো পোস্টার (ডিস্কাউন্ট ব্যাজ) */
        .red-discount-badge {
            background: linear-gradient(145deg, #ff0000, #b30000);
            color: white; border-radius: 50%; width: 52px; height: 52px;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 800; position: absolute;
            top: 12px; right: 12px; z-index: 30; line-height: 1.2;
            text-align: center; border: 2px solid #fff;
            box-shadow: 0 4px 10px rgba(255,0,0,0.4);
            animation: bounce 2s infinite;
        }
        @keyframes bounce { 0%, 100% {transform: translateY(0);} 50% {transform: translateY(-5px);} }

        /* হেডার ও লোগো ডিজাইন */
        .logo-orange { color: #f97316; }
        .logo-dark { color: #1f2937; }

        /* মেনু ডিজাইন */
        .sidebar-menu { transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        .sidebar-hidden { transform: translateX(-100%); }

        /* বটম ন্যাভ */
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #eee; 
                      z-index: 100; display: flex; justify-content: space-around; padding: 8px 0; box-shadow: 0 -4px 15px rgba(0,0,0,0.05); }
        .nav-item { display: flex; flex-direction: column; align-items: center; color: #666; font-size: 11px; font-weight: 600; }
        .home-circle { background: #f97316; color: white; padding: 14px; border-radius: 50%; margin-top: -38px; border: 5px solid white; box-shadow: 0 4px 12px rgba(249,115,22,0.3); }

        .tab-btn.active { border-bottom: 3px solid #f97316; color: #f97316; font-weight: bold; }
    </style>
</head>
<body class="pb-24">

    <!-- Top Announcement -->
    <div class="bg-[#f97316] text-white text-center py-2 text-[12px] font-bold tracking-tight">
        স্বাগতম || আমরা খাগড়াছড়ি হতে সারা বাংলাদেশে ক্যাশ অন ডেলিভারি দেই
    </div>

    <!-- Main Header -->
    <header class="bg-white sticky top-0 z-50 shadow-sm px-4 py-3 flex justify-between items-center">
        <button onclick="toggleSidebar()" class="text-2xl text-gray-800">☰</button>
        <a href="/" class="text-2xl font-black flex items-center">
            <span class="logo-orange">Paharer</span><span class="logo-dark ml-1">Bazar</span>
        </a>
        <div class="relative">
            <span class="text-2xl">🛒</span>
            <span class="absolute -top-2 -right-2 bg-orange-600 text-white text-[10px] rounded-full h-5 w-5 flex items-center justify-center font-bold">0</span>
        </div>
    </header>

    <!-- Search Section -->
    <div class="bg-white px-4 pb-3 shadow-sm">
        <div class="relative max-w-2xl mx-auto">
            <input type="text" placeholder="Search Product..." class="w-full bg-[#f3f4f6] border-none rounded-lg py-2.5 px-5 text-sm outline-none focus:ring-2 focus:ring-orange-400">
            <button class="absolute right-3 top-2.5 text-gray-500">🔍</button>
        </div>
    </div>

    <!-- Side Menu (হুবহু স্ক্রিনশটের মতো) -->
    <div id="sidebar" class="sidebar-menu sidebar-hidden fixed top-0 left-0 h-full w-72 bg-white shadow-2xl z-[100] overflow-y-auto">
        <div class="p-5 border-b flex justify-between items-center bg-gray-50">
            <div class="font-bold text-xl flex items-center gap-2">
                <span class="logo-orange">Paharer</span><span class="logo-dark">Bazar</span>
            </div>
            <button onclick="toggleSidebar()" class="text-3xl">&times;</button>
        </div>
        <ul class="p-4 space-y-1">
            <li><a href="/category/আচার (Pickle)" class="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg border-b border-gray-50 text-gray-700">🥣 আচার (Pickle)</a></li>
            <li><a href="/category/মধু (Honey)" class="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg border-b border-gray-50 text-gray-700">🍯 মধু (Honey)</a></li>
            <li><a href="/category/হস্তশিল্প (Handicraft)" class="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg border-b border-gray-50 text-gray-700">🧺 হস্তশিল্প (Handicraft)</a></li>
            <li><a href="/category/শস্য (Crops)" class="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg border-b border-gray-50 text-gray-700">🌾 শস্য (Crops)</a></li>
            <li><a href="/category/ফল (Fruits)" class="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg border-b border-gray-50 text-gray-700">🍓 ফল (Fruits)</a></li>
            <li><a href="/category/মশলা (Masala)" class="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg border-b border-gray-50 text-gray-700">🌶️ মশলা (Masala)</a></li>
            <li><a href="/category/আম (Mango)" class="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg border-b border-gray-50 text-gray-700">🥭 আম (Mango)</a></li>
            
            <div class="mt-8 border-t pt-5">
                <li><a href="/admin" class="block p-3 text-red-600 font-bold bg-red-50 rounded-lg">⚙️ Admin Control</a></li>
                {% if session.get('user') %}
                    <li class="p-3 font-bold text-orange-600">👤 {{ session['user'] }}</li>
                    <li><a href="/logout" class="block p-3 text-gray-500">Logout</a></li>
                {% else %}
                    <li><a href="/login" class="block p-3 text-blue-600 font-bold">Login / Register</a></li>
                {% endif %}
            </div>
        </ul>
    </div>

    <!-- Main Content -->
    <div class="container mx-auto p-4 max-w-6xl">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                <div class="bg-green-500 text-white p-3 mb-4 rounded-lg shadow text-center text-sm font-bold">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% if page == 'home' %}
            <!-- Banner Slider Area -->
            <div class="mb-8 rounded-2xl overflow-hidden shadow-lg border-4 border-white">
                <img src="https://i.ibb.co/L5Bf85m/banner.jpg" class="w-full object-cover h-44 md:h-80">
            </div>

            <!-- Product Grid -->
            <h2 class="text-center font-bold text-xl mb-6 text-gray-800 uppercase tracking-widest border-b pb-2 max-w-xs mx-auto">All Products</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                {% for p in products %}
                <div class="bg-white rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden flex flex-col group">
                    {% if p.discount > 0 %}
                    <div class="red-discount-badge">{{ p.discount }}%<br>ছাড়</div>
                    {% endif %}
                    <a href="/product/{{ p._id }}"><img src="{{ p.image }}" class="w-full h-44 object-cover group-hover:scale-110 transition duration-500"></a>
                    <div class="p-3 flex-grow text-center">
                        <a href="/product/{{ p._id }}"><h3 class="text-[14px] font-bold h-10 overflow-hidden text-gray-800 leading-tight mb-2">{{ p.name }}</h3></a>
                        <div class="flex justify-center items-center gap-2">
                            <span class="text-gray-400 line-through text-[12px]">৳{{ p.price }}</span>
                            <span class="text-[#f97316] font-black text-lg">৳{{ p.sale_price }}</span>
                        </div>
                    </div>
                    <a href="/product/{{ p._id }}" class="bg-[#f97316] text-white text-center py-3 text-xs font-black uppercase tracking-tighter hover:bg-orange-600 transition">অর্ডার করুন</a>
                </div>
                {% endfor %}
            </div>

        {% elif page == 'product_detail' %}
            <!-- Product Detail Page -->
            <div class="bg-white rounded-3xl shadow-sm p-5 md:p-10 border border-gray-50">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div class="relative bg-gray-50 rounded-3xl p-6">
                        {% if p.discount > 0 %} <div class="red-discount-badge w-16 h-16 text-sm">{{ p.discount }}%<br>ছাড়</div> {% endif %}
                        <img src="{{ p.image }}" class="w-full max-h-96 object-contain mx-auto">
                    </div>
                    <div class="flex flex-col">
                        <nav class="text-[11px] text-gray-400 font-bold uppercase mb-2 tracking-widest">Home / {{ p.category }}</nav>
                        <h1 class="text-2xl font-black text-gray-900 mb-4">{{ p.name }}</h1>
                        <div class="text-4xl font-black text-[#f97316] mb-2">৳{{ p.sale_price }}</div>
                        <div class="text-gray-400 line-through font-bold mb-4">৳{{ p.price }}</div>
                        
                        <div class="inline-block bg-[#1a7a50] text-white text-[10px] px-4 py-1.5 rounded-sm font-bold uppercase w-fit mb-6">প্রোডাক্ট কোড : {{ p.code }}</div>

                        <div class="mb-6">
                            <label class="text-[11px] font-black text-gray-400 block mb-2 uppercase">Size / Weight:</label>
                            <div class="border-2 border-[#f97316] px-5 py-2.5 rounded-xl bg-orange-50 text-[#f97316] font-bold inline-block shadow-sm">📦 {{ p.weight }} - ৳{{ p.sale_price }}</div>
                        </div>

                        <div class="flex gap-4 mb-4">
                            <div class="flex border-2 border-gray-100 rounded-xl bg-gray-50 px-2 items-center">
                                <button class="px-3 py-2 text-xl font-bold">-</button>
                                <input type="text" value="1" class="w-10 text-center bg-transparent font-black" readonly>
                                <button class="px-3 py-2 text-xl font-bold">+</button>
                            </div>
                            <button class="flex-1 bg-[#1a7a50] text-white py-4 rounded-xl font-black uppercase text-sm shadow-md">কার্টে যোগ করুন</button>
                        </div>

                        <a href="/checkout/{{ p._id }}" class="block w-full bg-[#f97316] text-white text-center py-4 rounded-xl font-black text-xl shadow-lg hover:shadow-orange-200 transition">অর্ডার করুন</a>
                        
                        <div class="grid grid-cols-2 gap-3 mt-4">
                            <a href="tel:01511820222" class="bg-black text-white py-3 rounded-xl text-center text-xs font-bold flex items-center justify-center gap-2">📞 কল করুন</a>
                            <a href="https://wa.me/8801511820222" class="bg-[#25d366] text-white py-3 rounded-xl text-center text-xs font-bold flex items-center justify-center gap-2">💬 Whatsapp</a>
                        </div>
                    </div>
                </div>

                <!-- Delivery Table -->
                <div class="mt-12 border-2 border-dashed border-orange-100 rounded-3xl p-6 bg-orange-50/30">
                    <h3 class="font-bold text-gray-800 mb-4 border-b pb-2">কুরিয়ার ডেলিভারি খরচ</h3>
                    <div class="overflow-hidden rounded-xl border border-gray-200 bg-white">
                        <table class="w-full text-sm text-left">
                            <tr class="bg-gray-50 border-b font-bold"><td class="p-3">বিবরণ</td><td class="p-3 text-right">চার্জ</td></tr>
                            <tr class="border-b"><td class="p-3">সর্বমোট ১ কেজি পর্যন্ত</td><td class="p-3 text-right font-bold">৳ ১৩০</td></tr>
                            <tr class="border-b"><td class="p-3">সর্বমোট ২ কেজি পর্যন্ত</td><td class="p-3 text-right font-bold">৳ ১৫০</td></tr>
                        </table>
                    </div>
                    <p class="mt-4 text-[12px] text-orange-600 font-bold italic">⚠️ {{ p.delivery_text }}</p>
                </div>

                <!-- Tabs -->
                <div class="mt-12">
                    <div class="flex border-b text-sm font-bold">
                        <button onclick="tab('desc')" id="btn-desc" class="tab-btn active px-6 py-4">Description</button>
                        <button onclick="tab('pol')" id="btn-pol" class="tab-btn px-6 py-4">Order Policy</button>
                        <button onclick="tab('rev')" id="btn-rev" class="tab-btn px-6 py-4">Reviews (0)</button>
                    </div>
                    <div id="c-desc" class="py-8 text-gray-700 leading-loose text-sm">
                        <h4 class="font-bold text-gray-900 mb-4">পণ্যের বিস্তারিত:</h4>
                        {{ p.description | safe }}
                    </div>
                    <div id="c-pol" class="hidden py-8 text-gray-700 text-sm">
                        <h4 class="font-bold text-gray-900 mb-4">অর্ডার নিয়মাবলী:</h4>
                        {{ p.order_policy | safe }}
                    </div>
                    <div id="c-rev" class="hidden py-12 text-center text-gray-400 italic">এখনো কোনো রিভিউ নেই।</div>
                </div>
            </div>

        {% elif page == 'admin' %}
            <!-- Admin Control (বিন্দু পরিমাণ ফিচার বাদ নেই) -->
            <div class="max-w-4xl mx-auto space-y-10">
                <div class="bg-white p-8 rounded-3xl shadow-sm border border-orange-100">
                    <h2 class="font-black text-xl mb-6 text-orange-600 flex items-center gap-2">🍎 নতুন ফল যুক্ত করুন</h2>
                    <form action="/admin/add-product" method="POST" class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <input type="text" name="name" placeholder="ফলের নাম" class="border-2 p-4 rounded-2xl w-full outline-none focus:border-orange-500" required>
                            <select name="cat" class="border-2 p-4 rounded-2xl w-full bg-white outline-none">
                                <option>ফল (Fruits)</option><option>আচার (Pickle)</option><option>মধু (Honey)</option><option>আম (Mango)</option><option>মশলা (Masala)</option>
                            </select>
                        </div>
                        <input type="text" name="img" placeholder="ইমেজ সরাসরি লিঙ্ক (URL)" class="border-2 p-4 rounded-2xl w-full outline-none">
                        <div class="grid grid-cols-3 gap-4">
                            <input type="number" name="price" placeholder="আসল দাম" class="border-2 p-4 rounded-2xl">
                            <input type="number" name="disc" placeholder="ডিস্কাউন্ট %" class="border-2 p-4 rounded-2xl">
                            <input type="text" name="weight" placeholder="ওজন (যেমন: ৫০০ গ্রাম)" class="border-2 p-4 rounded-2xl">
                        </div>
                        <input type="text" name="code" placeholder="প্রোডাক্ট কোড (যেমন: P-101)" class="border-2 p-4 rounded-2xl w-full">
                        <textarea name="desc" placeholder="ফলের বিস্তারিত তথ্য" class="w-full border-2 p-4 rounded-2xl h-32"></textarea>
                        <textarea name="pol" placeholder="অর্ডার করার নিয়মাবলী" class="w-full border-2 p-4 rounded-2xl h-24"></textarea>
                        <input type="text" name="del_text" placeholder="ডেলিভারি সার্চ টেক্স" class="w-full border-2 p-4 rounded-2xl">
                        <button class="w-full bg-[#f97316] text-white py-5 rounded-2xl font-black text-lg shadow-xl shadow-orange-100">পাবলিশ করুন</button>
                    </form>
                </div>
            </div>

        {% elif page == 'checkout' %}
            <!-- Checkout (Location, BKash, Cash on Delivery সব সহ) -->
            <div class="max-w-xl mx-auto bg-white p-8 rounded-3xl shadow-xl border border-gray-50">
                <h2 class="text-2xl font-black mb-8 text-gray-800 border-b pb-4">অর্ডার কনফার্ম করুন</h2>
                <form action="/place-order" method="POST" class="space-y-5">
                    <input type="hidden" name="p_id" value="{{ p._id }}">
                    <div><label class="text-xs font-bold text-gray-500 mb-1 block">আপনার নাম *</label>
                        <input type="text" name="name" class="w-full border-2 p-4 rounded-2xl" placeholder="নাম লিখুন" required></div>
                    <div><label class="text-xs font-bold text-gray-500 mb-1 block">মোবাইল নাম্বার *</label>
                        <input type="text" name="phone" class="w-full border-2 p-4 rounded-2xl" placeholder="017xxxxxxxx" required></div>
                    <div><label class="text-xs font-bold text-gray-500 mb-1 block">পূর্ণ ঠিকানা (লোকেশন) *</label>
                        <textarea name="address" class="w-full border-2 p-4 rounded-2xl h-24" placeholder="গ্রাম/এলাকা, থানা, জেলা লিখুন" required></textarea></div>
                    <div><label class="text-xs font-bold text-gray-500 mb-1 block">পেমেন্ট মেথড সিলেক্ট করুন</label>
                        <select name="payment" class="w-full border-2 p-4 rounded-2xl bg-white font-bold">
                            <option value="Cash on Delivery">ক্যাশ অন ডেলিভারি (COD)</option>
                            <option value="Bkash">বিকাশ (Bkash)</option>
                            <option value="Nagad">নগদ (Nagad)</option>
                            <option value="Rocket">রকেট/উপায়</option>
                        </select></div>
                    <button class="w-full bg-[#f97316] text-white py-5 rounded-2xl font-black text-xl shadow-2xl mt-5 transform hover:scale-95 transition">অর্ডার সম্পন্ন করুন</button>
                </form>
            </div>
        {% endif %}
    </div>

    <!-- Footer (হুবহু স্ক্রিনশটের মতো) -->
    <footer class="bg-white border-t border-gray-100 p-10 mt-20 text-center">
        <div class="text-3xl font-black flex justify-center items-center mb-4">
            <span class="logo-orange">Paharer</span><span class="logo-dark ml-1">Bazar</span>
        </div>
        <p class="text-xs text-gray-400 font-bold mb-10 tracking-[3px]">Address: Muslimpara, Khagrachhari Sadar.<br>Hotline: +8801511820222</p>
        
        <div class="grid grid-cols-2 gap-10 text-left max-w-sm mx-auto text-[11px] font-bold text-gray-600 border-t pt-8">
            <ul class="space-y-2"><li>Useful Link</li><li class="font-normal">Contact Us</li><li class="font-normal">Delivery Rules</li></ul>
            <ul class="space-y-2"><li>Company</li><li class="font-normal">All Products</li><li class="font-normal">Return Policy</li></ul>
        </div>
        
        <div class="bg-[#f97316] text-white p-5 text-[10px] font-bold tracking-[2px] mt-10 -mx-10 -mb-10">
            Copyright © 2026 Paharer Bazar. All rights reserved.
        </div>
    </footer>

    <!-- Fixed Bottom Nav (আপনার স্ক্রিনশটের মতো) -->
    <nav class="bottom-nav">
        <button onclick="toggleSidebar()" class="nav-item"><span>☰</span><span>Category</span></button>
        <a href="https://wa.me/8801511820222" class="nav-item"><span>💬</span><span>Whatsapp</span></a>
        <a href="/" class="nav-item"><div class="home-circle">🏠</div><span class="mt-4 text-[#f97316] uppercase">Home</span></a>
        <div class="nav-item"><span>🛒</span><span>Cart (0)</span></div>
        <a href="/login" class="nav-item"><span>👤</span><span>Login</span></a>
    </nav>

    <script>
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('sidebar-hidden'); }
        function tab(n) {
            document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
            document.querySelectorAll('[id^="c-"]').forEach(c=>c.classList.add('hidden'));
            document.getElementById('btn-'+n).classList.add('active');
            document.getElementById('c-'+n).classList.remove('hidden');
        }
    </script>
</body>
</html>
"""

# --- রুটিং এবং ডাটাবেস লজিক ---

@app.route('/')
def index():
    return render_template_string(MASTER_HTML, page='home', products=list(products_col.find()), categories=list(categories_col.find()))

@app.route('/product/<id>')
def product_detail(id):
    return render_template_string(MASTER_HTML, page='product_detail', p=products_col.find_one({"_id": ObjectId(id)}), categories=list(categories_col.find()))

@app.route('/checkout/<id>')
def checkout(id):
    return render_template_string(MASTER_HTML, page='checkout', p=products_col.find_one({"_id": ObjectId(id)}), categories=list(categories_col.find()))

@app.route('/place-order', methods=['POST'])
def place_order():
    orders_col.insert_one({"p_id": request.form['p_id'], "name": request.form['name'], "phone": request.form['phone'], "address": request.form['address'], "payment": request.form['payment'], "date": datetime.now()})
    flash("অর্ডার সফল হয়েছে! আমরা শীঘ্রই যোগাযোগ করব।")
    return redirect('/')

@app.route('/admin')
def admin_panel():
    return render_template_string(MASTER_HTML, page='admin', categories=list(categories_col.find()))

@app.route('/admin/add-product', methods=['POST'])
def add_product():
    price = float(request.form['price'])
    disc = float(request.form['disc'] or 0)
    products_col.insert_one({
        "name": request.form['name'], "image": request.form['img'], "category": request.form['cat'],
        "price": price, "discount": disc, "sale_price": int(price - (price * disc / 100)),
        "code": request.form['code'], "weight": request.form['weight'],
        "description": request.form['desc'].replace('\n', '<br>'),
        "order_policy": request.form['pol'].replace('\n', '<br>'),
        "delivery_text": request.form['del_text']
    })
    flash("পণ্যটি শপে যুক্ত করা হয়েছে!")
    return redirect('/')

@app.route('/login')
def login_page(): return "লগইন পেজ কনফিগার করা হয়নি। এডমিন প্যানেল সরাসরি এক্সেসযোগ্য।"

if __name__ == "__main__":
    app.run(debug=True)
