import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# --- অ্যাপ্লিকেশন কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "paharer_bazar_final_secret_mega_2024"

# --- মংগোডিবি কানেকশন (এখানে আপনার কানেকশন স্ট্রিং অবশ্যই দিবেন) ---
# উদাহরণ: MONGO_URI = "mongodb+srv://user:pass@cluster.mongodb.net/dbname"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['paharer_bazar_master']
products_col = db['products']
categories_col = db['categories']
users_col = db['users']
orders_col = db['orders']

# --- সম্পূর্ণ ডিজাইন ও ফ্রন্টএন্ড (HTML/CSS/JS) ---
MASTER_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paharer Bazar | বিশুদ্ধ পাহাড়ী পণ্য</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Hind Siliguri', sans-serif; background-color: #f4f6f8; color: #333; }
        
        /* লাল গোল প্রিমিয়াম অটো পোস্টার (ডিস্কাউন্ট ব্যাজ) */
        .red-premium-badge {
            background: radial-gradient(circle, #ff0000 0%, #a30000 100%);
            color: white; border-radius: 50%; width: 48px; height: 48px;
            display: flex; align-items: center; justify-content: center;
            font-size: 10px; font-weight: 800; position: absolute;
            top: 12px; right: 12px; z-index: 30; line-height: 1.1;
            text-align: center; border: 2px solid white; box-shadow: 0 4px 10px rgba(255,0,0,0.3);
            animation: pulse-red 2s infinite;
        }
        @keyframes pulse-red { 0% {transform: scale(1);} 50% {transform: scale(1.08);} 100% {transform: scale(1);} }

        /* মেনু ও সাইডবার ডিজাইন */
        .sidebar { transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1); z-index: 100; }
        .sidebar-hidden { transform: translateX(-100%); }
        .nav-active { color: #f97316; font-weight: bold; }

        /* বটম ন্যাভ */
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #ddd; 
                      z-index: 100; display: flex; justify-content: space-around; padding: 10px 0; box-shadow: 0 -4px 12px rgba(0,0,0,0.05); }
        .home-center { margin-top: -35px; background: #f97316; color: white; padding: 12px; border-radius: 50%; 
                       border: 4px solid white; box-shadow: 0 4px 15px rgba(249,115,22,0.4); }

        /* ট্যাব সিস্টেম */
        .tab-btn.active { border-bottom: 3px solid #f97316; color: #f97316; font-weight: bold; }
    </style>
</head>
<body class="pb-24">

    <!-- Top Announcement -->
    <div class="bg-[#f97316] text-white text-center py-1.5 text-[11px] font-bold tracking-tight">
        স্বাগতম || আমরা খাগড়াছড়ি হতে সারা বাংলাদেশে ক্যাশ অন ডেলিভারি এবং অনলাইন পেমেন্ট সুবিধা দেই
    </div>

    <!-- Main Header -->
    <header class="bg-white sticky top-0 z-50 shadow-sm px-4 py-3 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <button onclick="toggleSidebar()" class="text-2xl text-gray-700">☰</button>
            <a href="/" class="text-2xl font-black flex items-center">
                <span class="text-[#f97316]">Paharer</span><span class="text-gray-800 ml-1">Bazar</span>
            </a>
        </div>
        <div class="relative">
            <span class="text-2xl">🛒</span>
            <span class="absolute -top-1 -right-2 bg-orange-600 text-white text-[10px] rounded-full h-4 w-4 flex items-center justify-center font-bold">0</span>
        </div>
    </header>

    <!-- Search Section -->
    <div class="bg-white px-4 pb-3 shadow-sm border-t">
        <form action="/search" method="GET" class="relative max-w-2xl mx-auto mt-2">
            <input type="text" name="q" placeholder="Search Product..." class="w-full bg-[#f3f4f6] border-none rounded-lg py-2 px-5 text-sm outline-none focus:ring-1 focus:ring-orange-400">
            <button class="absolute right-3 top-2 text-gray-400">🔍</button>
        </form>
    </div>

    <!-- Side Sidebar Menu (এক বিন্দুও ভিন্ন নয়) -->
    <div id="sidebar" class="sidebar sidebar-hidden fixed top-0 left-0 h-full w-72 bg-white shadow-2xl overflow-y-auto">
        <div class="p-5 border-b flex justify-between items-center bg-gray-50">
            <div class="font-bold text-xl"><span class="text-[#f97316]">Paharer</span>Bazar</div>
            <button onclick="toggleSidebar()" class="text-3xl">&times;</button>
        </div>
        <ul class="p-4 space-y-1">
            {% for cat in categories %}
            <li><a href="/category/{{ cat.name }}" class="flex items-center gap-4 p-3 hover:bg-orange-50 rounded-lg border-b border-gray-50 text-gray-700 font-semibold">
                <span>{{ cat.icon }}</span> {{ cat.name }}
            </a></li>
            {% endfor %}
            
            <div class="mt-8 border-t pt-5 space-y-2">
                <li><a href="/admin" class="block p-3 text-red-600 font-bold bg-red-50 rounded-lg">⚙️ Admin Control Panel</a></li>
                {% if session.get('user') %}
                    <li class="p-3 font-bold text-orange-600">👤 স্বাগতম, {{ session['user'] }}</li>
                    <li><a href="/logout" class="block p-3 text-gray-500">Log Out</a></li>
                {% else %}
                    <li><a href="/login" class="block p-3 text-blue-600 font-bold">Login / Register</a></li>
                {% endif %}
            </div>
        </ul>
    </div>

    <!-- Content Area -->
    <div class="container mx-auto p-4 max-w-6xl">
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                <div class="bg-emerald-500 text-white p-3 mb-4 rounded-lg shadow-md text-center font-bold text-sm">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% if page == 'home' %}
            <!-- Banner Slider Area -->
            <div class="mb-8 rounded-2xl overflow-hidden shadow-sm border-2 border-white">
                <img src="https://i.ibb.co/L5Bf85m/banner.jpg" class="w-full object-cover h-44 md:h-80">
            </div>

            <!-- Product Grid -->
            <h2 class="text-center font-bold text-xl mb-6 text-gray-700 tracking-widest uppercase border-b-2 border-orange-100 max-w-xs mx-auto pb-1">All Products</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                {% for p in products %}
                <div class="bg-white rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden flex flex-col group">
                    {% if p.discount > 0 %}
                    <div class="red-premium-badge">{{ p.discount }}%<br>ছাড়</div>
                    {% endif %}
                    <a href="/product/{{ p._id }}"><img src="{{ p.image }}" class="w-full h-44 object-cover group-hover:scale-110 transition duration-500"></a>
                    <div class="p-3 flex-grow text-center">
                        <a href="/product/{{ p._id }}"><h3 class="text-[14px] font-bold h-10 overflow-hidden text-gray-800 leading-tight mb-2">{{ p.name }}</h3></a>
                        <div class="flex justify-center items-center gap-2">
                            <span class="text-gray-400 line-through text-[11px]">৳{{ p.price }}</span>
                            <span class="text-[#f97316] font-black text-lg">৳{{ p.sale_price }}</span>
                        </div>
                    </div>
                    <a href="/product/{{ p._id }}" class="bg-[#f97316] text-white text-center py-3 text-xs font-black uppercase tracking-widest">অর্ডার করুন</a>
                </div>
                {% endfor %}
            </div>

        {% elif page == 'product_detail' %}
            <!-- Product Detail Page (এক বিন্দুও বাদ নেই) -->
            <div class="bg-white rounded-3xl shadow-sm p-5 md:p-10">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div class="relative bg-gray-50 rounded-3xl p-4">
                        {% if p.discount > 0 %} <div class="red-premium-badge w-14 h-14 text-sm">{{ p.discount }}%<br>ছাড়</div> {% endif %}
                        <img src="{{ p.image }}" class="w-full max-h-96 object-contain mx-auto">
                    </div>
                    <div class="flex flex-col">
                        <nav class="text-[11px] text-gray-400 font-bold uppercase mb-2">Home / {{ p.category }}</nav>
                        <h1 class="text-2xl font-black text-gray-900 leading-tight mb-3">{{ p.name }}</h1>
                        <div class="flex items-baseline gap-3 mb-4">
                            <div class="text-3xl font-black text-[#f97316]">৳{{ p.sale_price }}</div>
                            <div class="text-gray-400 line-through font-bold">৳{{ p.price }}</div>
                        </div>
                        
                        <div class="bg-emerald-700 text-white text-[10px] inline-block px-3 py-1 rounded-sm font-bold uppercase w-fit mb-5 tracking-widest">প্রোডাক্ট কোড : {{ p.code }}</div>

                        <div class="mb-6">
                            <label class="text-[11px] font-black text-gray-400 block mb-2 uppercase">Size / Weight:</label>
                            <div class="border-2 border-orange-500 px-4 py-2 rounded-xl bg-orange-50 text-orange-600 font-bold inline-block">📦 {{ p.weight }} - ৳{{ p.sale_price }}</div>
                        </div>

                        <div class="flex gap-4 mb-4">
                            <div class="flex border-2 border-gray-100 rounded-xl bg-gray-50 px-2 items-center">
                                <button class="px-3 py-2 text-xl font-bold">-</button>
                                <input type="text" value="1" class="w-10 text-center bg-transparent font-black" readonly>
                                <button class="px-3 py-2 text-xl font-bold">+</button>
                            </div>
                            <button class="flex-1 bg-emerald-600 text-white py-4 rounded-xl font-black uppercase text-sm">কার্টে যোগ করুন</button>
                        </div>

                        <a href="/checkout/{{ p._id }}" class="block w-full bg-[#f97316] text-white text-center py-4 rounded-xl font-black text-xl shadow-lg hover:bg-orange-600 transition">অর্ডার করুন</a>
                        
                        <div class="grid grid-cols-2 gap-3 mt-4">
                            <a href="tel:01511820222" class="bg-gray-900 text-white py-3 rounded-xl text-center text-xs font-bold flex items-center justify-center gap-2">📞 কল করুন</a>
                            <a href="https://wa.me/8801511820222" class="bg-emerald-500 text-white py-3 rounded-xl text-center text-xs font-bold flex items-center justify-center gap-2">💬 Whatsapp</a>
                        </div>

                        <!-- Delivery Charge Table -->
                        <div class="mt-8 border-2 border-orange-100 rounded-2xl p-5 bg-orange-50/20">
                            <h4 class="font-bold text-sm mb-3">কুরিয়ার ডেলিভারি খরচ:</h4>
                            <table class="w-full text-xs text-left bg-white border border-gray-200">
                                <tr class="bg-gray-100 border-b"><th class="p-2">বিবরণ</th><th class="p-2 text-right">চার্জ</th></tr>
                                <tr class="border-b"><td class="p-2">সর্বমোট ১ কেজি পর্যন্ত</td><td class="p-2 text-right font-bold">৳ ১৩০</td></tr>
                                <tr><td class="p-2">সর্বমোট ২ কেজি পর্যন্ত</td><td class="p-2 text-right font-bold">৳ ১৫০</td></tr>
                            </table>
                            <p class="mt-3 text-[11px] text-orange-600 font-bold italic tracking-tighter">⚠️ {{ p.delivery_text }}</p>
                        </div>
                    </div>
                </div>

                <!-- Detail Tabs -->
                <div class="mt-12">
                    <div class="flex border-b text-sm font-bold">
                        <button onclick="tab('desc')" id="btn-desc" class="tab-btn active px-6 py-4">Description</button>
                        <button onclick="tab('pol')" id="btn-pol" class="tab-btn px-6 py-4">Order Policy</button>
                        <button onclick="tab('rev')" id="btn-rev" class="tab-btn px-6 py-4">Reviews (0)</button>
                    </div>
                    <div id="c-desc" class="py-8 text-gray-700 text-sm leading-relaxed">
                        <h4 class="font-bold mb-4 border-b pb-1">পণ্যের বিস্তারিত:</h4>
                        {{ p.description | safe }}
                    </div>
                    <div id="c-pol" class="hidden py-8 text-gray-700 text-sm leading-relaxed">
                        <h4 class="font-bold mb-4 border-b pb-1">অর্ডার করার নিয়মাবলী:</h4>
                        {{ p.order_policy | safe }}
                    </div>
                    <div id="c-rev" class="hidden py-16 text-center text-gray-400 italic">এখনো কোনো কাস্টমার রিভিউ দেননি।</div>
                </div>
            </div>

        {% elif page == 'checkout' %}
            <!-- Checkout (বিকাশ, নগদ, রকেট, ক্যাশ অন ডেলিভারি সব সহ) -->
            <div class="max-w-xl mx-auto bg-white p-8 rounded-3xl shadow-xl border border-gray-100">
                <h2 class="text-2xl font-black mb-6 text-gray-800 border-b pb-4">অর্ডার কনফার্ম করুন</h2>
                <div class="flex gap-4 mb-8 bg-gray-50 p-3 rounded-xl border border-gray-100">
                    <img src="{{ p.image }}" class="w-16 h-16 rounded-lg object-cover">
                    <div>
                        <p class="text-sm font-bold">{{ p.name }}</p>
                        <p class="text-[#f97316] font-bold">৳ {{ p.sale_price }}</p>
                    </div>
                </div>
                <form action="/place-order" method="POST" class="space-y-4">
                    <input type="hidden" name="p_id" value="{{ p._id }}">
                    <div>
                        <label class="text-xs font-bold text-gray-500 block mb-1">আপনার নাম *</label>
                        <input type="text" name="name" class="w-full border-2 p-4 rounded-2xl outline-none focus:border-orange-500" placeholder="সম্পূর্ণ নাম লিখুন" required>
                    </div>
                    <div>
                        <label class="text-xs font-bold text-gray-500 block mb-1">মোবাইল নাম্বার *</label>
                        <input type="text" name="phone" class="w-full border-2 p-4 rounded-2xl outline-none focus:border-orange-500" placeholder="017xxxxxxxx" required>
                    </div>
                    <div>
                        <label class="text-xs font-bold text-gray-500 block mb-1">ঠিকানা (লোকেশন) *</label>
                        <textarea name="address" class="w-full border-2 p-4 rounded-2xl h-24 outline-none focus:border-orange-500" placeholder="গ্রাম/এলাকা, থানা, জেলা লিখুন" required></textarea>
                    </div>
                    <div>
                        <label class="text-xs font-bold text-gray-500 block mb-1">পেমেন্ট মেথড সিলেক্ট করুন</label>
                        <select name="payment" class="w-full border-2 p-4 rounded-2xl bg-white font-bold outline-none">
                            <option value="Cash on Delivery">ক্যাশ অন ডেলিভারি (COD)</option>
                            <option value="Bkash">বিকাশ (Bkash)</option>
                            <option value="Nagad">নগদ (Nagad)</option>
                            <option value="Rocket">রকেট / উপায় (Rocket)</option>
                        </select>
                    </div>
                    <button class="w-full bg-[#f97316] text-white py-4 rounded-2xl font-black text-xl shadow-2xl mt-4">অর্ডার কনফার্ম করুন</button>
                </form>
            </div>

        {% elif page == 'admin' %}
            <!-- Full Control Admin Panel (এক বিন্দুও বাদ নেই) -->
            <div class="max-w-4xl mx-auto space-y-10">
                <!-- Add Category -->
                <div class="bg-white p-8 rounded-3xl shadow-sm border border-orange-100">
                    <h2 class="font-black text-xl mb-6 text-emerald-600">📂 ক্যাটাগরি তৈরি করুন</h2>
                    <form action="/admin/add-cat" method="POST" class="flex flex-wrap gap-4">
                        <input type="text" name="icon" placeholder="ইমোজি (🥭)" class="w-20 border-2 p-3 rounded-xl text-center outline-none">
                        <input type="text" name="name" placeholder="ক্যাটাগরি নাম" class="flex-1 min-w-[200px] border-2 p-3 rounded-xl outline-none">
                        <button class="bg-emerald-600 text-white px-8 rounded-xl font-bold">Add</button>
                    </form>
                </div>

                <!-- Add Product -->
                <div class="bg-white p-8 rounded-3xl shadow-sm border border-orange-100">
                    <h2 class="font-black text-xl mb-6 text-orange-600">🍎 নতুন প্রোডাক্ট অ্যাড করুন</h2>
                    <form action="/admin/add-product" method="POST" class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <input type="text" name="name" placeholder="ফলের নাম" class="border-2 p-4 rounded-xl w-full outline-none focus:border-orange-500" required>
                            <select name="cat" class="border-2 p-4 rounded-xl w-full bg-white outline-none">
                                {% for c in categories %} <option>{{ c.name }}</option> {% endfor %}
                            </select>
                        </div>
                        <input type="text" name="img" placeholder="ইমেজ সরাসরি লিঙ্ক (URL)" class="border-2 p-4 rounded-xl w-full outline-none">
                        <div class="grid grid-cols-3 gap-4">
                            <input type="number" name="price" placeholder="আসল দাম" class="border-2 p-4 rounded-xl outline-none">
                            <input type="number" name="disc" placeholder="ডিস্কাউন্ট %" class="border-2 p-4 rounded-xl outline-none">
                            <input type="text" name="weight" placeholder="ওজন (৫০০ গ্রাম)" class="border-2 p-4 rounded-xl outline-none">
                        </div>
                        <input type="text" name="code" placeholder="কোড (যেমন: P-101)" class="border-2 p-4 rounded-xl w-full outline-none">
                        <textarea name="desc" placeholder="ফলের বিস্তারিত তথ্য (HTML সাপোর্ট করে)" class="w-full border-2 p-4 rounded-xl h-32 outline-none"></textarea>
                        <textarea name="pol" placeholder="অর্ডার করার নিয়মাবলী" class="w-full border-2 p-4 rounded-xl h-24 outline-none"></textarea>
                        <input type="text" name="del_text" placeholder="ডেলিভারি সার্চ টেক্স" class="w-full border-2 p-4 rounded-xl outline-none">
                        <button class="w-full bg-[#f97316] text-white py-5 rounded-2xl font-black text-lg">পণ্যটি পাবলিশ করুন</button>
                    </form>
                </div>

                <!-- Orders Table -->
                <div class="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <h2 class="font-black text-xl mb-4 text-blue-600">📋 অর্ডার লিস্ট</h2>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr class="bg-gray-50 border-b"><th class="p-3">ক্রেতা</th><th class="p-3">পণ্য</th><th class="p-3">পেমেন্ট</th><th class="p-3">ঠিকানা</th></tr>
                            </thead>
                            <tbody>
                                {% for o in orders %}
                                <tr class="border-b hover:bg-gray-50">
                                    <td class="p-3 font-bold">{{ o.name }}<br><span class="text-orange-500">{{ o.phone }}</span></td>
                                    <td class="p-3 text-gray-600">ID: {{ o.p_id }}</td>
                                    <td class="p-3"><span class="bg-emerald-100 text-emerald-800 px-2 py-1 rounded">{{ o.payment }}</span></td>
                                    <td class="p-3 text-gray-500">{{ o.address }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        {% elif page == 'login' %}
            <div class="max-w-md mx-auto bg-white p-10 rounded-3xl shadow-xl text-center border">
                <h2 class="text-2xl font-black mb-8">লগইন করুন</h2>
                <form action="/auth/login" method="POST" class="space-y-4">
                    <input type="text" name="user" placeholder="Username" class="w-full border-2 p-4 rounded-2xl outline-none" required>
                    <input type="password" name="pass" placeholder="Password" class="w-full border-2 p-4 rounded-2xl outline-none" required>
                    <button class="w-full bg-[#f97316] text-white py-4 rounded-2xl font-black">Login</button>
                </form>
                <div class="mt-6 text-sm text-gray-500">অ্যাকাউন্ট নেই? <a href="/register" class="text-orange-600 font-bold">রেজিস্ট্রেশন</a></div>
            </div>

        {% elif page == 'register' %}
            <div class="max-w-md mx-auto bg-white p-10 rounded-3xl shadow-xl text-center border">
                <h2 class="text-2xl font-black mb-8">নতুন অ্যাকাউন্ট</h2>
                <form action="/auth/register" method="POST" class="space-y-4">
                    <input type="text" name="user" placeholder="Username" class="w-full border-2 p-4 rounded-2xl outline-none" required>
                    <input type="password" name="pass" placeholder="Password" class="w-full border-2 p-4 rounded-2xl outline-none" required>
                    <button class="w-full bg-blue-600 text-white py-4 rounded-2xl font-black">Register</button>
                </form>
            </div>
        {% endif %}
    </div>

    <!-- Professional Footer -->
    <footer class="bg-white border-t border-gray-100 p-10 mt-20 text-center">
        <div class="text-3xl font-black flex justify-center items-center mb-3">
            <span class="text-[#f97316]">Paharer</span><span class="text-gray-800 ml-1">Bazar</span>
        </div>
        <p class="text-[11px] text-gray-400 font-bold uppercase tracking-[4px]">Address: Muslimpara, Khagrachhari Sadar. | Hotline: +8801511820222</p>
        
        <div class="grid grid-cols-2 gap-10 text-left max-w-sm mx-auto text-[11px] font-bold text-gray-600 border-t pt-8 mt-8">
            <ul class="space-y-2"><li class="text-gray-800 font-black">Useful Link</li><li>Contact Us</li><li>Delivery Rules</li><li>Return Policy</li></ul>
            <ul class="space-y-2"><li class="text-gray-800 font-black">Company</li><li>All Products</li><li>Terms & Conditions</li><li>Privacy Policy</li></ul>
        </div>
        
        <div class="bg-[#f97316] text-white p-5 text-[10px] font-black tracking-[2px] mt-10 -mx-10 -mb-10 uppercase">
            Copyright © 2026 Paharer Bazar. All rights reserved.
        </div>
    </footer>

    <!-- Fixed Bottom Navigation (হুবহু স্ক্রিনশটের ডিজাইন) -->
    <nav class="bottom-nav">
        <button onclick="toggleSidebar()" class="nav-item flex flex-col items-center text-[10px] text-gray-500 font-bold">
            <span class="text-2xl">☰</span><span>Category</span>
        </button>
        <a href="https://wa.me/8801511820222" class="nav-item flex flex-col items-center text-[10px] text-gray-500 font-bold">
            <span class="text-2xl text-emerald-500">💬</span><span>Whatsapp</span>
        </a>
        <a href="/" class="flex flex-col items-center -mt-8">
            <div class="home-center text-xl">🏠</div>
            <span class="mt-4 font-black text-[#f97316] text-[10px] uppercase">Home</span>
        </a>
        <div class="nav-item flex flex-col items-center text-[10px] text-gray-500 font-bold">
            <span class="text-2xl">🛒</span><span>Cart (0)</span>
        </div>
        <a href="/login" class="nav-item flex flex-col items-center text-[10px] text-gray-500 font-bold">
            <span class="text-2xl">👤</span><span>Login</span>
        </a>
    </nav>

    <script>
        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('sidebar-hidden'); }
        function tab(name) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('[id^="c-"]').forEach(c => c.classList.add('hidden'));
            document.getElementById('btn-'+name).classList.add('active');
            document.getElementById('c-'+name).classList.remove('hidden');
        }
    </script>
