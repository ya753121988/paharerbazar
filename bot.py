import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "paharer_bazar_absolute_ultimate_mega_final_2024"

# --- মংগোডিবি কানেকশন (আপনার দেওয়া অরিজিনাল লিঙ্ক) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database('paharer_bazar_final_system') # নির্দিষ্ট ডাটাবেস নাম

# কালেকশন সমূহ
products_col = db['products']
categories_col = db['categories']
orders_col = db['orders']
settings_col = db['settings']
users_col = db['users']

# প্রাথমিক সেটিংস লোডার (এক বিন্দু মিসিং ছাড়াই)
def get_site_settings():
    s = settings_col.find_one({"type": "general"})
    if not s:
        default_settings = {
            "type": "general",
            "site_name": "Paharer Bazar",
            "notice": "স্বাগতম || সারা বাংলাদেশে ক্যাশ অন ডেলিভারি এবং অনলাইন পেমেন্ট সুবিধা!",
            "whatsapp": "01511820222",
            "bkash": "01511820222",
            "nagad": "01511820222",
            "rocket": "01511820222",
            "upay": "01511820222"
        }
        settings_col.insert_one(default_settings)
        return default_settings
    return s

# --- মাস্টার টেমপ্লেট: ইউজার ও এডমিন প্যানেল একসাথে কিন্তু আলাদা লজিক ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ settings.site_name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Hind Siliguri', sans-serif; background-color: #f4f7f6; color: #333; }
        
        /* লাল গোল প্রিমিয়াম ডিস্কাউন্ট স্টিকার */
        .discount-badge {
            background: radial-gradient(circle, #ff0000 0%, #a30000 100%);
            color: white; border-radius: 50%; width: 48px; height: 48px;
            display: flex; align-items: center; justify-content: center;
            font-size: 10px; font-weight: 800; position: absolute;
            top: 12px; right: 12px; z-index: 30; line-height: 1.1;
            text-align: center; border: 2px solid white; box-shadow: 0 4px 10px rgba(255,0,0,0.3);
            animation: pulse-red 2s infinite;
        }
        @keyframes pulse-red { 0% {transform: scale(1);} 50% {transform: scale(1.08);} 100% {transform: scale(1);} }

        /* সাইডবার ও ন্যাভ */
        .sidebar { transition: transform 0.4s ease; z-index: 100; }
        .sidebar-hidden { transform: translateX(-100%); }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #ddd; 
                      z-index: 100; display: flex; justify-content: space-around; padding: 10px 0; box-shadow: 0 -4px 12px rgba(0,0,0,0.05); }
        .home-circle { margin-top: -35px; background: #f97316; color: white; padding: 12px; border-radius: 50%; 
                       border: 4px solid white; box-shadow: 0 4px 15px rgba(249,115,22,0.4); }

        /* এডমিন সাইডবার */
        .admin-sidebar { background: #0f172a; color: white; min-height: 100vh; }
        .admin-link:hover { background: #1e293b; color: #fb923c; }
        .tab-btn.active { border-bottom: 3px solid #f97316; color: #f97316; font-weight: bold; }
    </style>
</head>
<body class="{% if not is_admin %}pb-24{% endif %}">

    {% if is_admin %}
    <!-- ================= ADIMIN PANEL UI (সম্পূর্ণ আলাদা) ================= -->
    <div class="flex flex-col md:flex-row min-h-screen">
        <!-- Sidebar -->
        <div class="w-full md:w-64 admin-sidebar p-6 flex flex-col">
            <h2 class="text-2xl font-black text-orange-500 mb-8 border-b border-gray-700 pb-4">Admin Panel</h2>
            <nav class="flex-grow space-y-2">
                <a href="/admin" class="admin-link block p-3 rounded-xl transition">📊 ড্যাশবোর্ড</a>
                <a href="/admin/settings" class="admin-link block p-3 rounded-xl transition">⚙️ সাইট সেটিংস</a>
                <a href="/admin/products" class="admin-link block p-3 rounded-xl transition">🍎 প্রোডাক্ট ম্যানেজ</a>
                <a href="/admin/categories" class="admin-link block p-3 rounded-xl transition">📂 ক্যাটাগরি ম্যানেজ</a>
                <a href="/admin/orders" class="admin-link block p-3 rounded-xl transition">📦 অর্ডার লিস্ট</a>
            </nav>
            <div class="mt-10 pt-5 border-t border-gray-700 space-y-2 text-sm">
                <a href="/" class="block p-3 text-gray-400 hover:text-white">🔙 মূল ওয়েবসাইট দেখুন</a>
                <a href="/logout" class="block p-3 text-red-400 hover:text-red-500">🚪 লগ আউট করুন</a>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="flex-1 p-5 md:p-10 bg-gray-50">
            {% with messages = get_flashed_messages() %}
                {% if messages %}{% for m in messages %}<div class="bg-emerald-500 text-white p-4 rounded-2xl mb-6 shadow-lg font-bold">{{ m }}</div>{% endfor %}{% endif %}
            {% endwith %}

            {% if admin_page == 'dashboard' %}
                <h1 class="text-3xl font-black mb-8 text-gray-800">Dashboard Overview</h1>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-white p-8 rounded-[30px] shadow-sm border-l-8 border-blue-500">
                        <p class="text-gray-400 font-bold uppercase text-[10px] tracking-widest">Total Products</p>
                        <h3 class="text-4xl font-black mt-2">{{ p_count }}</h3>
                    </div>
                    <div class="bg-white p-8 rounded-[30px] shadow-sm border-l-8 border-orange-500">
                        <p class="text-gray-400 font-bold uppercase text-[10px] tracking-widest">Categories</p>
                        <h3 class="text-4xl font-black mt-2">{{ c_count }}</h3>
                    </div>
                    <div class="bg-white p-8 rounded-[30px] shadow-sm border-l-8 border-emerald-500">
                        <p class="text-gray-400 font-bold uppercase text-[10px] tracking-widest">Orders</p>
                        <h3 class="text-4xl font-black mt-2">{{ o_count }}</h3>
                    </div>
                </div>

            {% elif admin_page == 'settings' %}
                <h1 class="text-3xl font-black mb-8">⚙️ সাইট সেটিংস</h1>
                <form action="/admin/settings/update" method="POST" class="bg-white p-10 rounded-[35px] shadow-sm border space-y-6 max-w-4xl">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div><label class="block text-xs font-black text-gray-400 uppercase mb-2">সাইটের নাম</label><input type="text" name="site_name" value="{{ settings.site_name }}" class="w-full border-2 p-4 rounded-2xl outline-none focus:border-orange-500"></div>
                        <div><label class="block text-xs font-black text-gray-400 uppercase mb-2">হোয়াটসঅ্যাপ নাম্বার</label><input type="text" name="whatsapp" value="{{ settings.whatsapp }}" class="w-full border-2 p-4 rounded-2xl outline-none focus:border-orange-500"></div>
                    </div>
                    <div><label class="block text-xs font-black text-gray-400 uppercase mb-2">নোটিশ বার টেক্সট</label><textarea name="notice" class="w-full border-2 p-4 rounded-2xl outline-none focus:border-orange-500 h-24">{{ settings.notice }}</textarea></div>
                    <hr class="border-gray-100">
                    <h3 class="font-black text-orange-600 uppercase text-sm">পেমেন্ট মেথড নাম্বারসমূহ</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div><label class="text-[10px] font-bold text-gray-400">বিকাশ</label><input type="text" name="bkash" value="{{ settings.bkash }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                        <div><label class="text-[10px] font-bold text-gray-400">নগদ</label><input type="text" name="nagad" value="{{ settings.nagad }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                        <div><label class="text-[10px] font-bold text-gray-400">রকেট/উপায়</label><input type="text" name="rocket" value="{{ settings.rocket }}" class="w-full border-2 p-3 rounded-xl outline-none"></div>
                    </div>
                    <button class="w-full bg-orange-600 text-white py-5 rounded-[25px] font-black text-xl shadow-2xl shadow-orange-100 mt-5">Save All Settings</button>
                </form>

            {% elif admin_page == 'products' %}
                <div class="flex justify-between items-center mb-10">
                    <h1 class="text-3xl font-black">🍎 প্রোডাক্ট ম্যানেজমেন্ট</h1>
                    <button onclick="document.getElementById('addModal').classList.toggle('hidden')" class="bg-emerald-600 text-white px-8 py-4 rounded-2xl font-black shadow-xl">+ Add Product</button>
                </div>

                <!-- Add Form -->
                <div id="addModal" class="hidden bg-white p-8 rounded-[35px] shadow-2xl border mb-10">
                    <h2 class="text-xl font-black mb-6 border-b pb-4">নতুন প্রোডাক্ট যোগ করুন</h2>
                    <form action="/admin/product/add" method="POST" class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <input type="text" name="name" placeholder="নাম" class="border-2 p-4 rounded-2xl w-full" required>
                            <select name="cat" class="border-2 p-4 rounded-2xl w-full bg-white font-bold">
                                {% for c in cats %} <option>{{ c.name }}</option> {% endfor %}
                            </select>
                        </div>
                        <input type="text" name="img" placeholder="ইমেজ লিঙ্ক (URL)" class="border-2 p-4 rounded-2xl w-full">
                        <div class="grid grid-cols-3 gap-4">
                            <input type="number" name="price" placeholder="আসল দাম" class="border-2 p-4 rounded-2xl">
                            <input type="number" name="disc" placeholder="ডিস্কাউন্ট %" class="border-2 p-4 rounded-2xl">
                            <input type="text" name="weight" placeholder="ওজন" class="border-2 p-4 rounded-2xl">
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <input type="text" name="code" placeholder="কোড (P-101)" class="border-2 p-4 rounded-2xl">
                            <input type="text" name="del_text" placeholder="ডেলিভারি টেক্সট" class="border-2 p-4 rounded-2xl">
                        </div>
                        <textarea name="desc" placeholder="বিস্তারিত তথ্য" class="w-full border-2 p-4 rounded-2xl h-24"></textarea>
                        <textarea name="policy" placeholder="অর্ডার নিয়ম" class="w-full border-2 p-4 rounded-2xl h-20"></textarea>
                        <button class="w-full bg-orange-600 text-white py-5 rounded-[25px] font-black text-xl">পাবলিশ করুন</button>
                    </form>
                </div>

                <!-- Product List -->
                <div class="bg-white rounded-[35px] shadow-sm border overflow-hidden">
                    <table class="w-full text-left">
                        <thead class="bg-gray-50 border-b">
                            <tr><th class="p-5">Image</th><th class="p-5">Name & Info</th><th class="p-5">Price</th><th class="p-5 text-center">Actions</th></tr>
                        </thead>
                        <tbody>
                            {% for p in prods %}
                            <tr class="border-b hover:bg-gray-50 transition">
                                <td class="p-5"><img src="{{ p.image }}" class="w-16 h-16 object-cover rounded-2xl"></td>
                                <td class="p-5 font-bold">{{ p.name }}<br><span class="text-[10px] text-gray-400 font-normal uppercase">{{ p.category }} | {{ p.code }}</span></td>
                                <td class="p-5 font-black text-orange-600">৳ {{ p.sale_price }}</td>
                                <td class="p-5 text-center space-x-2">
                                    <a href="/admin/product/edit/{{ p._id }}" class="bg-blue-100 text-blue-600 px-4 py-2 rounded-xl text-xs font-bold">ইডিট (Edit)</a>
                                    <a href="/admin/product/delete/{{ p._id }}" onclick="return confirm('ডিলিট করতে চান?')" class="bg-red-100 text-red-600 px-4 py-2 rounded-xl text-xs font-bold">ডিলিট (Delete)</a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

            {% elif admin_page == 'edit_product' %}
                <h1 class="text-3xl font-black mb-8">🛠️ ইডিট প্রোডাক্ট: {{ p.name }}</h1>
                <form action="/admin/product/update/{{ p._id }}" method="POST" class="bg-white p-10 rounded-[35px] shadow-sm border space-y-5 max-w-4xl">
                    <div class="grid grid-cols-2 gap-5">
                        <input type="text" name="name" value="{{ p.name }}" class="border-2 p-4 rounded-2xl w-full font-bold">
                        <select name="cat" class="border-2 p-4 rounded-2xl w-full bg-white font-bold">{% for c in cats %}<option {% if c.name == p.category %}selected{% endif %}>{{ c.name }}</option>{% endfor %}</select>
                    </div>
                    <input type="text" name="img" value="{{ p.image }}" class="border-2 p-4 rounded-2xl w-full">
                    <div class="grid grid-cols-3 gap-5">
                        <input type="number" name="price" value="{{ p.price }}" class="border-2 p-4 rounded-2xl font-bold">
                        <input type="number" name="disc" value="{{ p.discount }}" class="border-2 p-4 rounded-2xl font-bold">
                        <input type="text" name="weight" value="{{ p.weight }}" class="border-2 p-4 rounded-2xl font-bold">
                    </div>
                    <div class="grid grid-cols-2 gap-5">
                        <input type="text" name="code" value="{{ p.code }}" class="border-2 p-4 rounded-2xl">
                        <input type="text" name="del_text" value="{{ p.delivery_text }}" class="border-2 p-4 rounded-2xl">
                    </div>
                    <textarea name="desc" class="w-full border-2 p-4 rounded-2xl h-32">{{ p.description }}</textarea>
                    <textarea name="policy" class="w-full border-2 p-4 rounded-2xl h-24">{{ p.order_policy }}</textarea>
                    <button class="w-full bg-emerald-600 text-white py-5 rounded-[25px] font-black text-xl shadow-xl">Update Now</button>
                </form>

            {% elif admin_page == 'categories' %}
                <h1 class="text-3xl font-black mb-8">📂 ক্যাটাগরি ম্যানেজ</h1>
                <form action="/admin/category/add" method="POST" class="bg-white p-8 rounded-[30px] shadow-sm border flex gap-4 mb-10 max-w-xl">
                    <input type="text" name="icon" placeholder="Emoji (🥭)" class="w-20 border-2 p-4 rounded-2xl text-center text-xl">
                    <input type="text" name="name" placeholder="ক্যাটাগরি নাম" class="flex-1 border-2 p-4 rounded-2xl font-bold">
                    <button class="bg-black text-white px-8 rounded-2xl font-black">Add</button>
                </form>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    {% for c in cats %}
                    <div class="bg-white p-6 rounded-[25px] shadow-sm border flex justify-between items-center group">
                        <span class="text-xl font-bold">{{ c.icon }} {{ c.name }}</span>
                        <a href="/admin/category/delete/{{ c._id }}" onclick="return confirm('ডিলিট?')" class="text-red-100 group-hover:text-red-500 transition">🗑️</a>
                    </div>
                    {% endfor %}
                </div>

            {% elif admin_page == 'orders' %}
                <h1 class="text-3xl font-black mb-8">📦 অর্ডার তালিকা</h1>
                <div class="bg-white rounded-[35px] shadow-sm border overflow-hidden">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-100 border-b">
                            <tr><th class="p-5">ক্রেতা</th><th class="p-5">পণ্য</th><th class="p-5">পেমেন্ট</th><th class="p-5">ঠিকানা</th></tr>
                        </thead>
                        <tbody>
                            {% for o in orders %}
                            <tr class="border-b hover:bg-gray-50">
                                <td class="p-5 font-bold">{{ o.name }}<br><span class="text-orange-600">{{ o.phone }}</span></td>
                                <td class="p-5 text-gray-500">{{ o.p_id }}</td>
                                <td class="p-5"><span class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-black text-[10px]">{{ o.payment }}</span></td>
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
    <!-- ================= USER WEBSITE UI (বিন্দু পরিমাণ মিসিং ছাড়া) ================= -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
        <div class="bg-orange-600 text-white text-center py-2 text-[11px] font-black uppercase tracking-widest">{{ settings.notice }}</div>
        <div class="p-4 flex justify-between items-center container mx-auto">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="text-2xl">☰</button>
                <a href="/" class="text-2xl font-black text-orange-600">{{ settings.site_name }}</a>
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
            <li><a href="/category/{{ c.name }}" class="flex items-center gap-4 p-4 hover:bg-orange-50 rounded-2xl border-b border-gray-50 text-gray-700 font-bold">
                <span class="text-2xl">{{ c.icon }}</span> {{ c.name }}
            </a></li>
            {% endfor %}
            <div class="mt-10 pt-5 border-t space-y-2">
                <li><a href="/admin" class="block p-4 text-red-600 font-black bg-red-50 rounded-2xl">⚙️ Admin Control</a></li>
                {% if session.get('user') %}
                    <li class="p-4 text-orange-600 font-bold">👤 স্বাগতম, {{ session['user'] }}</li>
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
            <div class="mb-10 rounded-[40px] overflow-hidden shadow-xl border-4 border-white">
                <img src="https://i.ibb.co/L5Bf85m/banner.jpg" class="w-full object-cover h-48 md:h-80">
            </div>
            <h2 class="text-center font-black text-2xl mb-10 text-gray-800 tracking-[5px] uppercase border-b-2 border-orange-100 max-w-sm mx-auto pb-3">Paharer Bazar</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
                {% for p in products %}
                <div class="bg-white rounded-[35px] shadow-sm border border-gray-100 relative overflow-hidden flex flex-col group transition hover:shadow-2xl">
                    {% if p.discount > 0 %}
                    <div class="discount-badge">{{ p.discount }}%<br>ছাড়</div>
                    {% endif %}
                    <a href="/product/{{ p._id }}"><img src="{{ p.image }}" class="w-full h-48 object-cover group-hover:scale-110 transition duration-700"></a>
                    <div class="p-5 flex-grow text-center">
                        <a href="/product/{{ p._id }}"><h3 class="text-base font-black h-12 overflow-hidden text-gray-800 leading-tight mb-2">{{ p.name }}</h3></a>
                        <div class="flex justify-center items-center gap-2">
                            <span class="text-gray-400 line-through text-xs">৳{{ p.price }}</span>
                            <span class="text-orange-600 font-black text-xl">৳{{ p.sale_price }}</span>
                        </div>
                    </div>
                    <a href="/product/{{ p._id }}" class="bg-orange-500 text-white text-center py-5 text-xs font-black uppercase tracking-[3px]">অর্ডার করুন</a>
                </div>
                {% endfor %}
            </div>

        {% elif page == 'detail' %}
            <div class="bg-white rounded-[50px] shadow-sm p-6 md:p-12 border border-gray-50">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div class="relative bg-gray-50 rounded-[45px] p-10 border overflow-hidden">
                        {% if p.discount > 0 %} <div class="discount-badge w-16 h-16 text-sm">{{ p.discount }}%<br>ছাড়</div> {% endif %}
                        <img src="{{ p.image }}" class="w-full max-h-[500px] object-contain mx-auto transition hover:scale-105 duration-500">
                    </div>
                    <div class="flex flex-col">
                        <nav class="text-[11px] text-gray-400 font-black uppercase mb-4 tracking-widest">Home / {{ p.category }}</nav>
                        <h1 class="text-3xl md:text-4xl font-black text-gray-900 leading-tight mb-5">{{ p.name }}</h1>
                        <div class="flex items-baseline gap-4 mb-6">
                            <div class="text-5xl font-black text-orange-600">৳{{ p.sale_price }}</div>
                            <div class="text-gray-400 line-through font-bold text-xl">৳{{ p.price }}</div>
                        </div>
                        
                        <div class="inline-block bg-emerald-800 text-white text-[10px] px-5 py-2 rounded-lg font-black uppercase tracking-[3px] w-fit mb-10 shadow-lg shadow-emerald-100">প্রোডাক্ট কোড : {{ p.code }}</div>

                        <div class="mb-10">
                            <label class="text-xs font-black text-gray-400 block mb-3 uppercase tracking-widest">Weight / Pack:</label>
                            <div class="border-2 border-orange-500 px-8 py-4 rounded-2xl bg-orange-50 text-orange-600 font-black inline-block shadow-sm">📦 {{ p.weight }} - ৳{{ p.sale_price }}</div>
                        </div>

                        <div class="flex gap-5 mb-6">
                            <div class="flex border-2 border-gray-100 rounded-2xl bg-gray-50 px-4 items-center">
                                <button onclick="qtyC(-1)" class="px-5 py-3 text-2xl font-black text-gray-400">-</button>
                                <input id="qty" type="text" value="1" class="w-16 text-center bg-transparent font-black text-xl" readonly>
                                <button onclick="qtyC(1)" class="px-5 py-3 text-2xl font-black text-gray-400">+</button>
                            </div>
                            <button class="flex-1 bg-emerald-600 text-white py-6 rounded-3xl font-black uppercase text-sm shadow-2xl shadow-emerald-100">কার্টে যোগ করুন</button>
                        </div>

                        <a href="/checkout/{{ p._id }}" class="block w-full bg-orange-500 text-white text-center py-6 rounded-[30px] font-black text-2xl shadow-2xl shadow-orange-100 hover:scale-[1.02] transition">অর্ডার কনফার্ম করুন</a>
                        
                        <div class="grid grid-cols-2 gap-4 mt-6">
                            <a href="tel:{{ settings.whatsapp }}" class="bg-gray-900 text-white py-5 rounded-3xl text-center text-xs font-black flex items-center justify-center gap-2">📞 কল করুন</a>
                            <a href="https://wa.me/{{ settings.whatsapp }}" class="bg-emerald-500 text-white py-5 rounded-3xl text-center text-xs font-black flex items-center justify-center gap-2">💬 Whatsapp</a>
                        </div>

                        <div class="mt-16 border-2 border-dashed border-orange-200 rounded-[40px] p-8 bg-orange-50/10">
                            <h4 class="font-black text-gray-800 mb-5 border-b-2 border-orange-100 pb-3 flex items-center gap-3 tracking-widest uppercase text-sm">🚚 ডেলিভারি চার্ট:</h4>
                            <div class="overflow-hidden rounded-3xl border bg-white">
                                <table class="w-full text-sm text-left">
                                    <tr class="bg-gray-50 border-b font-black text-[10px] uppercase tracking-widest"><td class="p-5">ওজন</td><td class="p-5 text-right">খরচ</td></tr>
                                    <tr class="border-b"><td class="p-5 font-bold">সর্বমোট ১ কেজি পর্যন্ত</td><td class="p-5 text-right font-black">৳ ১৩০</td></tr>
                                    <tr class="border-b"><td class="p-5 font-bold">সর্বমোট ২ কেজি পর্যন্ত</td><td class="p-5 text-right font-black">৳ ১৫০</td></tr>
                                    <tr><td class="p-5 font-bold">সর্বমোট ৫ কেজি পর্যন্ত</td><td class="p-5 text-right font-black">৳ ২১০</td></tr>
                                </table>
                            </div>
                            <p class="mt-5 text-[12px] text-orange-600 font-black italic tracking-tighter uppercase">⚠️ {{ p.delivery_text }}</p>
                        </div>
                    </div>
                </div>

                <!-- Tabs -->
                <div class="mt-20">
                    <div class="flex border-b text-sm font-black uppercase tracking-widest overflow-x-auto whitespace-nowrap">
                        <button onclick="tabCh('desc')" id="btn-desc" class="tab-btn active px-10 py-6">Description</button>
                        <button onclick="tabCh('policy')" id="btn-policy" class="tab-btn px-10 py-6">Order Policy</button>
                        <button onclick="tabCh('rev')" id="btn-rev" class="tab-btn px-10 py-6">Review (0)</button>
                    </div>
                    <div id="c-desc" class="py-12 text-gray-700 leading-[2] text-sm p-6 bg-orange-50/5 rounded-b-[40px] border border-t-0">{{ p.description | safe }}</div>
                    <div id="c-policy" class="hidden py-12 text-gray-700 text-sm leading-[2] p-6 bg-gray-50 rounded-b-[40px] border border-t-0">{{ p.order_policy | safe }}</div>
                    <div id="c-rev" class="hidden py-24 text-center text-gray-300 font-black uppercase tracking-[5px]">No Reviews Yet</div>
                </div>
            </div>

        {% elif page == 'checkout' %}
            <div class="max-w-xl mx-auto bg-white p-10 md:p-14 rounded-[55px] shadow-2xl border border-gray-50">
                <h2 class="text-4xl font-black mb-12 text-gray-800 border-b pb-8 flex items-center gap-4">📝 অর্ডার ফর্ম</h2>
                <div class="flex gap-6 mb-12 bg-gray-50 p-6 rounded-[35px] border">
                    <img src="{{ p.image }}" class="w-24 h-24 rounded-3xl object-cover shadow-md">
                    <div>
                        <p class="text-lg font-black text-gray-800 leading-tight">{{ p.name }}</p>
                        <p class="text-orange-600 font-black text-2xl mt-1">৳ {{ p.sale_price }}</p>
                    </div>
                </div>
                <form action="/place-order" method="POST" class="space-y-8">
                    <input type="hidden" name="p_id" value="{{ p._id }}">
                    <div><label class="text-[10px] font-black text-gray-400 uppercase mb-3 block ml-3 tracking-widest">আপনার নাম *</label>
                         <input type="text" name="name" class="w-full border-2 p-6 rounded-[28px] outline-none focus:border-orange-500 transition shadow-inner font-bold" placeholder="সম্পূর্ণ নাম লিখুন" required></div>
                    <div><label class="text-[10px] font-black text-gray-400 uppercase mb-3 block ml-3 tracking-widest">মোবাইল নাম্বার *</label>
                         <input type="text" name="phone" class="w-full border-2 p-6 rounded-[28px] outline-none focus:border-orange-500 transition shadow-inner font-bold" placeholder="017xxxxxxxx" required></div>
                    <div><label class="text-[10px] font-black text-gray-400 uppercase mb-3 block ml-3 tracking-widest">পূর্ণ ঠিকানা (লোকেশন) *</label>
                         <textarea name="address" class="w-full border-2 p-6 rounded-[28px] h-32 outline-none focus:border-orange-500 transition shadow-inner font-bold" placeholder="গ্রাম/এলাকা, থানা, জেলা লিখুন" required></textarea></div>
                    <div>
                        <label class="text-[10px] font-black text-gray-400 uppercase mb-3 block ml-3 tracking-widest">পেমেন্ট মেথড সিলেক্ট করুন</label>
                        <div class="grid grid-cols-1 gap-4">
                            <label class="border-2 p-5 rounded-[25px] flex items-center justify-between cursor-pointer hover:border-orange-500 bg-gray-50 transition">
                                <span class="font-black text-sm">ক্যাশ অন ডেলিভারি (COD)</span>
                                <input type="radio" name="payment" value="COD" checked class="w-6 h-6 accent-orange-600">
                            </label>
                            <label class="border-2 p-5 rounded-[25px] flex items-center justify-between cursor-pointer hover:border-orange-500 bg-emerald-50 transition">
                                <span class="font-black text-sm">বিকাশ পেমেন্ট (Bkash) <br><small class="text-emerald-700 font-bold">পাঠান: {{ settings.bkash }}</small></span>
                                <input type="radio" name="payment" value="Bkash" class="w-6 h-6 accent-emerald-600">
                            </label>
                            <label class="border-2 p-5 rounded-[25px] flex items-center justify-between cursor-pointer hover:border-orange-500 bg-red-50 transition">
                                <span class="font-black text-sm">নগদ পেমেন্ট (Nagad) <br><small class="text-red-700 font-bold">পাঠান: {{ settings.nagad }}</small></span>
                                <input type="radio" name="payment" value="Nagad" class="w-6 h-6 accent-red-600">
                            </label>
                        </div>
                    </div>
                    <button class="w-full bg-orange-600 text-white py-7 rounded-[35px] font-black text-2xl shadow-2xl shadow-orange-200 mt-8 hover:scale-[1.02] transition">অর্ডার সম্পন্ন করুন</button>
                </form>
            </div>

        {% elif page == 'login' %}
            <div class="max-w-md mx-auto bg-white p-14 rounded-[50px] shadow-2xl text-center border mt-10">
                <h2 class="text-4xl font-black mb-12 text-gray-800 tracking-tighter">লগইন</h2>
                <form action="/auth/login" method="POST" class="space-y-6">
                    <input type="text" name="user" placeholder="ইউজারনেম" class="w-full border-2 p-6 rounded-[25px] outline-none font-bold">
                    <input type="password" name="pass" placeholder="পাসওয়ার্ড" class="w-full border-2 p-6 rounded-[25px] outline-none font-bold">
                    <button class="w-full bg-orange-600 text-white py-6 rounded-[25px] font-black text-xl shadow-xl shadow-orange-100">Login</button>
                </form>
                <div class="mt-10 text-xs font-black text-gray-400 uppercase tracking-widest">অ্যাকাউন্ট নেই? <a href="/register" class="text-orange-600">রেজিস্ট্রেশন করুন</a></div>
            </div>

        {% elif page == 'register' %}
            <div class="max-w-md mx-auto bg-white p-14 rounded-[50px] shadow-2xl text-center border mt-10">
                <h2 class="text-4xl font-black mb-12 text-gray-800 tracking-tighter">রেজিস্ট্রেশন</h2>
                <form action="/auth/register" method="POST" class="space-y-6">
                    <input type="text" name="user" placeholder="Username দিন" class="w-full border-2 p-6 rounded-[25px] outline-none font-bold">
                    <input type="password" name="pass" placeholder="Password দিন" class="w-full border-2 p-6 rounded-[25px] outline-none font-bold">
                    <button class="w-full bg-blue-600 text-white py-6 rounded-[25px] font-black text-xl shadow-xl shadow-blue-100">Register</button>
                </form>
            </div>
        {% endif %}
    </main>

    <footer class="bg-white border-t p-16 mt-20 text-center">
        <div class="text-5xl font-black text-orange-600 mb-5">{{ settings.site_name }}</div>
        <p class="text-[11px] text-gray-400 font-black uppercase tracking-[8px] mb-16">Pure & Natural Hill Fruits</p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-12 text-left max-w-5xl mx-auto mb-20 text-sm">
            <div><h4 class="font-black text-gray-800 border-b-2 border-orange-100 pb-3 mb-6 uppercase tracking-widest">Useful Link</h4><ul class="text-gray-500 space-y-4 font-bold"><li>Contact Us</li><li>Order Procedure</li><li>Delivery Rules</li><li>Return Policy</li></ul></div>
            <div><h4 class="font-black text-gray-800 border-b-2 border-orange-100 pb-3 mb-6 uppercase tracking-widest">Company</h4><ul class="text-gray-500 space-y-4 font-bold"><li>All Products</li><li>Return Policy</li><li>Terms & Conditions</li><li>Privacy Policy</li></ul></div>
            <div class="col-span-2 text-right"><h4 class="font-black text-gray-800 border-b-2 border-orange-100 pb-3 mb-6 uppercase tracking-widest">Contact Information</h4><p class="text-gray-500 font-bold leading-relaxed text-base">Address: Muslimpara, Khagrachhari Sadar.<br>Phone/WA: {{ settings.whatsapp }}</p></div>
        </div>
        <div class="bg-orange-600 text-white p-8 text-[11px] font-black tracking-[4px] -mx-16 -mb-16 uppercase">Copyright © 2024 {{ settings.site_name }}. All rights reserved | Designed by Khagrachhari Plus</div>
    </footer>

    <nav class="bottom-nav">
        <button onclick="toggleSidebar()" class="nav-btn text-gray-500"><span class="text-3xl">☰</span><span class="mt-2 uppercase font-black text-[9px] tracking-widest">Category</span></button>
        <a href="https://wa.me/{{ settings.whatsapp }}" class="nav-btn text-emerald-500"><span class="text-3xl">💬</span><span class="mt-2 uppercase font-black text-[9px] tracking-widest">Whatsapp</span></a>
        <a href="/" class="flex flex-col items-center -mt-10"><div class="home-circle text-2xl">🏠</div><span class="mt-4 font-black text-orange-600 text-[10px] uppercase tracking-widest">Home</span></a>
        <div class="nav-btn text-gray-400"><span class="text-3xl">🛒</span><span class="mt-2 uppercase font-black text-[9px]
