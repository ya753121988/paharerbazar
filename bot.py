import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "paharer_bazar_mega_ultimate_2024"

# --- মংগোডিবি কানেকশন (আপনার দেওয়া লিঙ্ক) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database('paharer_bazar_v5') # ডাটাবেস নির্দিষ্ট করা হলো

# কালেকশন সমূহ
products_col = db['products']
categories_col = db['categories']
orders_col = db['orders']
settings_col = db['settings']
users_col = db['users']

# প্রাথমিক সেটিংস চেক ও অটো-জেনারেট
def get_settings():
    s = settings_col.find_one({"type": "general"})
    if not s:
        default = {
            "type": "general",
            "site_name": "Paharer Bazar",
            "notice": "স্বাগতম || সারা বাংলাদেশে ক্যাশ অন ডেলিভারি সুবিধা!",
            "whatsapp": "01511820222",
            "bkash": "01511820222",
            "nagad": "01511820222",
            "rocket": "01511820222"
        }
        settings_col.insert_one(default)
        return default
    return s

# --- মাস্টার টেমপ্লেট (ইউজার ও এডমিন প্যানেল আলাদা ডিজাইন) ---
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
        body { font-family: 'Hind Siliguri', sans-serif; background-color: #f3f4f6; }
        .discount-badge {
            background: radial-gradient(circle, #ff0000 0%, #a30000 100%);
            color: white; border-radius: 50%; width: 50px; height: 50px;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 800; position: absolute;
            top: 10px; right: 10px; z-index: 10; line-height: 1.1;
            text-align: center; border: 2px solid white; box-shadow: 0 4px 10px rgba(255,0,0,0.3);
            animation: pulse-red 2s infinite;
        }
        @keyframes pulse-red { 0% {transform: scale(1);} 50% {transform: scale(1.1);} 100% {transform: scale(1);} }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #ddd; 
                      z-index: 100; display: flex; justify-content: space-around; padding: 10px 0; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
        .home-center { margin-top: -35px; background: #f97316; color: white; padding: 12px; border-radius: 50%; 
                       border: 4px solid white; box-shadow: 0 4px 15px rgba(249,115,22,0.4); }
        .tab-btn.active { border-bottom: 3px solid #f97316; color: #f97316; font-weight: bold; }
        .sidebar { transition: transform 0.3s ease; }
        .sidebar-hidden { transform: translateX(-100%); }
        /* Admin Sidebar */
        .admin-sidebar { background: #111827; color: white; min-height: 100vh; }
    </style>
</head>
<body class="{% if not is_admin %}pb-24{% endif %}">

    {% if is_admin %}
    <!-- ================= ADIMIN PANEL UI ================= -->
    <div class="flex flex-col md:flex-row">
        <div class="w-full md:w-64 admin-sidebar p-5 space-y-4">
            <h2 class="text-2xl font-bold text-orange-500 border-b border-gray-700 pb-2">Admin Panel</h2>
            <nav class="space-y-2 font-semibold">
                <a href="/admin" class="block p-3 hover:bg-gray-800 rounded">📊 ড্যাশবোর্ড</a>
                <a href="/admin/settings" class="block p-3 hover:bg-gray-800 rounded">⚙️ সাইট সেটিংস</a>
                <a href="/admin/products" class="block p-3 hover:bg-gray-800 rounded">🍎 প্রোডাক্ট ম্যানেজ</a>
                <a href="/admin/categories" class="block p-3 hover:bg-gray-800 rounded">📂 ক্যাটাগরি ম্যানেজ</a>
                <a href="/admin/orders" class="block p-3 hover:bg-gray-800 rounded">📦 অর্ডার লিস্ট</a>
                <hr class="border-gray-700 my-4">
                <a href="/" class="block p-3 text-gray-400">🔙 মূল ওয়েবসাইট</a>
                <a href="/logout" class="block p-3 text-red-400">🚪 লগ আউট</a>
            </nav>
        </div>
        <div class="flex-1 p-4 md:p-10">
            {% with messages = get_flashed_messages() %}
                {% if messages %}{% for m in messages %}<div class="bg-emerald-500 text-white p-3 rounded-lg mb-5 shadow">{{ m }}</div>{% endfor %}{% endif %}
            {% endwith %}
            
            {% if admin_page == 'dashboard' %}
                <h1 class="text-3xl font-bold mb-8">Dashboard Summary</h1>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-white p-8 rounded-2xl shadow-sm border-l-8 border-blue-500">
                        <p class="text-gray-500 font-bold uppercase text-xs">Total Products</p>
                        <h3 class="text-4xl font-black mt-2">{{ p_count }}</h3>
                    </div>
                    <div class="bg-white p-8 rounded-2xl shadow-sm border-l-8 border-orange-500">
                        <p class="text-gray-500 font-bold uppercase text-xs">Total Categories</p>
                        <h3 class="text-4xl font-black mt-2">{{ c_count }}</h3>
                    </div>
                    <div class="bg-white p-8 rounded-2xl shadow-sm border-l-8 border-green-500">
                        <p class="text-gray-500 font-bold uppercase text-xs">Total Orders</p>
                        <h3 class="text-4xl font-black mt-2">{{ o_count }}</h3>
                    </div>
                </div>

            {% elif admin_page == 'settings' %}
                <h1 class="text-3xl font-bold mb-8">⚙️ General Settings</h1>
                <form action="/admin/settings/update" method="POST" class="bg-white p-8 rounded-3xl shadow-sm border space-y-6 max-w-3xl">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div><label class="block text-sm font-bold text-gray-600 mb-1">সাইটের নাম</label><input type="text" name="site_name" value="{{ settings.site_name }}" class="w-full border-2 p-3 rounded-xl outline-none focus:border-orange-500"></div>
                        <div><label class="block text-sm font-bold text-gray-600 mb-1">হোয়াটসঅ্যাপ নাম্বার</label><input type="text" name="whatsapp" value="{{ settings.whatsapp }}" class="w-full border-2 p-3 rounded-xl outline-none focus:border-orange-500"></div>
                    </div>
                    <div><label class="block text-sm font-bold text-gray-600 mb-1">উপরের নোটিশ টেক্সট</label><textarea name="notice" class="w-full border-2 p-3 rounded-xl outline-none focus:border-orange-500 h-24">{{ settings.notice }}</textarea></div>
                    <hr>
                    <h3 class="font-bold text-orange-600">পেমেন্ট মেথড নাম্বার চেঞ্জ (Checkout Page)</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div><label class="text-xs font-bold text-gray-400">বিকাশ</label><input type="text" name="bkash" value="{{ settings.bkash }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                        <div><label class="text-xs font-bold text-gray-400">নগদ</label><input type="text" name="nagad" value="{{ settings.nagad }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                        <div><label class="text-xs font-bold text-gray-400">রকেট/উপায়</label><input type="text" name="rocket" value="{{ settings.rocket }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                    </div>
                    <button class="w-full bg-orange-600 text-white py-4 rounded-2xl font-black text-lg shadow-xl shadow-orange-100 mt-5">Save All Changes</button>
                </form>

            {% elif admin_page == 'products' %}
                <div class="flex justify-between items-center mb-8">
                    <h1 class="text-3xl font-bold">🍎 Manage Products</h1>
                    <button onclick="document.getElementById('addModal').classList.toggle('hidden')" class="bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold shadow-lg">+ Add New Product</button>
                </div>

                <!-- Add Product Modal (Hidden by default) -->
                <div id="addModal" class="hidden bg-white p-8 rounded-3xl shadow-2xl border mb-10">
                    <h2 class="text-xl font-bold mb-5 border-b pb-3">নতুন প্রোডাক্ট যোগ করুন</h2>
                    <form action="/admin/product/add" method="POST" class="space-y-4 text-sm">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <input type="text" name="name" placeholder="প্রোডাক্ট নাম" class="border-2 p-3 rounded-xl" required>
                            <select name="cat" class="border-2 p-3 rounded-xl bg-white">
                                {% for c in cats %} <option>{{ c.name }}</option> {% endfor %}
                            </select>
                        </div>
                        <input type="text" name="img" placeholder="ইমেজ লিঙ্ক (Direct URL)" class="w-full border-2 p-3 rounded-xl">
                        <div class="grid grid-cols-3 gap-4">
                            <input type="number" name="price" placeholder="আসল দাম" class="border-2 p-3 rounded-xl">
                            <input type="number" name="disc" placeholder="ডিস্কাউন্ট %" class="border-2 p-3 rounded-xl">
                            <input type="text" name="weight" placeholder="ওজন (৫০০ গ্রাম)" class="border-2 p-3 rounded-xl">
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <input type="text" name="code" placeholder="কোড (P-101)" class="border-2 p-3 rounded-xl">
                            <input type="text" name="del_text" placeholder="ডেলিভারি সার্চ টেক্স" class="border-2 p-3 rounded-xl">
                        </div>
                        <textarea name="desc" placeholder="বিস্তারিত তথ্য" class="w-full border-2 p-3 rounded-xl h-24"></textarea>
                        <textarea name="policy" placeholder="অর্ডার নিয়মাবলী" class="w-full border-2 p-3 rounded-xl h-20"></textarea>
                        <button class="bg-orange-600 text-white w-full py-4 rounded-xl font-bold text-lg">Save Product</button>
                    </form>
                </div>

                <!-- Product Table -->
                <div class="bg-white rounded-3xl shadow-sm border overflow-hidden">
                    <table class="w-full text-left">
                        <thead class="bg-gray-50 border-b">
                            <tr><th class="p-4">Image</th><th class="p-4">Name</th><th class="p-4">Price</th><th class="p-4 text-center">Actions</th></tr>
                        </thead>
                        <tbody>
                            {% for p in prods %}
                            <tr class="border-b hover:bg-gray-50 transition">
                                <td class="p-4"><img src="{{ p.image }}" class="w-12 h-12 object-cover rounded-lg"></td>
                                <td class="p-4 font-bold">{{ p.name }}<br><span class="text-[10px] text-gray-400 font-normal">{{ p.category }} | {{ p.code }}</span></td>
                                <td class="p-4 font-black text-orange-600">৳ {{ p.sale_price }}</td>
                                <td class="p-4 text-center space-x-3">
                                    <a href="/admin/product/edit/{{ p._id }}" class="bg-blue-100 text-blue-600 px-3 py-1.5 rounded-lg text-xs font-bold">ইডিট (Edit)</a>
                                    <a href="/admin/product/delete/{{ p._id }}" onclick="return confirm('ডিলিট করতে চান?')" class="bg-red-100 text-red-600 px-3 py-1.5 rounded-lg text-xs font-bold">ডিলিট (Delete)</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

            {% elif admin_page == 'edit_product' %}
                <h1 class="text-3xl font-bold mb-8">🛠️ ইডিট প্রোডাক্ট: {{ p.name }}</h1>
                <form action="/admin/product/update/{{ p._id }}" method="POST" class="bg-white p-10 rounded-3xl shadow-sm border space-y-5 max-w-4xl">
                    <div class="grid grid-cols-2 gap-5">
                        <div><label class="text-xs font-bold">নাম</label><input type="text" name="name" value="{{ p.name }}" class="w-full border-2 p-4 rounded-2xl"></div>
                        <div><label class="text-xs font-bold">ক্যাটাগরি</label><select name="cat" class="w-full border-2 p-4 rounded-2xl">{% for c in cats %}<option {% if c.name == p.category %}selected{% endif %}>{{ c.name }}</option>{% endfor %}</select></div>
                    </div>
                    <div><label class="text-xs font-bold">ইমেজ লিঙ্ক</label><input type="text" name="img" value="{{ p.image }}" class="w-full border-2 p-4 rounded-2xl"></div>
                    <div class="grid grid-cols-3 gap-5">
                        <div><label class="text-xs font-bold">দাম</label><input type="number" name="price" value="{{ p.price }}" class="w-full border-2 p-4 rounded-2xl"></div>
                        <div><label class="text-xs font-bold">ডিস্কাউন্ট %</label><input type="number" name="disc" value="{{ p.discount }}" class="w-full border-2 p-4 rounded-2xl"></div>
                        <div><label class="text-xs font-bold">ওজন</label><input type="text" name="weight" value="{{ p.weight }}" class="w-full border-2 p-4 rounded-2xl"></div>
                    </div>
                    <div class="grid grid-cols-2 gap-5">
                        <div><label class="text-xs font-bold">কোড</label><input type="text" name="code" value="{{ p.code }}" class="w-full border-2 p-4 rounded-2xl"></div>
                        <div><label class="text-xs font-bold">ডেলিভারি টেক্সট</label><input type="text" name="del_text" value="{{ p.delivery_text }}" class="w-full border-2 p-4 rounded-2xl"></div>
                    </div>
                    <div><label class="text-xs font-bold">Description</label><textarea name="desc" class="w-full border-2 p-4 rounded-2xl h-32">{{ p.description }}</textarea></div>
                    <button class="w-full bg-emerald-600 text-white py-5 rounded-2xl font-black text-xl shadow-lg">আপডেট কনফার্ম করুন (Save Update)</button>
                </form>

            {% elif admin_page == 'categories' %}
                <h1 class="text-3xl font-bold mb-8">📂 ক্যাটাগরি ম্যানেজ</h1>
                <div class="bg-white p-8 rounded-3xl shadow-sm border mb-10 max-w-xl">
                    <h3 class="font-bold mb-5">নতুন ক্যাটাগরি যোগ</h3>
                    <form action="/admin/category/add" method="POST" class="flex gap-4">
                        <input type="text" name="icon" placeholder="Emoji (🥭)" class="w-20 border-2 p-3 rounded-xl text-center">
                        <input type="text" name="name" placeholder="নাম" class="flex-1 border-2 p-3 rounded-xl">
                        <button class="bg-black text-white px-8 rounded-xl font-bold">Save</button>
                    </form>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
                    {% for c in cats %}
                    <div class="bg-white p-5 rounded-2xl shadow-sm border flex justify-between items-center">
                        <span class="text-lg font-bold">{{ c.icon }} {{ c.name }}</span>
                        <a href="/admin/category/delete/{{ c._id }}" onclick="return confirm('ডিলিট?')" class="text-red-500 hover:bg-red-50 p-2 rounded-full transition">🗑️</a>
                    </div>
                    {% endfor %}
                </div>

            {% elif admin_page == 'orders' %}
                <h1 class="text-3xl font-bold mb-8">📦 কাস্টমার অর্ডার লিস্ট</h1>
                <div class="bg-white rounded-3xl shadow-sm border overflow-hidden">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-100 border-b">
                            <tr><th class="p-4">Customer</th><th class="p-4">Phone</th><th class="p-4">Product ID</th><th class="p-4">Payment</th><th class="p-4">Address</th></tr>
                        </thead>
                        <tbody>
                            {% for o in orders %}
                            <tr class="border-b hover:bg-gray-50">
                                <td class="p-4 font-bold">{{ o.name }}</td>
                                <td class="p-4 text-blue-600 font-bold">{{ o.phone }}</td>
                                <td class="p-4 text-gray-500">{{ o.p_id }}</td>
                                <td class="p-4"><span class="bg-orange-100 text-orange-600 px-3 py-1 rounded-full font-bold uppercase text-[10px]">{{ o.payment }}</span></td>
                                <td class="p-4 text-gray-400">{{ o.address }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% endif %}
        </div>
    </div>

    {% else %}
    <!-- ================= USER UI (WEBSITE) ================= -->
    <!-- Header -->
    <header class="bg-white sticky top-0 z-50 shadow-sm">
        <div class="bg-orange-500 text-white text-center py-2 text-[12px] font-bold tracking-wide">{{ settings.notice }}</div>
        <div class="container mx-auto px-4 py-4 flex justify-between items-center">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="text-2xl text-gray-700">☰</button>
                <a href="/" class="text-2xl font-black text-orange-600">{{ settings.site_name }}</a>
            </div>
            <div class="relative">🛒<span class="absolute -top-2 -right-2 bg-red-600 text-white text-[10px] rounded-full h-4 w-4 flex items-center justify-center">0</span></div>
        </div>
        <!-- Search Bar -->
        <div class="px-4 pb-4">
            <form action="/search" class="relative max-w-2xl mx-auto">
                <input type="text" name="q" placeholder="Search Product..." class="w-full bg-gray-100 border-none rounded-full py-2.5 px-6 text-sm focus:ring-1 focus:ring-orange-400">
                <button class="absolute right-4 top-2.5">🔍</button>
            </form>
        </div>
    </header>

    <!-- Side Sidebar -->
    <div id="sidebar" class="sidebar sidebar-hidden fixed top-0 left-0 h-full w-72 bg-white shadow-2xl z-[100] overflow-y-auto">
        <div class="p-5 border-b flex justify-between items-center bg-gray-50">
            <span class="font-bold text-lg text-orange-600">{{ settings.site_name }}</span>
            <button onclick="toggleSidebar()" class="text-3xl">&times;</button>
        </div>
        <ul class="p-4 space-y-1">
            {% for cat in cats %}
            <li><a href="/category/{{ cat.name }}" class="flex items-center gap-4 p-4 hover:bg-orange-50 rounded-2xl border-b border-gray-50 text-gray-700 font-bold">
                <span class="text-xl">{{ cat.icon }}</span> {{ cat.name }}
            </a></li>
            {% endfor %}
            <div class="mt-10 pt-5 border-t">
                <li><a href="/admin" class="block p-4 text-red-600 font-bold bg-red-50 rounded-2xl">⚙️ Admin Control</a></li>
                {% if session.get('user') %}
                    <li class="p-4 text-orange-600 font-bold">👤 স্বাগতম, {{ session['user'] }}</li>
                    <li><a href="/logout" class="block p-4 text-gray-500">🚪 Log Out</a></li>
                {% else %}
                    <li><a href="/login" class="block p-4 text-blue-600 font-bold">🔑 Login / Register</a></li>
                {% endif %}
            </div>
        </ul>
    </div>

    <!-- Website Content -->
    <div class="container mx-auto p-4 max-w-6xl min-h-screen">
        {% with messages = get_flashed_messages() %}
            {% if messages %}{% for m in messages %}<div class="bg-emerald-500 text-white p-3 rounded-xl mb-6 shadow-md text-center font-bold text-sm">{{ m }}</div>{% endfor %}{% endif %}
        {% endwith %}

        {% if page == 'home' %}
            <div class="mb-8 rounded-3xl overflow-hidden shadow-sm border-2 border-white">
                <img src="https://i.ibb.co/L5Bf85m/banner.jpg" class="w-full object-cover h-44 md:h-80">
            </div>
            <h2 class="text-center font-bold text-xl mb-8 text-gray-800 tracking-widest uppercase border-b-2 border-orange-100 max-w-xs mx-auto pb-2">Our Fresh Fruits</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                {% for p in products %}
                <div class="bg-white rounded-3xl shadow-sm border border-gray-100 relative overflow-hidden flex flex-col group">
                    {% if p.discount > 0 %}
                    <div class="discount-badge">{{ p.discount }}%<br>ছাড়</div>
                    {% endif %}
                    <a href="/product/{{ p._id }}"><img src="{{ p.image }}" class="w-full h-44 object-cover group-hover:scale-105 transition duration-500"></a>
                    <div class="p-4 flex-grow text-center">
                        <a href="/product/{{ p._id }}"><h3 class="text-[14px] font-bold h-10 overflow-hidden text-gray-800 leading-tight mb-2">{{ p.name }}</h3></a>
                        <div class="flex justify-center items-center gap-2">
                            <span class="text-gray-400 line-through text-[11px]">৳{{ p.price }}</span>
                            <span class="text-orange-600 font-black text-lg">৳{{ p.sale_price }}</span>
                        </div>
                    </div>
                    <a href="/product/{{ p._id }}" class="bg-orange-500 text-white text-center py-4 text-xs font-black uppercase tracking-widest hover:bg-orange-600 transition">অর্ডার করুন</a>
                </div>
                {% endfor %}
            </div>

        {% elif page == 'detail' %}
            <div class="bg-white rounded-[40px] shadow-sm p-6 md:p-10 border border-gray-50">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div class="relative bg-gray-50 rounded-[35px] p-8 border">
                        {% if p.discount > 0 %} <div class="discount-badge w-14 h-14 text-sm">{{ p.discount }}%<br>ছাড়</div> {% endif %}
                        <img src="{{ p.image }}" class="w-full max-h-[450px] object-contain mx-auto">
                    </div>
                    <div class="flex flex-col">
                        <nav class="text-[11px] text-gray-400 font-bold uppercase mb-3 tracking-widest">Home / {{ p.category }}</nav>
                        <h1 class="text-3xl font-black text-gray-900 leading-tight mb-4">{{ p.name }}</h1>
                        <div class="text-4xl font-black text-orange-600 mb-2">৳{{ p.sale_price }}</div>
                        <div class="text-gray-400 line-through font-bold mb-6">৳{{ p.price }}</div>
                        
                        <div class="inline-block bg-emerald-700 text-white text-[10px] px-4 py-1.5 rounded-md font-bold uppercase tracking-widest w-fit mb-8">প্রোডাক্ট কোড : {{ p.code }}</div>

                        <div class="mb-10">
                            <label class="text-[11px] font-black text-gray-400 block mb-2 uppercase">Size / Weight:</label>
                            <div class="border-2 border-orange-500 px-6 py-3 rounded-2xl bg-orange-50 text-orange-600 font-bold inline-block shadow-sm">📦 {{ p.weight }} - ৳{{ p.sale_price }}</div>
                        </div>

                        <div class="flex gap-4 mb-5">
                            <div class="flex border-2 border-gray-100 rounded-2xl bg-gray-50 px-3 items-center">
                                <button onclick="qChange(-1)" class="px-4 py-2 text-xl font-bold">-</button>
                                <input id="qty" type="text" value="1" class="w-12 text-center bg-transparent font-black text-lg" readonly>
                                <button onclick="qChange(1)" class="px-4 py-2 text-xl font-bold">+</button>
                            </div>
                            <button class="flex-1 bg-emerald-600 text-white py-5 rounded-2xl font-black uppercase text-sm shadow-xl">কার্টে যোগ করুন</button>
                        </div>

                        <a href="/checkout/{{ p._id }}" class="block w-full bg-orange-500 text-white text-center py-5 rounded-2xl font-black text-2xl shadow-2xl shadow-orange-100 hover:scale-[1.02] transition">অর্ডার কনফার্ম করুন</a>
                        
                        <div class="grid grid-cols-2 gap-4 mt-6">
                            <a href="tel:{{ settings.whatsapp }}" class="bg-gray-900 text-white py-4 rounded-2xl text-center text-xs font-bold flex items-center justify-center gap-2">📞 কল করুন</a>
                            <a href="https://wa.me/{{ settings.whatsapp }}" class="bg-emerald-500 text-white py-4 rounded-2xl text-center text-xs font-bold flex items-center justify-center gap-2">💬 Whatsapp</a>
                        </div>

                        <div class="mt-12 border-2 border-dashed border-orange-200 rounded-[30px] p-6 bg-orange-50/20">
                            <h4 class="font-bold text-gray-800 mb-4 border-b-2 border-orange-100 pb-2 flex items-center gap-2">🚚 কুরিয়ার ডেলিভারি খরচ:</h4>
                            <div class="overflow-hidden rounded-2xl border bg-white">
                                <table class="w-full text-sm text-left">
                                    <tr class="bg-gray-50 border-b font-bold"><td class="p-4">বিবরণ</td><td class="p-4 text-right">চার্জ</td></tr>
                                    <tr class="border-b"><td class="p-4">সর্বমোট ১ কেজি পর্যন্ত</td><td class="p-4 text-right font-black">৳ ১৩০</td></tr>
                                    <tr class="border-b"><td class="p-4">সর্বমোট ২ কেজি পর্যন্ত</td><td class="p-4 text-right font-black">৳ ১৫০</td></tr>
                                    <tr><td class="p-4">সর্বমোট ৫ কেজি পর্যন্ত</td><td class="p-4 text-right font-black">৳ ২১০</td></tr>
                                </table>
                            </div>
                            <p class="mt-4 text-[12px] text-orange-600 font-bold italic">⚠️ {{ p.delivery_text }}</p>
                        </div>
                    </div>
                </div>

                <!-- Product Tabs -->
                <div class="mt-16">
                    <div class="flex border-b text-sm font-bold overflow-x-auto whitespace-nowrap">
                        <button onclick="tabSwitch('desc')" id="btn-desc" class="tab-btn active px-8 py-5">পণ্যের বিস্তারিত (Description)</button>
                        <button onclick="tabSwitch('policy')" id="btn-policy" class="tab-btn px-8 py-5">অর্ডার নিয়মাবলী (Policy)</button>
                        <button onclick="tabSwitch('rev')" id="btn-rev" class="tab-btn px-8 py-5">রিভিউ (Review)</button>
                    </div>
                    <div id="c-desc" class="py-10 text-gray-700 leading-loose text-sm p-4 bg-orange-50/10 rounded-b-[30px] border border-t-0">{{ p.description | safe }}</div>
                    <div id="c-policy" class="hidden py-10 text-gray-700 text-sm leading-loose p-4 bg-gray-50 rounded-b-[30px] border border-t-0">{{ p.order_policy | safe }}</div>
                    <div id="c-rev" class="hidden py-20 text-center text-gray-300 italic font-bold">এখনো কোনো রিভিউ দেওয়া হয়নি।</div>
                </div>
            </div>

        {% elif page == 'checkout' %}
            <div class="max-w-xl mx-auto bg-white p-8 md:p-12 rounded-[45px] shadow-2xl border border-gray-50">
                <h2 class="text-3xl font-black mb-10 text-gray-800 border-b pb-6 flex items-center gap-3">📝 অর্ডার ফর্ম</h2>
                <div class="flex gap-5 mb-10 bg-gray-50 p-5 rounded-3xl border">
                    <img src="{{ p.image }}" class="w-20 h-20 rounded-2xl object-cover shadow-sm">
                    <div>
                        <p class="text-base font-black text-gray-800">{{ p.name }}</p>
                        <p class="text-orange-600 font-black text-xl">৳ {{ p.sale_price }}</p>
                        <p class="text-[10px] text-gray-400 font-bold uppercase mt-1">Weight: {{ p.weight }} | Code: {{ p.code }}</p>
                    </div>
                </div>
                <form action="/place-order" method="POST" class="space-y-6">
                    <input type="hidden" name="p_id" value="{{ p._id }}">
                    <div><label class="text-xs font-black text-gray-400 uppercase mb-2 block ml-2">আপনার নাম *</label>
                         <input type="text" name="name" class="w-full border-2 p-5 rounded-[22px] outline-none focus:border-orange-500 transition shadow-inner" placeholder="সম্পূর্ণ নাম লিখুন" required></div>
                    <div><label class="text-xs font-black text-gray-400 uppercase mb-2 block ml-2">মোবাইল নাম্বার *</label>
                         <input type="text" name="phone" class="w-full border-2 p-5 rounded-[22px] outline-none focus:border-orange-500 transition shadow-inner" placeholder="017xxxxxxxx" required></div>
                    <div><label class="text-xs font-black text-gray-400 uppercase mb-2 block ml-2">বিস্তারিত ঠিকানা (লোকেশন) *</label>
                         <textarea name="address" class="w-full border-2 p-5 rounded-[22px] h-28 outline-none focus:border-orange-500 transition shadow-inner" placeholder="গ্রাম/এলাকা, থানা, জেলা" required></textarea></div>
                    <div>
                        <label class="text-xs font-black text-gray-400 uppercase mb-2 block ml-2">পেমেন্ট মেথড সিলেক্ট করুন</label>
                        <div class="grid grid-cols-1 gap-3">
                            <label class="border-2 p-4 rounded-[20px] flex items-center justify-between cursor-pointer hover:border-orange-500 bg-gray-50">
                                <span class="font-bold">ক্যাশ অন ডেলিভারি (COD)</span>
                                <input type="radio" name="payment" value="COD" checked class="w-5 h-5 accent-orange-600">
                            </label>
                            <label class="border-2 p-4 rounded-[20px] flex items-center justify-between cursor-pointer hover:border-orange-500 bg-emerald-50">
                                <span class="font-bold">বিকাশ পেমেন্ট (Bkash) <br><small class="text-emerald-600">Send to: {{ settings.bkash }}</small></span>
                                <input type="radio" name="payment" value="Bkash" class="w-5 h-5 accent-emerald-600">
                            </label>
                            <label class="border-2 p-4 rounded-[20px] flex items-center justify-between cursor-pointer hover:border-orange-500 bg-red-50">
                                <span class="font-bold">নগদ পেমেন্ট (Nagad) <br><small class="text-red-600">Send to: {{ settings.nagad }}</small></span>
                                <input type="radio" name="payment" value="Nagad" class="w-5 h-5 accent-red-600">
                            </label>
                        </div>
                    </div>
                    <button class="w-full bg-orange-600 text-white py-6 rounded-[25px] font-black text-2xl shadow-2xl shadow-orange-200 mt-5 hover:scale-[1.01] transition">অর্ডার সাবমিট করুন</button>
                </form>
            </div>

        {% elif page == 'login' %}
            <div class="max-w-md mx-auto bg-white p-12 rounded-[40px] shadow-2xl text-center border mt-10">
                <h2 class="text-4xl font-black mb-10 text-gray-800">লগইন</h2>
                <form action="/auth/login" method="POST" class="space-y-6">
                    <input type="text" name="user" placeholder="Username" class="w-full border-2 p-5 rounded-[22px]" required>
                    <input type="password" name="pass" placeholder="Password" class="w-full border-2 p-5 rounded-[22px]" required>
                    <button class="w-full bg-orange-600 text-white py-5 rounded-[22px] font-black text-xl">Login</button>
                </form>
                <div class="mt-8 text-sm font-bold text-gray-500">অ্যাকাউন্ট নেই? <a href="/register" class="text-orange-600">রেজিস্ট্রেশন করুন</a></div>
            </div>

        {% elif page == 'register' %}
            <div class="max-w-md mx-auto bg-white p-12 rounded-[40px] shadow-2xl text-center border mt-10">
                <h2 class="text-4xl font-black mb-10 text-gray-800">রেজিস্ট্রেশন</h2>
                <form action="/auth/register" method="POST" class="space-y-6">
                    <input type="text" name="user" placeholder="Username দিন" class="w-full border-2 p-5 rounded-[22px]" required>
                    <input type="password" name="pass" placeholder="Password দিন" class="w-full border-2 p-5 rounded-[22px]" required>
                    <button class="w-full bg-blue-600 text-white py-5 rounded-[22px] font-black text-xl">Register Now</button>
                </form>
            </div>
        {% endif %}
    </div>

    <!-- Footer -->
    <footer class="bg-white border-t p-12 mt-20 text-center">
        <div class="text-4xl font-black text-orange-600 mb-4">{{ settings.site_name }}</div>
        <p class="text-[11px] text-gray-400 font-black uppercase tracking-[5px] mb-12">Pure & Fresh Hill Products</p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-10 text-left max-w-4xl mx-auto mb-16 text-sm">
            <div><h4 class="font-black text-gray-800 border-b-2 border-orange-100 pb-2 mb-4 uppercase">Useful Link</h4><ul class="text-gray-500 space-y-3 font-bold"><li>Contact Us</li><li>Order Procedure</li><li>Delivery Rules</li><li>Return Policy</li></ul></div>
            <div><h4 class="font-black text-gray-800 border-b-2 border-orange-100 pb-2 mb-4 uppercase">Company</h4><ul class="text-gray-500 space-y-3 font-bold"><li>All Products</li><li>Return Policy</li><li>Terms & Conditions</li><li>Privacy Policy</li></ul></div>
            <div class="col-span-2 text-right"><h4 class="font-black text-gray-800 border-b-2 border-orange-100 pb-2 mb-4 uppercase">Contact Us</h4><p class="text-gray-500 font-bold">Address: Muslimpara, Khagrachhari Sadar.<br>Hotline: {{ settings.whatsapp }}</p></div>
        </div>
        <div class="bg-orange-600 text-white p-6 text-[10px] font-black tracking-[3px] -mx-12 -mb-12 uppercase">Copyright © 2024 {{ settings.site_name }}. All rights reserved | Designed by Khagrachhari Plus</div>
    </footer>

    <!-- Bottom Nav Bar -->
    <nav class="bottom-nav">
        <button onclick="toggleSidebar()" class="nav-item"><span>☰</span><span class="mt-1 uppercase">Category</span></button>
        <a href="https://wa.me/{{ settings.whatsapp }}" class="nav-item text-emerald-500"><span>💬</span><span class="mt-1 uppercase">Whatsapp</span></a>
        <a href="/" class="flex flex-col items-center -mt-8"><div class="home-center">🏠</div><span class="mt-4 font-black text-orange-600 text-[10px] uppercase tracking-widest">Home</span></a>
        <div class="nav-item"><span>🛒</span><span class="mt-1 uppercase text-gray-400">Cart (0)</span></div>
        <a href="/login" class="nav-item text-blue-600"><span>👤</span><span class="mt-1 uppercase">Login</span></a>
    </nav>
    {% endif %}

    <script>
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('sidebar-hidden'); }
        function tabSwitch(n) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('[id^="c-"]').forEach(c => c.classList.add('hidden'));
            document.getElementById('btn-'+n).classList.add('active');
            document.getElementById('c-'+n).classList.remove('hidden');
        }
        function qChange(v) {
            let q = document.getElementById('qty');
            let val = parseInt(q.value) + v;
            if(val >= 1) q.value = val;
        }
    </script>
</body>
</html>
"""

# --- Routes & Logic ---

# ইউজার রাউটস
@app.route('/')
def home():
    settings = get_settings()
    prods = list(products_col.find())
    cats = list(categories_col.find())
    return render_template_string(MASTER_HTML, page='home', products=prods, cats=cats, settings=settings, is_admin=False)

@app.route('/category/<name>')
def category_view(name):
    settings = get_settings()
    prods = list(products_col.find({"category": name}))
    cats = list(categories_col.find())
    return render_template_string(MASTER_HTML, page='home', products=prods, cats=cats, settings=settings, is_admin=False)

@app.route('/product/<id>')
def product_detail(id):
    settings = get_settings()
    cats = list(categories_col.find())
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(MASTER_HTML, page='detail', p=p, cats=cats, settings=settings, is_admin=False)

@app.route('/checkout/<id>')
def checkout(id):
    settings = get_settings()
    cats = list(categories_col.find())
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(MASTER_HTML, page='checkout', p=p, cats=cats, settings=settings, is_admin=False)

@app.route('/place-order', methods=['POST'])
def place_order():
    orders_col.insert_one({"p_id": request.form['p_id'], "name": request.form['name'], "phone": request.form['phone'], "address": request.form['address'], "payment": request.form['payment'], "date": datetime.now()})
    flash("ধন্যবাদ! আপনার অর্ডারটি সফলভাবে গ্রহণ করা হয়েছে।")
    return redirect('/')

@app.route('/search')
def search():
    q = request.args.get('q', '')
    settings = get_settings()
    prods = list(products_col.find({"name": {"$regex": q, "$options": "i"}}))
    cats = list(categories_col.find())
    return render_template_string(MASTER_HTML, page='home', products=prods, cats=cats, settings=settings, is_admin=False)

# অথেন্টিকেশন
@app.route('/login')
def login_page(): return render_template_string(MASTER_HTML, page='login', cats=list(categories_col.find()), settings=get_settings(), is_admin=False)

@app.route('/register')
def reg_page(): return render_template_string(MASTER_HTML, page='register', cats=list(categories_col.find()), settings=get_settings(), is_admin=False)

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

# --- এডমিন রাউটস (সম্পূর্ণ ফিচার সহ) ---

@app.route('/admin')
def admin_dash():
    if session.get('role') != 'admin':
        # প্রথমবার ব্যবহারের জন্য এটি আনকমেন্ট করে এডমিন হতে পারেন
        # session['role'] = 'admin'
        return "Access Denied! লগইন করে ইউজার রোল ডাটাবেস থেকে admin করুন।"
    settings = get_settings()
    p_count = products_col.count_documents({})
    c_count = categories_col.count_documents({})
    o_count = orders_col.count_documents({})
    return render_template_string(MASTER_HTML, admin_page='dashboard', settings=settings, is_admin=True, p_count=p_count, c_count=c_count, o_count=o_count)

# ১. সেটিংস আপডেট (নাম, নাম্বার, নোটিশ)
@app.route('/admin/settings')
def admin_settings():
    if session.get('role') != 'admin': return redirect('/login')
    return render_template_string(MASTER_HTML, admin_page='settings', settings=get_settings(), is_admin=True)

@app.route('/admin/settings/update', methods=['POST'])
def update_settings():
    updated = {
        "site_name": request.form['site_name'],
        "notice": request.form['notice'],
        "whatsapp": request.form['whatsapp'],
        "bkash": request.form['bkash'],
        "nagad": request.form['nagad'],
        "rocket": request.form['rocket']
    }
    settings_col.update_one({"type": "general"}, {"$set": updated})
    flash("সাইট সেটিংস আপডেট হয়েছে!")
    return redirect('/admin/settings')

# ২. প্রোডাক্ট ম্যানেজ (Add, Edit, Delete)
@app.route('/admin/products')
def admin_products():
    if session.get('role') != 'admin': return redirect('/login')
    prods = list(products_col.find())
    cats = list(categories_col.find())
    return render_template_string(MASTER_HTML, admin_page='products', prods=prods, cats=cats, settings=get_settings(), is_admin=True)

@app.route('/admin/product/add', methods=['POST'])
def add_product():
    price = float(request.form['price'])
    disc = float(request.form['disc'] or 0)
    products_col.insert_one({
        "name": request.form['name'], "image": request.form['img'], "category": request.form['cat'],
        "price": price, "discount": disc, "sale_price": int(price - (price * disc / 100)),
        "code": request.form['code'], "weight": request.form['weight'],
        "description": request.form['desc'].replace('\n', '<br>'),
        "order_policy": request.form['policy'].replace('\n', '<br>'),
        "delivery_text": request.form['del_text']
    })
    flash("নতুন প্রোডাক্ট যুক্ত হয়েছে!")
    return redirect('/admin/products')

@app.route('/admin/product/edit/<id>')
def edit_product_page(id):
    if session.get('role') != 'admin': return redirect('/login')
    p = products_col.find_one({"_id": ObjectId(id)})
    cats = list(categories_col.find())
    return render_template_string(MASTER_HTML, admin_page='edit_product', p=p, cats=cats, settings=get_settings(), is_admin=True)

@app.route('/admin/product/update/<id>', methods=['POST'])
def update_product(id):
    price = float(request.form['price'])
    disc = float(request.form['disc'] or 0)
    updated = {
        "name": request.form['name'], "image": request.form['img'], "category": request.form['cat'],
        "price": price, "discount": disc, "sale_price": int(price - (price * disc / 100)),
        "code": request.form['code'], "weight": request.form['weight'],
        "description": request.form['desc'].replace('\n', '<br>'),
        "delivery_text": request.form['del_text']
    }
    products_col.update_one({"_id": ObjectId(id)}, {"$set": updated})
    flash("প্রোডাক্ট আপডেট সফল!")
    return redirect('/admin/products')

@app.route('/admin/product/delete/<id>')
def delete_product(id):
    products_col.delete_one({"_id": ObjectId(id)})
    flash("প্রোডাক্ট ডিলিট করা হয়েছে!")
    return redirect('/admin/products')

# ৩. ক্যাটাগরি ম্যানেজ (Add, Delete)
@app.route('/admin/categories')
def admin_cats():
    if session.get('role') != 'admin': return redirect('/login')
    cats = list(categories_col.find())
    return render_template_string(MASTER_HTML, admin_page='categories', cats=cats, settings=get_settings(), is_admin=True)

@app.route('/admin/category/add', methods=['POST'])
def add_cat():
    categories_col.insert_one({"name": request.form['name'], "icon": request.form['icon'] or '🥭'})
    flash("ক্যাটাগরি যুক্ত হয়েছে!")
    return redirect('/admin/categories')

@app.route('/admin/category/delete/<id>')
def delete_cat(id):
    categories_col.delete_one({"_id": ObjectId(id)})
    flash("ক্যাটাগরি ডিলিট করা হয়েছে!")
    return redirect('/admin/categories')

# ৪. অর্ডার লিস্ট
@app.route('/admin/orders')
def admin_orders():
    if session.get('role') != 'admin': return redirect('/login')
    ords = list(orders_col.find().sort("date", -1))
    return render_template_string(MASTER_HTML, admin_page='orders', orders=ords, settings=get_settings(), is_admin=True)

if __name__ == "__main__":
    app.run(debug=True)