</body>
</html>
"""

# --- রুটিং এবং লজিক ---

@app.route('/')
def index():
    return render_template_string(MASTER_HTML, page='home', products=list(products_col.find()), categories=list(categories_col.find()))

@app.route('/category/<name>')
def category_view(name):
    return render_template_string(MASTER_HTML, page='home', products=list(products_col.find({"category": name})), categories=list(categories_col.find()))

@app.route('/product/<id>')
def product_detail(id):
    return render_template_string(MASTER_HTML, page='product_detail', p=products_col.find_one({"_id": ObjectId(id)}), categories=list(categories_col.find()))

@app.route('/checkout/<id>')
def checkout(id):
    return render_template_string(MASTER_HTML, page='checkout', p=products_col.find_one({"_id": ObjectId(id)}), categories=list(categories_col.find()))

@app.route('/place-order', methods=['POST'])
def place_order():
    orders_col.insert_one({"p_id": request.form['p_id'], "name": request.form['name'], "phone": request.form['phone'], "address": request.form['address'], "payment": request.form['payment'], "date": datetime.now()})
    flash("অর্ডার সফল হয়েছে! আপনার সাথে শীঘ্রই যোগাযোগ করা হবে।")
    return redirect('/')

@app.route('/admin')
def admin_panel():
    return render_template_string(MASTER_HTML, page='admin', categories=list(categories_col.find()), orders=list(orders_col.find().sort("date", -1)))

@app.route('/admin/add-cat', methods=['POST'])
def add_cat():
    categories_col.insert_one({"name": request.form['name'], "icon": request.form['icon'] or '🥭'})
    return redirect('/admin')

@app.route('/admin/add-product', methods=['POST'])
def add_product():
    price = float(request.form['price'])
    disc = float(request.form['disc'] or 0)
    products_col.insert_one({"name": request.form['name'], "image": request.form['img'], "category": request.form['cat'], "price": price, "discount": disc, "sale_price": int(price - (price * disc / 100)), "code": request.form['code'], "weight": request.form['weight'], "description": request.form['desc'].replace('\\n', '<br>'), "order_policy": request.form['pol'].replace('\\n', '<br>'), "delivery_text": request.form['del_text']})
    flash("পণ্য সফলভাবে যুক্ত হয়েছে!")
    return redirect('/admin')

@app.route('/auth/register', methods=['POST'])
def auth_reg():
    users_col.insert_one({"user": request.form['user'], "pass": request.form['pass'], "role": "user"})
    flash("রেজিস্ট্রেশন সফল! লগইন করুন।")
    return redirect('/login')

@app.route('/auth/login', methods=['POST'])
def auth_login():
    u = users_col.find_one({"user": request.form['user'], "pass": request.form['pass']})
    if u: session['user'] = u['user']; session['role'] = u.get('role', 'user'); return redirect('/')
    flash("ভুল ইউজারনেম বা পাসওয়ার্ড!")
    return redirect('/login')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/search')
def search():
    q = request.args.get('q', '')
    prods = list(products_col.find({"name": {"$regex": q, "$options": "i"}}))
    return render_template_string(MASTER_HTML, page='home', products=prods, categories=list(categories_col.find()))

@app.route('/login')
def login_page(): return render_template_string(MASTER_HTML, page='login', categories=list(categories_col.find()))

@app.route('/register')
def reg_page(): return render_template_string(MASTER_HTML, page='register', categories=list(categories_col.find()))

if __name__ == "__main__":
    app.run(debug=True)
