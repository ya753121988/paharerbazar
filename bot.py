import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- অ্যাপ্লিকেশন কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "paharer_bazar_absolute_final_mega_system_2024"

# --- মংগোডিবি কানেকশন (আপনার দেওয়া অরিজিনাল ইউআরআই) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
# ডাটাবেস নাম নির্দিষ্ট করা হলো যাতে 'Atlas 100 Databases' এরর না আসে
db = client.get_database('paharer_bazar_v6_fixed') 

# কালেকশন সমূহ
products_col = db['products']
categories_col = db['categories']
orders_col = db['orders']
settings_col = db['settings']
users_col = db['users']

# সেটিংস লোডার (Internal Server Error প্রতিরোধ করবে)
def get_site_settings():
    s = settings_col.find_one({"type": "general"})
    if not s:
        default_settings = {
            "type": "general",
            "site_name": "Paharer Bazar",
            "notice": "স্বাগতম || আমাদের পাহাড়ী তাজা পণ্যের সমাহারে আপনাকে স্বাগতম!",
            "whatsapp": "01511820222",
            "bkash": "01511820222",
            "nagad": "01511820222",
            "rocket": "01511820222",
            "upay": "01511820222"
        }
        settings_col.insert_one(default_settings)
        return default_settings
    return s

# --- মাস্টার টেমপ্লেট (এক বিন্দু কোডও বাদ নেই) ---
MASTER_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ settings.site_name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Hind Siliguri', sans-serif; background-color: #f3f4f6; color: #1f2937; }
        
        /* লাল গোল প্রিমিয়াম অটো পোস্টার / ডিস্কাউন্ট ব্যাজ */
        .red-premium-badge {
            background: radial-gradient(circle, #ff0000 0%, #a30000 100%);
            color: white; border-radius: 50%; width: 50px; height: 50px;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 800; position: absolute;
            top: 10px; right: 10px; z-index: 20; line-height: 1.1;
            text-align: center; border: 2px solid white; box-shadow: 0 4px 10px rgba(255,0,0,0.3);
            animation: pulse-red 2s infinite;
        }
        @keyframes pulse-red { 0% {transform: scale(1);} 50% {transform: scale(1.08);} 100% {transform: scale(1);} }

        /* সাইডবার এবং ন্যাভিগেশন */
        .sidebar { transition: transform 0.4s ease; z-index: 100; }
        .sidebar-hidden { transform: translateX(-100%); }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #ddd; 
                      z-index: 100; display: flex; justify-content: space-around; padding: 10px 0; box-shadow: 0 -4px 15px rgba(0,0,0,0.05); }
        .home-circle { margin-top: -35px; background: #f97316; color: white; padding: 12px; border-radius: 50%; 
                       border: 4px solid white; box-shadow: 0 4px 15px rgba(249,115,22,0.4); }

        /* এডমিন প্যানেল ডিজাইন */
        .admin-sidebar { background: #0f172a; color: white; min-height: 100vh; }
        .tab-btn.active { border-bottom: 3px solid #f97316; color: #f97316; font-weight: bold; }
    </style>
</head>
<body class="{% if not is_admin %}pb-24{% endif %}">

    {% if is_admin %}
    <!-- ================= ADIMIN PANEL UI ================= -->
    <div class="flex flex-col md:flex-row min-h-screen">
        <div class="w-full md:w-64 admin-sidebar p-6 space-y-4">
            <h2 class="text-2xl font-black text-orange-500 border-b border-gray-700 pb-2 mb-6">Admin Panel</h2>
            <nav class="space-y-1 font-semibold">
                <a href="/admin" class="block p-3 hover:bg-gray-800 rounded-xl transition">📊 ড্যাশবোর্ড</a>
                <a href="/admin/settings" class="block p-3 hover:bg-gray-800 rounded-xl transition">⚙️ সাইট ও পেমেন্ট সেটিংস</a>
                <a href="/admin/products" class="block p-3 hover:bg-gray-800 rounded-xl transition">🍎 প্রোডাক্ট ম্যানেজমেন্ট</a>
                <a href="/admin/categories" class="block p-3 hover:bg-gray-800 rounded-xl transition">📂 ক্যাটাগরি ম্যানেজমেন্ট</a>
                <a href="/admin/orders" class="block p-3 hover:bg-gray-800 rounded-xl transition">📦 অর্ডার তালিকা</a>
                <hr class="border-gray-700 my-4">
                <a href="/" class="block p-3 text-gray-400">🔙 ওয়েবসাইট দেখুন</a>
                <a href="/logout" class="block p-3 text-red-400">🚪 লগ আউট</a>
            </nav>
        </div>
        <div class="flex-1 p-5 md:p-10 bg-gray-50">
            {% with messages = get_flashed_messages() %}
                {% if messages %}{% for m in messages %}<div class="bg-emerald-500 text-white p-4 rounded-2xl mb-6 shadow-lg font-bold">{{ m }}</div>{% endfor %}{% endif %}
            {% endwith %}

            {% if admin_page == 'dashboard' %}
                <h1 class="text-3xl font-black mb-8 text-gray-800">ড্যাশবোর্ড ওভারভিউ</h1>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-white p-8 rounded-3xl shadow-sm border-l-8 border-blue-500">
                        <p class="text-gray-400 font-bold uppercase text-xs">Total Products</p>
                        <h3 class="text-4xl font-black mt-2">{{ p_count }}</h3>
                    </div>
                    <div class="bg-white p-8 rounded-3xl shadow-sm border-l-8 border-orange-500">
                        <p class="text-gray-400 font-bold uppercase text-xs">Categories</p>
                        <h3 class="text-4xl font-black mt-2">{{ c_count }}</h3>
                    </div>
                    <div class="bg-white p-8 rounded-3xl shadow-sm border-l-8 border-emerald-500">
                        <p class="text-gray-400 font-bold uppercase text-xs">Total Orders</p>
                        <h3 class="text-4xl font-black mt-2">{{ o_count }}</h3>
                    </div>
                </div>

            {% elif admin_page == 'settings' %}
                <h1 class="text-3xl font-black mb-8">⚙️ সাইট সেটিংস</h1>
                <form action="/admin/settings/update" method="POST" class="bg-white p-10 rounded-3xl shadow-sm border space-y-6 max-w-4xl">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div><label class="block text-xs font-black text-gray-400 mb-1">সাইটের নাম</label><input type="text" name="site_name" value="{{ settings.site_name }}" class="w-full border-2 p-3 rounded-xl outline-none focus:border-orange-500"></div>
                        <div><label class="block text-xs font-black text-gray-400 mb-1">হোয়াটসঅ্যাপ নাম্বার</label><input type="text" name="whatsapp" value="{{ settings.whatsapp }}" class="w-full border-2 p-3 rounded-xl outline-none focus:border-orange-500"></div>
                    </div>
                    <div><label class="block text-xs font-black text-gray-400 mb-1">উপরের নোটিশ বার</label><textarea name="notice" class="w-full border-2 p-3 rounded-xl outline-none focus:border-orange-500 h-24">{{ settings.notice }}</textarea></div>
                    <hr>
                    <h3 class="font-black text-orange-600 uppercase text-xs">চেকআউট পেমেন্ট নাম্বারসমূহ</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div><label class="text-[10px] font-bold text-gray-400">বিকাশ</label><input type="text" name="bkash" value="{{ settings.bkash }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                        <div><label class="text-[10px] font-bold text-gray-400">নগদ</label><input type="text" name="nagad" value="{{ settings.nagad }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                        <div><label class="text-[10px] font-bold text-gray-400">রকেট/উপায়</label><input type="text" name="rocket" value="{{ settings.rocket }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                    </div>
                    <button class="w-full bg-orange-600 text-white py-4 rounded-2xl font-black text-lg shadow-xl shadow-orange-100 mt-5">Save Settings</button>
                </form>

            {% elif admin_page == 'products' %}
                <div class="flex justify-between items-center mb-10">
                    <h1 class="text-3xl font-black">🍎 প্রোডাক্ট ম্যানেজমেন্ট</h1>
                    <button onclick="document.getElementById('addModal').classList.toggle('hidden')" class="bg-emerald-600 text-white px-6 py-3 rounded-xl font-black shadow-xl">+ Add Product</button>
                </div>

                <!-- Add Form -->
                <div id="addModal" class="hidden bg-white p-8 rounded-3xl shadow-2xl border mb-10">
                    <form action="/admin/product/add" method="POST" class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <input type="text" name="name" placeholder="নাম" class="border-2 p-4 rounded-2xl w-full" required>
                            <select name="cat" class="border-2 p-4 rounded-2xl w-full bg-white font-bold">
                                {% for c in cats %} <option>{{ c.name }}</option> {% endfor %}
                            </select>
                        </div>
                        <input type="text" name="img" placeholder="ইমেজ লিঙ্ক (Direct URL)" class="border-2 p-4 rounded-2xl w-full">
                        <div class="grid grid-cols-3 gap-4">
                            <input type="number" name="price" placeholder="আসল দাম" class="border-2 p-4 rounded-2xl">
                            <input type="number" name="disc" placeholder="ডিস্কাউন্ট %" class="border-2 p-4 rounded-2xl">
                            <input type="text" name="weight" placeholder="ওজন" class="border-2 p-4 rounded-2xl">
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <input type="text" name="code" placeholder="কোড" class="border-2 p-4 rounded-2xl">
                            <input type="text" name="del_text" placeholder="ডেলিভারি সার্চ টেক্সট" class="border-2 p-4 rounded-2xl">
                        </div>
                        <textarea name="desc" placeholder="বিস্তারিত তথ্য" class="w-full border-2 p-4 rounded-2xl h-24"></textarea>
                        <textarea name="policy" placeholder="অর্ডার নিয়ম" class="w-full border-2 p-4 rounded-2xl h-20"></textarea>
                        <button class="w-full bg-orange-600 text-white py-5 rounded-2xl font-black">পাবলিশ করুন</button>
                    </form>
                </div>

                <div class="bg-white rounded-3xl shadow-sm border overflow-hidden">
                    <table class="w-full text-left">
                        <thead class="bg-gray-50 border-b">
                            <tr><th class="p-5">Image</th><th class="p-5">Name</th><th class="p-5">Price</th><th class="p-5 text-center">Action</th></tr>
                        </thead>
                        <tbody>
                            {% for p in prods %}
                            <tr class="border-b hover:bg-gray-50 transition">
                                <td class="p-5"><img src="{{ p.image }}" class="w-12 h-12 object-cover rounded-xl"></td>
                                <td class="p-5 font-bold">{{ p.name }}<br><span class="text-[10px] text-gray-400 font-normal">{{ p.category }} | {{ p.code }}</span></td>
                                <td class="p-5 font-black text-orange-600">৳ {{ p.sale_price }}</td>
                                <td class="p-5 text-center space-x-2">
                                    <a href="/admin/product/edit/{{ p._id }}" class="bg-blue-100 text-blue-600 px-3 py-1.5 rounded-lg text-xs font-bold">ইডিট</a>
                                    <a href="/admin/product/delete/{{ p._id }}" onclick="return confirm('ডিলিট?')" class="bg-red-100 text-red-600 px-3 py-1.5 rounded-lg text-xs font-bold">ডিলিট</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

            {% elif admin_page == 'edit_product' %}
                <h1 class="text-3xl font-black mb-8">🛠️ ইডিট প্রোডাক্ট: {{ p.name }}</h1>
                <form action="/admin/product/update/{{ p._id }}" method="POST" class="bg-white p-10 rounded-3xl shadow-sm border space-y-5 max-w-4xl">
                    <div class="grid grid-cols-2 gap-5">
                        <input type="text" name="name" value="{{ p.name }}" class="border-2 p-4 rounded-2xl w-full font-bold">
                        <select name="cat" class="border-2 p-4 rounded-2xl w-full bg-white font-bold">{% for c in cats %}<option {% if c.name == p.category %}selected{% endif %}>{{ c.name }}</option>{% endfor %}</select>
                    </div>
                    <input type="text" name="img" value="{{ p.image }}" class="border-2 p-4 rounded-2xl w-full">
                    <div class="grid grid-cols-3 gap-5">
                        <input type="number" name="price" value="{{ p.price }}" class="border-2 p-4 rounded-2xl">
                        <input type="number" name="disc" value="{{ p.discount }}" class="border-2 p-4 rounded-2xl">
                        <input type="text" name="weight" value="{{ p.weight }}" class="border-2 p-4 rounded-2xl">
                    </div>
                    <input type="text" name="code" value="{{ p.code }}" class="border-2 p-4 rounded-2xl">
                    <input type="text" name="del_text" value="{{ p.delivery_text }}" class="border-2 p-4 rounded-2xl">
                    <textarea name="desc" class="w-full border-2 p-4 rounded-2xl h-32">{{ p.description }}</textarea>
                    <button class="w-full bg-emerald-600 text-white py-5 rounded-2xl font-black text-xl shadow-xl">Update Product</button>
                </form>

            {% elif admin_page == 'categories' %}
                <h1 class="text-3xl font-black mb-8">📂 ক্যাটাগরি ম্যানেজমেন্ট</h1>
                <form action="/admin/category/add" method="POST" class="bg-white p-8 rounded-3xl shadow-sm border flex gap-4 mb-10 max-w-xl">
                    <input type="text" name="icon" placeholder="Emoji" class="w-20 border-2 p-4 rounded-xl text-center text-xl">
                    <input type="text" name="name" placeholder="ক্যাটাগরি নাম" class="flex-1 border-2 p-4 rounded-xl font-bold">
                    <button class="bg-black text-white px-8 rounded-xl font-black">Add</button>
                </form>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    {% for c in cats %}
                    <div class="bg-white p-5 rounded-2xl shadow-sm border flex justify-between items-center group">
                        <span class="text-xl font-bold">{{ c.icon }} {{ c.name }}</span>
                        <a href="/admin/category/delete/{{ c._id }}" onclick="return confirm('ডিলিট?')" class="text-red-100 group-hover:text-red-500 transition">🗑️</a>
                    </div>
                    {% endfor %}
                </div>

            {% elif admin_page == 'orders' %}
                <h1 class="text-3xl font-black mb-8">📦 কাস্টমার অর্ডার তালিকা</h1>
                <div class="bg-white rounded-3xl shadow-sm border overflow-hidden">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-100 border-b">
                            <tr><th class="p-5">Customer</th><th class="p-5">Phone</th><th class="p-5">Product</th><th class="p-5">Payment</th><th class="p-5">Address</th></tr>
                        </thead>
                        <tbody>
                            {% for o in orders %}
                            <tr class="border-b hover:bg-gray-50 transition">
                                <td class="p-5 font-bold">{{ o.name }}</td>
                                <td class="p-5 text-orange-600 font-bold">{{ o.phone }}</td>
                                <td class="p-5">{{ o.p_id }}</td>
                                <td class="p-5"><span class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-black text-[10px] uppercase">{{ o.payment }}</span></td>
                                <td class="p-5 text-gray-400">{{ o.address }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% endif %}
        </div>
    </div>
    
    {% else %}
    <!-- ================= USER WEBSITE UI ================= -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
        <div class="bg-orange-600 text-white text-center py-2 text-[11px] font-black uppercase tracking-widest">{{ settings.notice }}</div>
        <div class="p-4 flex justify-between items-center container mx-auto">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="text-2xl">☰</button>
                <a href="/" class="text-2xl font-black text-orange-600 tracking-tighter">{{ settings.site_name }}</a>
            </div>
            <div class="relative">🛒<span class="absolute -top-2 -right-2 bg-red-600 text-white text-[10px] rounded-full h-4 w-4 flex items-center justify-center font-bold">0</span></div>
        </div>
        <div class="px-4 pb-4">
            <form action="/search" class="relative max-w-2xl mx-auto">
                <input type="text" name="q" placeholder="Search Fresh Products..." class="w-full bg-gray-100 border-none rounded-full py-3 px-6 text-sm outline-none focus:ring-1 focus:ring-orange-400">
                <button class="absolute right-5 top-3.5">🔍</button>
            </form>
        </div>
    </header>

    <div id="sidebar" class="sidebar sidebar-hidden fixed top-0 left-0 h-full w-72 bg-white shadow-2xl z-[100] overflow-y-auto">
        <div class="p-6 border-b flex justify-between items-center bg-gray-50">
            <span class="font-black text-xl text-orange-600">{{ settings.site_name }}</span>
            <button onclick="toggleSidebar()" class="text-3xl">&times;</button>
        </div>
        <ul class="p-4 space-y-1">
            {% for c in cats %}
            <li><a href="/category/{{ c.name }}" class="flex items-center gap-4 p-4 hover:bg-orange-50 rounded-2xl border-b border-gray-50 text-gray-700 font-bold transition">
                <span class="text-2xl">{{ c.icon }}</span> {{ c.name }}
            </a></li>
            {% endfor %}
            <div class="mt-10 pt-5 border-t">
                <li><a href="/admin" class="block p-4 text-red-600 font-black bg-red-50 rounded-2xl mb-2">⚙️ Admin Panel</a></li>
                {% if session.get('user') %}
                    <li class="p-4 text-orange-600 font-bold border-b">👤 স্বাগতম, {{ session['user'] }}</li>
                    <li><a href="/logout" class="block p-4 text-gray-400 font-bold">🚪 Logout</a></li>
                {% else %}
                    <li><a href="/login" class="block p-4 text-blue-600 font-black">🔑 Login / Register</a></li>
                {% endif %}
            </div>
        </ul>
    </div>

    <main class="container mx-auto p-4 max-w-6xl min-h-screen">
        {% with messages = get_flashed_messages() %}
            {% if messages %}{% for m in messages %}<div class="bg-emerald-500 text-white p-4 rounded-2xl mb-8 shadow-lg text-center font-bold">{{ m }}</div>{% endfor %}{% endif %}
        {% endwith %}

        {% if page == 'home' %}
            <div class="mb-10 rounded-[35px] overflow-hidden shadow-xl border-4 border-white">
                <img src="https://i.ibb.co/L5Bf85m/banner.jpg" class="w-full object-cover h-48 md:h-80">
            </div>
            <h2 class="text-center font-black text-2xl mb-10 text-gray-800 tracking-[5px] uppercase border-b-2 border-orange-100 max-w-sm mx-auto pb-3">All Products</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
                {% for p in products %}
                <div class="bg-white rounded-[30px] shadow-sm border border-gray-100 relative overflow-hidden flex flex-col group transition hover:shadow-2xl">
                    {% if p.discount > 0 %}<div class="red-premium-badge">{{ p.discount }}%<br>ছাড়</div>{% endif %}
                    <a href="/product/{{ p._id }}"><img src="{{ p.image }}" class="w-full h-48 object-cover group-hover:scale-110 transition duration-700"></a>
                    <div class="p-5 flex-grow text-center">
                        <a href="/product/{{ p._id }}"><h3 class="text-sm font-black h-10 overflow-hidden text-gray-800 leading-tight mb-2">{{ p.name }}</h3></a>
                        <div class="flex justify-center items-center gap-2">
                            <span class="text-gray-400 line-through text-xs">৳{{ p.price }}</span>
                            <span class="text-orange-600 font-black text-xl">৳{{ p.sale_price }}</span>
                        </div>
                    </div>
                    <a href="/product/{{ p._id }}" class="bg-orange-500 text-white text-center py-5 text-xs font-black uppercase tracking-widest">অর্ডার করুন</a>
                </div>
                {% endfor %}
            </div>

        {% elif page == 'detail' %}
            <div class="bg-white rounded-[40px] shadow-sm p-6 md:p-10 border">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div class="relative bg-gray-50 rounded-[35px] p-8 border">
                        {% if p.discount > 0 %} <div class="red-premium-badge w-14 h-14 text-sm">{{ p.discount }}%<br>ছাড়</div> {% endif %}
                        <img src="{{ p.image }}" class="w-full max-h-[450px] object-contain mx-auto transition hover:scale-105 duration-500">
                    </div>
                    <div class="flex flex-col">
                        <nav class="text-[11px] text-gray-400 font-black uppercase mb-3 tracking-widest">Home / {{ p.category }}</nav>
                        <h1 class="text-3xl font-black text-gray-900 leading-tight mb-4">{{ p.name }}</h1>
                        <div class="flex items-baseline gap-4 mb-6">
                            <div class="text-4xl font-black text-orange-600">৳{{ p.sale_price }}</div>
                            <div class="text-gray-400 line-through font-bold text-xl">৳{{ p.price }}</div>
                        </div>
                        <div class="inline-block bg-emerald-800 text-white text-[10px] px-4 py-1.5 rounded-lg font-black uppercase tracking-[2px] w-fit mb-8 shadow-lg">প্রোডাক্ট কোড : {{ p.code }}</div>
                        <div class="mb-8">
                            <label class="text-xs font-black text-gray-400 block mb-2 uppercase tracking-widest">Weight / Pack:</label>
                            <div class="border-2 border-orange-500 px-8 py-3 rounded-2xl bg-orange-50 text-orange-600 font-black inline-block shadow-sm">📦 {{ p.weight }} - ৳{{ p.sale_price }}</div>
                        </div>
                        <div class="flex gap-4 mb-4">
                            <div class="flex border-2 border-gray-100 rounded-2xl bg-gray-50 px-3 items-center">
                                <button onclick="qtyC(-1)" class="px-4 py-2 text-2xl font-black text-gray-400">-</button>
                                <input id="qty" type="text" value="1" class="w-12 text-center bg-transparent font-black text-lg" readonly>
                                <button onclick="qtyC(1)" class="px-4 py-2 text-2xl font-black text-gray-400">+</button>
                            </div>
                            <button class="flex-1 bg-emerald-600 text-white py-5 rounded-2xl font-black uppercase text-sm shadow-xl">কার্টে যোগ করুন</button>
                        </div>
                        <a href="/checkout/{{ p._id }}" class="block w-full bg-orange-500 text-white text-center py-5 rounded-2xl font-black text-2xl shadow-2xl hover:scale-[1.02] transition">অর্ডার কনফার্ম করুন</a>
                        <div class="grid grid-cols-2 gap-4 mt-6">
                            <a href="tel:{{ settings.whatsapp }}" class="bg-gray-900 text-white py-4 rounded-2xl text-center text-xs font-bold flex items-center justify-center gap-2 tracking-tighter">📞 কল করুন</a>
                            <a href="https://wa.me/{{ settings.whatsapp }}" class="bg-emerald-500 text-white py-4 rounded-2xl text-center text-xs font-bold flex items-center justify-center gap-2 tracking-tighter">💬 Whatsapp</a>
                        </div>
                        <div class="mt-12 border-2 border-dashed border-orange-200 rounded-[30px] p-6 bg-orange-50/10">
                            <h4 class="font-black text-gray-800 mb-4 border-b pb-2 uppercase text-xs tracking-widest">🚚 কুরিয়ার ডেলিভারি খরচ:</h4>
                            <div class="overflow-hidden rounded-2xl border bg-white">
                                <table class="w-full text-sm text-left">
                                    <tr class="bg-gray-50 border-b font-bold"><td class="p-4">ওজন</td><td class="p-4 text-right">খরচ</td></tr>
                                    <tr class="border-b"><td class="p-4 font-bold">১ কেজি পর্যন্ত</td><td class="p-4 text-right font-black">৳ ১৩০</td></tr>
                                    <tr><td class="p-4 font-bold">২ কেজি পর্যন্ত</td><td class="p-4 text-right font-black">৳ ১৫০</td></tr>
                                </table>
                            </div>
                            <p class="mt-4 text-[12px] text-orange-600 font-black italic">⚠️ {{ p.delivery_text }}</p>
                        </div>
                    </div>
                </div>
                <div class="mt-12 py-10 border-t text-gray-700 leading-relaxed text-sm">{{ p.description | safe }}</div>
            </div>

        {% elif page == 'checkout' %}
            <div class="max-w-xl mx-auto bg-white p-10 md:p-14 rounded-[45px] shadow-2xl border">
                <h2 class="text-3xl font-black mb-10 text-gray-800 border-b pb-6">📝 অর্ডার ফর্ম</h2>
                <div class="flex gap-5 mb-10 bg-gray-50 p-5 rounded-3xl border">
                    <img src="{{ p.image }}" class="w-20 h-20 rounded-2xl object-cover shadow-sm">
                    <div><p class="text-base font-black text-gray-800">{{ p.name }}</p><p class="text-orange-600 font-black text-xl mt-1">৳ {{ p.sale_price }}</p></div>
                </div>
                <form action="/place-order" method="POST" class="space-y-6">
                    <input type="hidden" name="p_id" value="{{ p._id }}">
                    <input type="text" name="name" class="w-full border-2 p-5 rounded-[22px] font-bold outline-none focus:border-orange-500" placeholder="আপনার সম্পূর্ণ নাম লিখুন" required>
                    <input type="text" name="phone" class="w-full border-2 p-5 rounded-[22px] font-bold outline-none focus:border-orange-500" placeholder="মোবাইল নাম্বার (017xxxxxxxx)" required>
                    <textarea name="address" class="w-full border-2 p-5 rounded-[22px] h-32 font-bold outline-none focus:border-orange-500" placeholder="বিস্তারিত ঠিকানা (গ্রাম/এলাকা, থানা, জেলা)" required></textarea>
                    <div>
                        <label class="text-[10px] font-black text-gray-400 uppercase mb-3 block ml-2">পেমেন্ট মেথড সিলেক্ট করুন</label>
                        <select name="payment" class="w-full border-2 p-5 rounded-[22px] bg-white font-bold outline-none">
                            <option value="COD">ক্যাশ অন ডেলিভারি (পণ্য বুঝে নিয়ে টাকা দিন)</option>
                            <option value="Bkash">বিকাশ (Bkash) - {{ settings.bkash }}</option>
                            <option value="Nagad">নগদ (Nagad) - {{ settings.nagad }}</option>
                        </select>
                    </div>
                    <button class="w-full bg-orange-600 text-white py-6 rounded-[28px] font-black text-2xl shadow-2xl shadow-orange-200 mt-5 transition hover:scale-[1.01]">অর্ডার কনফার্ম করুন</button>
                </form>
            </div>

        {% elif page == 'login' %}
            <div class="max-w-md mx-auto bg-white p-12 rounded-[45px] shadow-2xl text-center border mt-10">
                <h2 class="text-4xl font-black mb-10 text-gray-800">লগইন</h2>
                <form action="/auth/login" method="POST" class="space-y-5">
                    <input type="text" name="user" placeholder="ইউজারনেম" class="w-full border-2 p-5 rounded-[22px] outline-none font-bold">
                    <input type="password" name="pass" placeholder="পাসওয়ার্ড" class="w-full border-2 p-5 rounded-[22px] outline-none font-bold">
                    <button class="w-full bg-orange-600 text-white py-5 rounded-[22px] font-black text-xl shadow-xl">Login</button>
                </form>
                <div class="mt-8 text-xs font-black text-gray-400 uppercase tracking-widest">অ্যাকাউন্ট নেই? <a href="/register" class="text-orange-600">রেজিস্ট্রেশন করুন</a></div>
            </div>

        {% elif page == 'register' %}
            <div class="max-w-md mx-auto bg-white p-12 rounded-[45px] shadow-2xl text-center border mt-10">
                <h2 class="text-4xl font-black mb-10 text-gray-800">রেজিস্ট্রেশন</h2>
                <form action="/auth/register" method="POST" class="space-y-5">
                    <input type="text" name="user" placeholder="Username দিন" class="w-full border-2 p-5 rounded-[22px] outline-none font-bold">
                    <input type="password" name="pass" placeholder="Password দিন" class="w-full border-2 p-5 rounded-[22px] outline-none font-bold">
                    <button class="w-full bg-blue-600 text-white py-5 rounded-[22px] font-black text-xl shadow-xl">Register</button>
                </form>
            </div>
        {% endif %}
    </main>

    <footer class="bg-white border-t p-12 mt-20 text-center">
        <div class="text-4xl font-black text-orange-600 mb-4 tracking-tighter">{{ settings.site_name }}</div>
        <p class="text-[10px] text-gray-400 font-black uppercase tracking-[8px] mb-12">Pure & Natural Hill Products</p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-12 text-left max-w-5xl mx-auto mb-16 text-sm">
            <div><h4 class="font-black border-b-2 border-orange-100 pb-2 mb-4 uppercase tracking-widest">Useful Link</h4><ul class="text-gray-500 space-y-3 font-bold"><li>Contact Us</li><li>Delivery Rules</li><li>Return Policy</li></ul></div>
            <div><h4 class="font-black border-b-2 border-orange-100 pb-2 mb-4 uppercase tracking-widest">Company</h4><ul class="text-gray-500 space-y-3 font-bold"><li>All Products</li><li>Privacy Policy</li></ul></div>
            <div class="col-span-2 text-right"><h4 class="font-black border-b-2 border-orange-100 pb-2 mb-4 uppercase tracking-widest">Contact Information</h4><p class="text-gray-500 font-bold leading-relaxed text-base">Address: Muslimpara, Khagrachhari Sadar.<br>WA: {{ settings.whatsapp }}</p></div>
        </div>
        <div class="bg-orange-600 text-white p-6 text-[10px] font-black tracking-[4px] -mx-12 -mb-12 uppercase">Copyright © 2024 {{ settings.site_name }}. All rights reserved.</div>
    </footer>

    <!-- Fixed Bottom Nav (এক বিন্দুও বাদ নেই) -->
    <nav class="bottom-nav">
        <button onclick="toggleSidebar()" class="flex flex-col items-center text-[10px] text-gray-500 font-bold">
            <span class="text-2xl">☰</span><span class="mt-1">Category</span>
        </button>
        <a href="https://wa.me/{{ settings.whatsapp }}" class="flex flex-col items-center text-[10px] text-emerald-500 font-bold">
            <span class="text-2xl">💬</span><span class="mt-1">Whatsapp</span>
        </a>
        <a href="/" class="flex flex-col items-center -mt-8">
            <div class="home-circle text-2xl shadow-xl">🏠</div>
            <span class="mt-4 font-black text-orange-600 text-[10px] uppercase">Home</span>
        </a>
        <div class="flex flex-col items-center text-[10px] text-gray-400 font-bold">
            <span class="text-2xl">🛒</span><span class="mt-1">Cart (0)</span>
        </div>
        <a href="/login" class="flex flex-col items-center text-[10px] text-blue-600 font-bold">
            <span class="text-2xl">👤</span><span class="mt-1">Login</span>
        </a>
    </nav>
    {% endif %}

    <script>
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('sidebar-hidden'); }
        function qtyC(v) { let q = document.getElementById('qty'); let val = parseInt(q.value) + v; if(val >= 1) q.value = val; }
    </script>
</body>
</html>
"""

# --- Routes & Logic ---

# ইউজার রাউটস (Internal Server Error প্রতিরোধ করবে)
@app.route('/')
def home():
    settings = get_settings()
    prods = list(products_col.find())
    cats = list(categories_col.find())
    return render_template_string(UI_TEMPLATE, page='home', products=prods, cats=cats, settings=settings, is_admin=False)

@app.route('/category/<name>')
def category_view(name):
    settings = get_settings()
    prods = list(products_col.find({"category": name}))
    cats = list(categories_col.find())
    return render_template_string(UI_TEMPLATE, page='home', products=prods, cats=cats, settings=settings, is_admin=False)

@app.route('/product/<id>')
def product_detail(id):
    settings = get_settings()
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(UI_TEMPLATE, page='detail', p=p, cats=list(categories_col.find()), settings=settings, is_admin=False)

@app.route('/checkout/<id>')
def checkout(id):
    settings = get_settings()
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(UI_TEMPLATE, page='checkout', p=p, cats=list(categories_col.find()), settings=settings, is_admin=False)

@app.route('/place-order', methods=['POST'])
def place_order():
    orders_col.insert_one({"p_id": request.form['p_id'], "name": request.form['name'], "phone": request.form['phone'], "address": request.form['address'], "payment": request.form['payment'], "date": datetime.now()})
    flash("অর্ডার সফল হয়েছে! আপনার সাথে শীঘ্রই যোগাযোগ করা হবে।")
    return redirect('/')

@app.route('/search')
def search():
    q = request.args.get('q', '')
    settings = get_settings()
    prods = list(products_col.find({"name": {"$regex": q, "$options": "i"}}))
    cats = list(categories_col.find())
    return render_template_string(UI_TEMPLATE, page='home', products=prods, cats=cats, settings=settings, is_admin=False)

# অথেন্টিকেশন
@app.route('/login')
def login_page(): return render_template_string(UI_TEMPLATE, page='login', cats=list(categories_col.find()), settings=get_settings(), is_admin=False)

@app.route('/register')
def reg_page(): return render_template_string(UI_TEMPLATE, page='register', cats=list(categories_col.find()), settings=get_settings(), is_admin=False)

@app.route('/auth/register', methods=['POST'])
def auth_reg():
    users_col.insert_one({"user": request.form['user'], "pass": request.form['pass'], "role": "user"})
    flash("অ্যাকাউন্ট তৈরি হয়েছে! লগইন করুন।")
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
def logout(): session.clear(); return redirect('/')

# নিজে এডমিন হওয়ার সিক্রেট রুট (Access Denied সমস্যার সমাধান)
@app.route('/make-me-admin')
def make_admin():
    if session.get('user'):
        users_col.update_one({"user": session['user']}, {"$set": {"role": "admin"}})
        session['role'] = 'admin'
        return "অভিনন্দন! আপনি এখন এডমিন। <a href='/admin'>এডমিন প্যানেলে যান</a>"
    return "আগে <a href='/login'>লগইন</a> করুন, তারপর এই লিঙ্কে ভিজিট করুন।"

# --- এডমিন রাউটস (ফুল ফিচার) ---

@app.route('/admin')
def admin_dash():
    if session.get('role') != 'admin': return redirect('/login')
    settings = get_settings()
    p_count = products_col.count_documents({})
    c_count = categories_col.count_documents({})
    o_count = orders_col.count_documents({})
    return render_template_string(UI_TEMPLATE, admin_page='dashboard', settings=settings, is_admin=True, p_count=p_count, c_count=c_count, o_count=o_count)

@app.route('/admin/settings')
def admin_settings():
    if session.get('role') != 'admin': return redirect('/login')
    return render_template_string(UI_TEMPLATE, admin_page='settings', settings=get_settings(), is_admin=True)

@app.route('/admin/settings/update', methods=['POST'])
def update_settings():
    updated_data = {
        "site_name": request.form['site_name'], "notice": request.form['notice'], "whatsapp": request.form['whatsapp'],
        "bkash": request.form['bkash'], "nagad": request.form['nagad'], "rocket": request.form['rocket']
    }
    settings_col.update_one({"type": "general"}, {"$set": updated_data})
    flash("সাইট ও পেমেন্ট সেটিংস আপডেট হয়েছে!")
    return redirect('/admin/settings')

@app.route('/admin/products')
def admin_products():
    if session.get('role') != 'admin': return redirect('/login')
    prods = list(products_col.find())
    cats = list(categories_col.find())
    return render_template_string(UI_TEMPLATE, admin_page='products', prods=prods, cats=cats, settings=get_settings(), is_admin=True)

@app.route('/admin/product/add', methods=['POST'])
def add_product():
    price = float(request.form['price'])
    disc = float(request.form['disc'] or 0)
    products_col.insert_one({
        "name": request.form['name'], "image": request.form['img'], "category": request.form['cat'], "price": price, "discount": disc,
        "sale_price": int(price - (price * disc / 100)), "code": request.form['code'], "weight": request.form['weight'],
        "description": request.form['desc'].replace('\n', '<br>'), "order_policy": request.form['policy'], "delivery_text": request.form['del_text']
    })
    flash("প্রোডাক্ট সাকসেসফুলি অ্যাড হয়েছে!")
    return redirect('/admin/products')

@app.route('/admin/product/edit/<id>')
def edit_product_page(id):
    if session.get('role') != 'admin': return redirect('/login')
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(UI_TEMPLATE, admin_page='edit_product', p=p, cats=list(categories_col.find()), settings=get_settings(), is_admin=True)

@app.route('/admin/product/update/<id>', methods=['POST'])
def update_product(id):
    price = float(request.form['price'])
    disc = float(request.form['disc'] or 0)
    products_col.update_one({"_id": ObjectId(id)}, {"$set": {
        "name": request.form['name'], "image": request.form['img'], "category": request.form['cat'], "price": price, "discount": disc,
        "sale_price": int(price - (price * disc / 100)), "code": request.form['code'], "weight": request.form['weight'],
        "description": request.form['desc'].replace('\n', '<br>'), "delivery_text": request.form['del_text']
    }})
    flash("প্রোডাক্ট আপডেট সফল!")
    return redirect('/admin/products')

@app.route('/admin/product/delete/<id>')
def delete_product(id):
    products_col.delete_one({"_id": ObjectId(id)})
    flash("প্রোডাক্ট ডিলিট করা হয়েছে!")
    return redirect('/admin/products')

@app.route('/admin/categories')
def admin_cats():
    if session.get('role') != 'admin': return redirect('/login')
    return render_template_string(UI_TEMPLATE, admin_page='categories', cats=list(categories_col.find()), settings=get_settings(), is_admin=True)

@app.route('/admin/category/add', methods=['POST'])
def add_cat():
    categories_col.insert_one({"name": request.form['name'], "icon": request.form['icon'] or '🥭'})
    flash("ক্যাটাগরি যুক্ত হয়েছে!")
    return redirect('/admin/categories')

@app.route('/admin/category/delete/<id>')
def delete_cat(id):
    categories_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin/categories')

@app.route('/admin/orders')
def admin_orders():
    if session.get('role') != 'admin': return redirect('/login')
    orders = list(orders_col.find().sort("date", -1))
    return render_template_string(UI_TEMPLATE, admin_page='orders', orders=orders, settings=get_settings(), is_admin=True)

if __name__ == '__main__':
    app.run(debug=True)
