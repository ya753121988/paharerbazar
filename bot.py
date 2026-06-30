import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- অ্যাপ্লিকেশন সেটআপ ---
app = Flask(__name__)
app.secret_key = "paharer_bazar_mega_ultra_key_2024"

# --- মংগোডিবি কানেকশন (এখানে আপনার কানেকশন স্ট্রিংটি অবশ্যই বসাবেন) ---
MONGO_URI = "mongodb+srv://YOUR_USER:YOUR_PASSWORD@cluster0.mongodb.net/shop_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client['paharer_bazar_final']
products_col = db['products']
categories_col = db['categories']
users_col = db['users']
orders_col = db['orders']

# --- সম্পূর্ণ ডিজাইন ও ফাংশনালিটি (HTML/CSS/JS) ---
# এটি একটি বিশাল স্ট্রিং যা পুরো সাইটের চেহারা নিয়ন্ত্রণ করবে।
MASTER_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paharer Bazar | পাহাড়ের তাজা ফলের সমাহার</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Hind Siliguri', sans-serif; background-color: #f9fafb; color: #1f2937; }
        
        /* লাল গোল প্রিমিয়াম অটো পোস্টার/ডিস্কাউন্ট ব্যাজ */
        .premium-discount-badge {
            background: radial-gradient(circle, #ff0000 0%, #cc0000 100%);
            color: white; border-radius: 50%; width: 48px; height: 48px;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 800; position: absolute;
            top: 10px; right: 10px; z-index: 20; line-height: 1.1;
            text-align: center; box-shadow: 0 4px 10px rgba(255,0,0,0.3);
            border: 2px solid white; animation: pulse-red 2s infinite;
        }
        @keyframes pulse-red { 0% {transform: scale(1);} 50% {transform: scale(1.1);} 100% {transform: scale(1);} }

        /* বটম নেভিগেশন */
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #e5e7eb; 
                      z-index: 100; display: flex; justify-content: space-around; padding: 10px 0; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
        .nav-btn { display: flex; flex-direction: column; align-items: center; color: #6b7280; font-size: 10px; font-weight: 600; }
        .nav-btn.active { color: #f97316; }
        .home-center-btn { margin-top: -35px; background: #f97316; color: white; padding: 12px; border-radius: 50%; 
                           box-shadow: 0 4px 15px rgba(249,115,22,0.4); border: 4px solid white; }

        /* ট্যাব ও সাইডবার */
        .tab-active { border-bottom: 3px solid #f97316; color: #f97316; font-weight: 700; }
        .sidebar { transition: transform 0.3s ease-in-out; }
        .sidebar-hidden { transform: translateX(-100%); }
    </style>
</head>
<body class="pb-24">

    <!-- Top Announcement -->
    <div class="bg-orange-500 text-white text-center py-2 text-[12px] font-bold tracking-wide sticky top-0 z-[60]">
        স্বাগতম || সারা বাংলাদেশে ক্যাশ অন ডেলিভারি এবং অনলাইন পেমেন্ট সুবিধা
    </div>

    <!-- Main Header -->
    <header class="bg-white shadow-sm sticky top-8 z-50">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <button onclick="toggleSidebar()" class="text-2xl text-gray-700">☰</button>
            <a href="/" class="text-2xl font-black text-orange-600 flex items-center">
                <span>Paharer</span><span class="text-gray-800 ml-1">Bazar</span>
            </a>
            <div class="flex items-center gap-4">
                <div class="relative">
                    <span class="text-2xl">🛒</span>
                    <span class="absolute -top-2 -right-2 bg-red-600 text-white text-[10px] rounded-full h-4 w-4 flex items-center justify-center">0</span>
                </div>
            </div>
        </div>
        <!-- Search Bar -->
        <div class="px-4 pb-3">
            <form action="/search" method="GET" class="relative">
                <input type="text" name="q" placeholder="Search Product..." class="w-full bg-gray-100 border border-transparent rounded-lg py-2 px-4 text-sm focus:outline-none focus:border-orange-500 focus:bg-white transition">
                <button class="absolute right-3 top-2 text-gray-400">🔍</button>
            </form>
        </div>
    </header>

    <!-- Side Menu (Sidebar) -->
    <div id="sidebar" class="sidebar sidebar-hidden fixed top-0 left-0 h-full w-72 bg-white shadow-2xl z-[100] overflow-y-auto">
        <div class="p-5 border-b flex justify-between items-center bg-gray-50">
            <span class="font-bold text-lg text-gray-800">সব ক্যাটাগরি</span>
            <button onclick="toggleSidebar()" class="text-3xl font-light">&times;</button>
        </div>
        <ul class="p-4 space-y-2">
            {% for cat in categories %}
            <li>
                <a href="/category/{{ cat.name }}" class="flex items-center gap-4 p-3 hover:bg-orange-50 rounded-xl transition border-b border-gray-50">
                    <span class="text-xl">{{ cat.icon }}</span>
                    <span class="font-semibold text-gray-700">{{ cat.name }}</span>
                </a>
            </li>
            {% endfor %}
            <div class="mt-10 pt-5 border-t space-y-3">
                {% if session.get('user') %}
                    <li class="px-3 font-bold text-orange-600">👤 {{ session['user'] }}</li>
                    {% if session.get('role') == 'admin' %}
                    <li><a href="/admin" class="block px-3 py-2 text-red-600 font-bold bg-red-50 rounded">⚙️ Admin Panel</a></li>
                    {% endif %}
                    <li><a href="/logout" class="block px-3 py-2 text-gray-500">🚪 Logout</a></li>
                {% else %}
                    <li><a href="/login" class="block px-3 py-2 text-blue-600 font-bold">🔑 Login / Register</a></li>
                {% endif %}
            </div>
        </ul>
    </div>

    <!-- Page Content Container -->
    <div class="container mx-auto p-4 max-w-5xl">
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                <div class="bg-green-100 border-l-4 border-green-500 text-green-700 p-3 mb-4 rounded shadow-sm text-sm">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% if page == 'home' %}
            <!-- Hero Banner -->
            <div class="mb-8 rounded-2xl overflow-hidden shadow-lg">
                <img src="https://i.ibb.co/L5Bf85m/banner.jpg" class="w-full object-cover h-40 md:h-64">
            </div>

            <!-- Product Grid -->
            <h2 class="text-center font-bold text-xl mb-6 text-gray-800 flex items-center justify-center gap-3">
                <span class="h-[2px] w-8 bg-orange-300"></span> সব পণ্য <span class="h-[2px] w-8 bg-orange-300"></span>
            </h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                {% for p in products %}
                <div class="bg-white rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden flex flex-col group">
                    {% if p.discount > 0 %}
                    <div class="premium-discount-badge">{{ p.discount }}%<br>ছাড়</div>
                    {% endif %}
                    <a href="/product/{{ p._id }}" class="overflow-hidden">
                        <img src="{{ p.image }}" class="w-full h-44 object-cover group-hover:scale-105 transition duration-500">
                    </a>
                    <div class="p-3 flex-grow">
                        <a href="/product/{{ p._id }}">
                            <h3 class="text-[14px] font-bold leading-tight h-10 overflow-hidden text-gray-800 hover:text-orange-600 transition">{{ p.name }}</h3>
                        </a>
                        <div class="mt-2 flex items-center gap-2">
                            <span class="text-gray-400 line-through text-[11px]">৳{{ p.price }}</span>
                            <span class="text-orange-600 font-black text-base">৳{{ p.sale_price }}</span>
                        </div>
                    </div>
                    <a href="/product/{{ p._id }}" class="bg-orange-500 text-white text-center py-3 text-xs font-black uppercase tracking-widest hover:bg-orange-600 transition">অর্ডার করুন</a>
                </div>
                {% endfor %}
            </div>

        {% elif page == 'product_detail' %}
            <!-- Detail Page -->
            <div class="bg-white rounded-3xl shadow-sm p-4 md:p-8">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <!-- Image Section -->
                    <div class="relative bg-gray-50 rounded-2xl p-4">
                        {% if p.discount > 0 %} <div class="premium-discount-badge w-14 h-14 text-sm">{{ p.discount }}%<br>ছাড়</div> {% endif %}
                        <img src="{{ p.image }}" class="w-full max-h-[400px] object-contain mx-auto">
                    </div>
                    <!-- Info Section -->
                    <div>
                        <nav class="text-[11px] text-gray-400 font-bold uppercase mb-2 tracking-wider">Home / {{ p.category }}</nav>
                        <h1 class="text-2xl font-black text-gray-900 leading-tight">{{ p.name }}</h1>
                        <div class="flex items-center gap-4 mt-3">
                            <div class="text-3xl font-black text-orange-600">৳{{ p.sale_price }}</div>
                            <div class="text-gray-400 line-through font-bold">৳{{ p.price }}</div>
                        </div>
                        
                        <div class="inline-block bg-gray-900 text-white text-[10px] px-3 py-1 rounded mt-4 font-bold tracking-widest uppercase">
                            প্রোডাক্ট কোড : {{ p.code }}
                        </div>

                        <div class="mt-6">
                            <label class="text-[11px] font-black text-gray-500 uppercase tracking-widest block mb-2">Select Weight / Size</label>
                            <div class="inline-flex items-center border-2 border-orange-500 px-4 py-2 rounded-xl bg-orange-50 text-orange-600 font-bold">
                                📦 {{ p.weight }} - ৳{{ p.sale_price }}
                            </div>
                        </div>

                        <div class="mt-8 flex gap-4">
                            <div class="flex items-center border-2 border-gray-100 rounded-xl bg-gray-50">
                                <button onclick="changeQty(-1)" class="px-4 py-2 text-xl font-bold">-</button>
                                <input id="qty" type="text" value="1" class="w-12 text-center bg-transparent font-black text-lg" readonly>
                                <button onclick="changeQty(1)" class="px-4 py-2 text-xl font-bold">+</button>
                            </div>
                            <button class="flex-1 bg-emerald-600 text-white py-4 rounded-xl font-black text-sm uppercase shadow-lg shadow-emerald-100">কার্টে যোগ করুন</button>
                        </div>

                        <a href="/checkout/{{ p._id }}" class="block w-full bg-orange-500 text-white text-center py-4 rounded-xl font-black mt-4 shadow-xl shadow-orange-100 text-xl hover:bg-orange-600 transition">অর্ডার করুন</a>

                        <div class="grid grid-cols-2 gap-3 mt-4">
                            <a href="tel:01511820222" class="bg-gray-800 text-white py-3 rounded-xl text-center text-xs font-bold flex items-center justify-center gap-2">📞 কল করুন</a>
                            <a href="https://wa.me/8801511820222" class="bg-green-500 text-white py-3 rounded-xl text-center text-xs font-bold flex items-center justify-center gap-2">💬 WhatsApp</a>
                        </div>
                    </div>
                </div>

                <!-- Delivery & Rules -->
                <div class="mt-10 border-2 border-dashed border-gray-100 rounded-3xl p-5 bg-gray-50">
                    <h3 class="font-black text-sm mb-3 flex items-center gap-2">🚚 ডেলিভারি চার্জ চার্ট:</h3>
                    <div class="overflow-hidden rounded-xl border border-gray-200">
                        <table class="w-full text-xs text-left bg-white">
                            <tr class="bg-gray-100 border-b"><th class="p-3">ওজন রেঞ্জ</th><th class="p-3 text-right">চার্জ</th></tr>
                            <tr class="border-b"><td class="p-3">সর্বমোট ১ কেজি পর্যন্ত</td><td class="p-3 text-right font-bold">৳ ১৩০</td></tr>
                            <tr class="border-b"><td class="p-3">সর্বমোট ২ কেজি পর্যন্ত</td><td class="p-3 text-right font-bold">৳ ১৫০</td></tr>
                            <tr><td class="p-3">সর্বমোট ৫ কেজি পর্যন্ত</td><td class="p-3 text-right font-bold">৳ ২১০</td></tr>
                        </table>
                    </div>
                    <p class="mt-3 text-[11px] text-orange-600 font-bold">⚠️ অর্ডার নিয়ম: {{ p.delivery_text or 'অর্ডার করতে উপরের বাটনে ক্লিক করুন।' }}</p>
                </div>

                <!-- Tabs Section -->
                <div class="mt-12">
                    <div class="flex border-b text-sm font-bold overflow-x-auto whitespace-nowrap">
                        <button onclick="switchTab('desc')" id="btn-desc" class="tab-active px-6 py-4">পণ্যের বিস্তারিত</button>
                        <button onclick="switchTab('policy')" id="btn-policy" class="px-6 py-4">অর্ডার নিয়মাবলী</button>
                        <button onclick="switchTab('rev')" id="btn-rev" class="px-6 py-4">রিভিউ (০)</button>
                    </div>
                    <div id="cont-desc" class="py-8 text-sm text-gray-600 leading-relaxed space-y-4">
                        <div class="p-4 bg-orange-50 rounded-2xl border-l-4 border-orange-400">
                            {{ p.description | safe }}
                        </div>
                    </div>
                    <div id="cont-policy" class="hidden py-8 text-sm text-gray-600 space-y-4">
                        <div class="p-4 bg-blue-50 rounded-2xl border-l-4 border-blue-400">
                            {{ p.order_policy | safe }}
                        </div>
                    </div>
                    <div id="cont-rev" class="hidden py-16 text-center text-gray-400">
                        <img src="https://cdn-icons-png.flaticon.com/512/1435/1435156.png" class="w-20 mx-auto opacity-20 mb-4">
                        <p class="font-bold">এখনো কোনো রিভিউ দেওয়া হয়নি।</p>
                    </div>
                </div>
            </div>

        {% elif page == 'checkout' %}
            <!-- Checkout Form -->
            <div class="max-w-2xl mx-auto bg-white p-6 md:p-10 rounded-3xl shadow-xl">
                <h2 class="text-2xl font-black mb-6 text-gray-800 border-b pb-4">অর্ডার ফর্ম পূরণ করুন</h2>
                <div class="flex gap-4 mb-8 bg-gray-50 p-4 rounded-2xl border border-gray-100">
                    <img src="{{ p.image }}" class="w-20 h-20 rounded-xl object-cover shadow-sm">
                    <div>
                        <p class="text-sm font-black text-gray-800">{{ p.name }}</p>
                        <p class="text-orange-600 font-black text-lg">৳ {{ p.sale_price }}</p>
                        <p class="text-[10px] text-gray-400 uppercase font-bold">Qty: 1 | Weight: {{ p.weight }}</p>
                    </div>
                </div>
                <form action="/place-order" method="POST" class="space-y-5">
                    <input type="hidden" name="p_id" value="{{ p._id }}">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div>
                            <label class="text-[11px] font-black text-gray-500 uppercase ml-1">আপনার নাম *</label>
                            <input type="text" name="name" class="w-full border-2 border-gray-100 p-4 rounded-2xl mt-1 focus:border-orange-500 transition outline-none" placeholder="নাম লিখুন" required>
                        </div>
                        <div>
                            <label class="text-[11px] font-black text-gray-500 uppercase ml-1">মোবাইল নাম্বার *</label>
                            <input type="text" name="phone" class="w-full border-2 border-gray-100 p-4 rounded-2xl mt-1 focus:border-orange-500 transition outline-none" placeholder="017xxxxxxxx" required>
                        </div>
                    </div>
                    <div>
                        <label class="text-[11px] font-black text-gray-500 uppercase ml-1">আপনার লোকেশন/ঠিকানা *</label>
                        <textarea name="address" class="w-full border-2 border-gray-100 p-4 rounded-2xl mt-1 focus:border-orange-500 transition outline-none h-24" placeholder="গ্রাম/এলাকা, থানা, জেলা লিখুন" required></textarea>
                    </div>
                    <div>
                        <label class="text-[11px] font-black text-gray-500 uppercase ml-1">পেমেন্ট মেথড সিলেক্ট করুন</label>
                        <select name="payment" class="w-full border-2 border-gray-100 p-4 rounded-2xl mt-1 bg-white focus:border-orange-500 outline-none font-bold">
                            <option value="COD">ক্যাশ অন ডেলিভারি (পণ্য বুঝে নিয়ে টাকা দেবেন)</option>
                            <option value="Bkash">বিকাশ (Bkash)</option>
                            <option value="Nagad">নগদ (Nagad)</option>
                            <option value="Rocket">রকেট / উপায় (Rocket/Upay)</option>
                        </select>
                    </div>
                    <button class="w-full bg-orange-600 text-white py-5 rounded-2xl font-black text-xl shadow-2xl shadow-orange-200 mt-6 hover:bg-orange-700 transition transform hover:scale-[1.01]">অর্ডার কনফার্ম করুন</button>
                </form>
            </div>

        {% elif page == 'admin' %}
            <!-- Full Control Admin Panel -->
            <div class="max-w-4xl mx-auto space-y-10">
                <div class="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <h2 class="font-black text-xl mb-6 text-emerald-600">📂 ক্যাটাগরি তৈরি করুন</h2>
                    <form action="/admin/add-cat" method="POST" class="flex flex-wrap gap-4">
                        <input type="text" name="icon" placeholder="ইমোজি (যেমন: 🥭)" class="w-20 border-2 p-3 rounded-xl text-center">
                        <input type="text" name="name" placeholder="ক্যাটাগরি নাম" class="flex-1 min-w-[200px] border-2 p-3 rounded-xl">
                        <button class="bg-emerald-600 text-white px-8 rounded-xl font-bold">Add Category</button>
                    </form>
                </div>

                <div class="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <h2 class="font-black text-xl mb-6 text-orange-600">🍎 নতুন প্রোডাক্ট অ্যাড করুন</h2>
                    <form action="/admin/add-product" method="POST" class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <input type="text" name="name" placeholder="ফলের নাম (পূর্ণ)" class="border-2 p-4 rounded-xl w-full" required>
                            <select name="cat" class="border-2 p-4 rounded-xl w-full bg-white">
                                {% for c in categories %} <option>{{ c.name }}</option> {% endfor %}
                            </select>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <input type="text" name="img" placeholder="ইমেজ লিঙ্ক (Imgur URL)" class="border-2 p-4 rounded-xl w-full">
                            <input type="text" name="code" placeholder="প্রোডাক্ট কোড (যেমন: P-100)" class="border-2 p-4 rounded-xl w-full">
                        </div>
                        <div class="grid grid-cols-3 gap-4">
                            <input type="number" name="price" placeholder="আসল দাম" class="border-2 p-4 rounded-xl">
                            <input type="number" name="disc" placeholder="ডিস্কাউন্ট %" class="border-2 p-4 rounded-xl">
                            <input type="text" name="weight" placeholder="ওজন (৫০০ গ্রাম)" class="border-2 p-4 rounded-xl">
                        </div>
                        <textarea name="desc" placeholder="ফলের বিস্তারিত তথ্য (Description)" class="w-full border-2 p-4 rounded-xl h-32"></textarea>
                        <textarea name="policy" placeholder="অর্ডার করার নিয়ম (Order Policy)" class="w-full border-2 p-4 rounded-xl h-24"></textarea>
                        <input type="text" name="del_text" placeholder="ডেলিভারি সার্চ টেক্স (Delivery Text)" class="w-full border-2 p-4 rounded-xl">
                        <button class="w-full bg-orange-600 text-white py-5 rounded-2xl font-black text-lg shadow-lg">পণ্যটি সাইটে পাবলিশ করুন</button>
                    </form>
                </div>

                <div class="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <h2 class="font-black text-xl mb-6 text-blue-600">📋 অর্ডার লিস্ট</h2>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr class="bg-gray-50 border-b"><th class="p-4">Customer</th><th class="p-4">Product ID</th><th class="p-4">Method</th><th class="p-4">Status</th></tr>
                            </thead>
                            <tbody>
                                {% for o in orders %}
                                <tr class="border-b hover:bg-gray-50">
                                    <td class="p-4 font-bold">{{ o.name }}<br><span class="text-blue-500">{{ o.phone }}</span><br><span class="text-gray-400 font-normal">{{ o.address }}</span></td>
                                    <td class="p-4 text-gray-600">{{ o.p_id }}</td>
                                    <td class="p-4"><span class="bg-gray-100 px-2 py-1 rounded">{{ o.payment }}</span></td>
                                    <td class="p-4"><span class="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full font-bold">Pending</span></td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        {% elif page == 'login' %}
            <!-- Registration & Login -->
            <div class="max-w-md mx-auto bg-white p-10 rounded-3xl shadow-2xl">
                <h2 class="text-3xl font-black mb-8 text-center text-gray-800">লগইন</h2>
                <form action="/auth/login" method="POST" class="space-y-5">
                    <input type="text" name="user" placeholder="ইউজারনেম" class="w-full border-2 p-4 rounded-2xl" required>
                    <input type="password" name="pass" placeholder="পাসওয়ার্ড" class="w-full border-2 p-4 rounded-2xl" required>
                    <button class="w-full bg-orange-600 text-white py-4 rounded-2xl font-black">Login</button>
                </form>
                <div class="mt-8 text-center text-sm text-gray-500">
                    অ্যাকাউন্ট নেই? <a href="/register" class="text-orange-600 font-bold">নতুন অ্যাকাউন্ট খুলুন</a>
                </div>
            </div>

        {% elif page == 'register' %}
            <div class="max-w-md mx-auto bg-white p-10 rounded-3xl shadow-2xl">
                <h2 class="text-3xl font-black mb-8 text-center text-gray-800">রেজিস্ট্রেশন</h2>
                <form action="/auth/register" method="POST" class="space-y-5">
                    <input type="text" name="user" placeholder="ইউজারনেম দিন" class="w-full border-2 p-4 rounded-2xl" required>
                    <input type="password" name="pass" placeholder="পাসওয়ার্ড দিন" class="w-full border-2 p-4 rounded-2xl" required>
                    <button class="w-full bg-blue-600 text-white py-4 rounded-2xl font-black">Register Now</button>
                </form>
            </div>
        {% endif %}
    </div>

    <!-- Professional Footer -->
    <footer class="bg-white border-t border-gray-100 p-10 mt-20 text-center">
        <div class="text-3xl font-black text-orange-600 mb-2">Paharer Bazar</div>
        <p class="text-xs text-gray-400 font-bold mb-8 uppercase tracking-[4px]">Pure Hill Products</p>
        
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-left max-w-4xl mx-auto mb-12">
            <div>
                <h4 class="font-black text-gray-800 border-b-2 border-orange-200 pb-2 mb-4">Useful Link</h4>
                <ul class="text-[11px] font-bold text-gray-500 space-y-3">
                    <li>Contact Us</li><li>Order Procedure</li><li>Delivery Rules</li><li>Return Policy</li>
                </ul>
            </div>
            <div>
                <h4 class="font-black text-gray-800 border-b-2 border-orange-200 pb-2 mb-4">Support</h4>
                <ul class="text-[11px] font-bold text-gray-500 space-y-3">
                    <li>All Products</li><li>Return Policy</li><li>Terms & Conditions</li><li>Privacy Policy</li>
                </ul>
            </div>
            <div class="col-span-2">
                <h4 class="font-black text-gray-800 border-b-2 border-orange-200 pb-2 mb-4">Follow Us</h4>
                <div class="flex gap-4 mt-2">
                    <span class="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">f</span>
                    <span class="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold">w</span>
                    <span class="w-10 h-10 bg-red-600 text-white rounded-full flex items-center justify-center font-bold">y</span>
                    <span class="w-10 h-10 bg-gradient-to-tr from-yellow-500 to-purple-600 text-white rounded-full flex items-center justify-center font-bold">i</span>
                </div>
                <p class="text-[11px] text-gray-400 mt-5 font-bold">Address: Muslimpara, Khagrachhari Sadar.<br>Hotline: +8801511820222</p>
            </div>
        </div>
        <div class="bg-orange-500 text-white p-5 text-[10px] font-black uppercase tracking-[2px] -mx-10 -mb-10">
            © 2024 Paharer Bazar. All rights reserved | Designed by Khagrachhari Plus
        </div>
    </footer>

    <!-- Fixed Bottom Nav -->
    <nav class="bottom-nav">
        <button onclick="toggleSidebar()" class="nav-btn">
            <span class="text-2xl">☰</span><span>Category</span>
        </button>
        <a href="https://wa.me/8801511820222" class="nav-btn">
            <span class="text-2xl">💬</span><span>Whatsapp</span>
        </a>
        <a href="/" class="nav-btn">
            <div class="home-center-btn">🏠</div>
            <span class="mt-4 font-black text-orange-600">Home</span>
        </a>
        <div class="nav-btn relative">
            <span class="text-2xl">🛒</span><span>Cart (0)</span>
        </div>
        <a href="/login" class="nav-btn">
            <span class="text-2xl">👤</span><span>Login</span>
        </a>
    </nav>

    <script>
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('sidebar-hidden'); }
        
        function changeQty(v) {
            let q = document.getElementById('qty');
            let val = parseInt(q.value) + v;
            if(val >= 1) q.value = val;
        }

        function switchTab(name) {
            document.querySelectorAll('[id^="btn-"]').forEach(b => b.classList.remove('tab-active'));
            document.querySelectorAll('[id^="cont-"]').forEach(c => c.classList.add('hidden'));
            document.getElementById('btn-'+name).classList.add('tab-active');
            document.getElementById('cont-'+name).classList.remove('hidden');
        }
    </script>
</body>
</html>
"""

# --- রুটিং এবং লজিক (Routing & Business Logic) ---

@app.route('/')
def index():
    cats = list(categories_col.find())
    prods = list(products_col.find())
    return render_template_string(MASTER_HTML, page='home', products=prods, categories=cats)

@app.route('/category/<name>')
def category_view(name):
    cats = list(categories_col.find())
    prods = list(products_col.find({"category": name}))
    return render_template_string(MASTER_HTML, page='home', products=prods, categories=cats)

@app.route('/product/<id>')
def product_detail(id):
    cats = list(categories_col.find())
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(MASTER_HTML, page='product_detail', p=p, categories=cats)

@app.route('/checkout/<id>')
def checkout(id):
    cats = list(categories_col.find())
    p = products_col.find_one({"_id": ObjectId(id)})
    return render_template_string(MASTER_HTML, page='checkout', p=p, categories=cats)

@app.route('/place-order', methods=['POST'])
def place_order():
    order = {
        "p_id": request.form['p_id'],
        "name": request.form['name'],
        "phone": request.form['phone'],
        "address": request.form['address'],
        "payment": request.form['payment'],
        "status": "Pending",
        "date": datetime.now()
    }
    orders_col.insert_one(order)
    flash("ধন্যবাদ! আপনার অর্ডারটি সফলভাবে গ্রহণ করা হয়েছে।")
    return redirect('/')

@app.route('/login')
def login_page():
    return render_template_string(MASTER_HTML, page='login', categories=list(categories_col.find()))

@app.route('/register')
def reg_page():
    return render_template_string(MASTER_HTML, page='register', categories=list(categories_col.find()))

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
def logout():
    session.clear()
    return redirect('/')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    cats = list(categories_col.find())
    prods = list(products_col.find({"name": {"$regex": query, "$options": "i"}}))
    return render_template_string(MASTER_HTML, page='home', products=prods, categories=cats)

# --- অ্যাডমিন প্যানেল কন্ট্রোল ---

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':
        # প্রথমবার ব্যবহারের জন্য এটি আনকমেন্ট করতে পারেন যাতে আপনি এডমিন হতে পারেন
        # session['role'] = 'admin' 
        return "Access Denied!"
    cats = list(categories_col.find())
    ords = list(orders_col.find().sort("date", -1))
    return render_template_string(MASTER_HTML, page='admin', categories=cats, orders=ords)

@app.route('/admin/add-cat', methods=['POST'])
def add_cat():
    categories_col.insert_one({"name": request.form['name'], "icon": request.form['icon'] or '🥭'})
    return redirect('/admin')

@app.route('/admin/add-product', methods=['POST'])
def add_product():
    price = float(request.form['price'])
    disc = float(request.form['disc'] or 0)
    sale_price = int(price - (price * disc / 100))
    
    product_data = {
        "name": request.form['name'],
        "image": request.form['img'] or "https://via.placeholder.com/300",
        "category": request.form['cat'],
        "price": price,
        "discount": disc,
        "sale_price": sale_price,
        "code": request.form['code'],
        "weight": request.form['weight'],
        "description": request.form['desc'].replace('\n', '<br>'),
        "order_policy": request.form['policy'].replace('\n', '<br>'),
        "delivery_text": request.form['del_text']
    }
    products_col.insert_one(product_data)
    flash("পণ্যটি সফলভাবে শপে যুক্ত করা হয়েছে!")
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
