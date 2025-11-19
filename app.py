from flask import Flask, render_template_string, request, redirect, url_for, session
import webbrowser
import threading

app = Flask(__name__)
app.secret_key = "mysecretkey" # 啟用 session 功能

# 所有可用的分類
CATEGORIES = ["胸", "背", "腿", "肩", "手臂", "核心"]

# 影片網址轉嵌入格式
def convert_to_embed(url):
    if "youtube.com/shorts/" in url:
        video_id = url.split("shorts/")[-1]
        return f"https://www.youtube.com/embed/{video_id}"
    elif "watch?v=" in url:
        # 處理可能的 &list= 等參數
        video_id = url.split("watch?v=")[-1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    else:
        return url


# ✅ 原始完整的動作資料 (已新增 'category' 欄位)
exercises_data = [
    {"name": "仰臥推舉（槓鈴)", "video": "https://www.youtube.com/watch?v=5SSdbmIjNj4", "category": "胸"},
    {"name": "雙槓臂屈伸（寬握）", "video": "https://www.youtube.com/watch?v=h_JsA3tt0vU", "category": "胸"},
    {"name": "夾胸機", "video": "https://www.youtube.com/watch?v=YKk_gkZOGic", "category": "胸"},
    {"name": "器械推舉", "video": "https://www.youtube.com/embed/qzqz7ScucAg", "category": "胸"},
    {"name": "上斜推舉（啞鈴）單手", "video": "https://www.youtube.com/embed/fMNUiQbRqZw", "category": "胸"},
    {"name": "繩索下拉（Triceps Pushdown）", "video": "https://www.youtube.com/watch?v=dvM2IoxpTnI", "category": "手臂"},
    {"name": "繩索臂屈伸", "video": "https://www.youtube.com/watch?v=W53rZyGHLEQ", "category": "手臂"},
    {"name": "引體向上（正握）", "video": "https://www.youtube.com/watch?v=rffAYLTSMJY", "category": "背"},
    {"name": "槓鈴划船", "video": "https://www.youtube.com/watch?v=0CGyZUqqzIc", "category": "背"},
    {"name": "坐姿划船機(窄握)", "video": "https://www.youtube.com/watch?v=IjqCKVy4WXA", "category": "背"},
    {"name": "高位下拉（正握）", "video": "https://www.youtube.com/watch?v=wV1nVjAPGHs", "category": "背"},
    {"name": "面拉（Face Pull）", "video": "https://www.youtube.com/watch?v=89yerIMpGX4", "category": "肩"}, # 針對後三角肌
    {"name": "啞鈴彎舉", "video": "https://www.youtube.com/watch?v=igppHAAIdT4", "category": "手臂"},
    {"name": "繩索彎舉", "video": "https://www.youtube.com/watch?v=IWu_vf_0tfo", "category": "手臂"},
    {"name": "硬舉（傳統 / 羅馬尼亞式）", "video": "https://www.youtube.com/watch?v=xQ6cLsq2bjA", "category": "腿"},
    {"name": "腿推機（Leg Press）", "video": "https://www.youtube.com/watch?v=EotSw18oR9w", "category": "腿"},
    {"name": "腿彎舉（Leg Curl）", "video": "https://www.youtube.com/watch?v=SgzUqJ3HCAk", "category": "腿"},
    {"name": "腿伸展（Leg Extension）", "video": "https://www.youtube.com/watch?v=cSUYSxZHhg8", "category": "腿"},
    {"name": "仰臥抬腿", "video": "https://www.youtube.com/watch?v=wXDnKR_GkcE", "category": "核心"},
    {"name": "腹部捲機", "video": "https://www.youtube.com/watch?v=tTow_SbxB-E", "category": "核心"},
    {"name": "啞鈴肩推（坐姿）", "video": "https://www.youtube.com/watch?v=usPnudgiaDA", "category": "肩"},
    {"name": "器械肩推", "video": "https://www.youtube.com/watch?v=QlOEm34TkDs", "category": "肩"},
    {"name": "側平舉", "video": "https://www.youtube.com/watch?v=Kl3LEzQ5Zqs", "category": "肩"},
    {"name": "前平舉", "video": "https://www.youtube.com/watch?v=1lXa528j0Vs", "category": "肩"},
    {"name": "反向飛鳥", "video": "https://www.youtube.com/watch?v=CizCvKdvBP0", "category": "肩"},
]

# 處理影片網址為嵌入格式
for ex in exercises_data:
    ex["video"] = convert_to_embed(ex["video"])


# ✅ HTML 模板（內含收藏清單、分類篩選和動作名稱選單）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>健身影片查詢網站</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #f4f7f9; text-align: center; color: #333; }
        .container { max-width: 1200px; margin: 20px auto; padding: 0 15px; }
        h1 { color: #1e88e5; }
        form { margin-bottom: 25px; display: flex; justify-content: center; gap: 10px; align-items: center; }
        input[type="text"], select { 
            padding: 10px; 
            border: 1px solid #ccc; 
            border-radius: 6px; 
            font-size: 16px;
        }
        input[type="text"] { width: 300px; max-width: 30%; } /* 縮小搜尋框寬度 */
        select { max-width: 30%; }
        button, .fav-link {
            padding: 10px 15px; 
            background-color: #4caf50; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            text-decoration: none;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        button:hover { background-color: #388e3c; }
        .fav-link { background-color: #fbc02d; color: #333; }
        .fav-link:hover { background-color: #f9a825; }

        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 20px; 
            margin-top: 20px; 
        }
        .card { 
            background: white; 
            border-radius: 12px; 
            padding: 15px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        }
        iframe { border-radius: 8px; width: 100%; height: 180px; border: none; }
        h2 { font-size: 1.2em; margin-top: 5px; margin-bottom: 10px; color: #1e88e5; }
        .action-link { 
            text-decoration: none; 
            padding: 5px 10px; 
            border-radius: 5px;
            display: inline-block;
            margin-top: 5px;
            font-weight: bold;
        }
        .add-fav { background-color: #e3f2fd; color: #1e88e5; }
        .add-fav:hover { background-color: #bbdefb; }
        .remove-fav { color: #d32f2f; margin-left: 10px; }
        .remove-fav:hover { text-decoration: underline; }
        .favorite-status { color: #4caf50; font-weight: bold; }

        @media (max-width: 900px) {
            form { flex-wrap: wrap; } /* 允許表單元素換行 */
            input[type="text"], select, button, .fav-link { 
                max-width: 90%; 
                width: 90%; 
                margin: 5px 0; 
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💪 健身影片查詢系統</h1>
        <form method="get" action="/">
            <!-- 分類篩選選單 -->
            <select name="category" onchange="this.form.submit()">
                <option value="">所有分類</option>
                {% for cat in categories %}
                    <option value="{{ cat }}" {% if category == cat %}selected{% endif %}>{{ cat }}</option>
                {% endfor %}
            </select>

            <!-- 動作名稱選單 (新增) -->
            <select name="exercise_name" onchange="this.form.submit()">
                <option value="">所有動作 (點選下拉)</option>
                {% for ex_name in all_exercise_names %}
                    <option value="{{ ex_name }}" {% if selected_exercise == ex_name %}selected{% endif %}>{{ ex_name }}</option>
                {% endfor %}
            </select>
            
            <input type="text" name="search" placeholder="輸入動作名稱搜尋" value="{{ keyword }}">
            <button type="submit">搜尋</button>
            <a href="/favorites" class="fav-link">查看收藏清單 ({{ fav_count }})</a>
        </form>

        <div class="grid">
            {% for ex in exercises %}
            <div class="card">
                <h2>{{ ex.name }}</h2>
                <!-- 使用 ex.video 已經是嵌入格式的 URL -->
                <iframe src="{{ ex.video }}" title="{{ ex.name }}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                <p>分類：<span style="font-weight: bold; color: #ff9800;">{{ ex.category }}</span></p>
                {% if ex.name in favorites %}
                    <span class="favorite-status">✅ 已收藏</span> 
                    <a href="/remove_favorite/{{ ex.name }}" class="remove-fav">❌ 移除</a>
                {% else %}
                    <a href="/add_favorite/{{ ex.name }}" class="action-link add-fav">⭐ 加入收藏</a>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% if not exercises %}
            <p style="margin-top: 40px; color: #757575;">查無相關動作，請嘗試不同的關鍵字、分類或動作名稱。</p>
        {% endif %}
    </div>
</body>
</html>
"""

# ✅ 收藏頁面模板 (未變動，但一併列出)
FAV_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的收藏清單</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #f4f7f9; text-align: center; color: #333; }
        h1 { color: #1e88e5; margin-bottom: 10px; }
        a { text-decoration: none; color: #1e88e5; font-weight: bold; transition: color 0.3s; }
        a:hover { color: #0d47a1; }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 20px; 
            max-width: 1200px; 
            margin: 20px auto; 
            padding: 0 15px;
        }
        .card { 
            background: white; 
            border-radius: 12px; 
            padding: 15px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
        }
        h2 { font-size: 1.2em; margin-top: 5px; margin-bottom: 10px; color: #1e88e5; }
        iframe { border-radius: 8px; width: 100%; height: 180px; border: none; }
        .remove-link { 
            color: #d32f2f; 
            display: inline-block; 
            margin-top: 10px; 
            padding: 5px 10px;
            border: 1px solid #d32f2f;
            border-radius: 5px;
        }
        .remove-link:hover { background-color: #ef9a9a; color: white; }
    </style>
</head>
<body>
    <h1>⭐ 我的收藏清單</h1>
    {% if not favorites %}
        <p style="margin-top: 40px; color: #757575;">您的收藏清單是空的！<a href="/">立即前往主頁瀏覽</a></p>
    {% endif %}
    <a href="/">← 返回主頁</a>
    <div class="grid">
        {% for ex in favorites %}
        <div class="card">
            <h2>{{ ex.name }}</h2>
            <iframe src="{{ ex.video }}" title="{{ ex.name }}" allowfullscreen></iframe>
            <p>分類：<span style="font-weight: bold; color: #ff9800;">{{ ex.category }}</span></p>
            <a href="/remove_favorite/{{ ex.name }}" class="remove-link">❌ 移除收藏</a>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""


@app.route('/')
def index():
    # 取得搜尋關鍵字、分類參數，以及新增的動作名稱參數
    keyword = request.args.get("search", "")
    category = request.args.get("category", "")
    exercise_name = request.args.get("exercise_name", "") # <<< 新增動作名稱參數
    
    # 初始化過濾後的列表為所有動作
    filtered = exercises_data
    
    # 優先篩選邏輯：如果直接選了動作名稱，則只顯示該動作，忽略分類和關鍵字
    if exercise_name:
        filtered = [ex for ex in filtered if ex["name"] == exercise_name]
    else:
        # 1. 根據分類篩選
        if category:
            filtered = [ex for ex in filtered if ex["category"] == category]

        # 2. 根據關鍵字篩選
        if keyword:
            filtered = [ex for ex in filtered if keyword.lower() in ex["name"].lower()]

    # 取得收藏清單
    favorites = session.get("favorites", [])
    fav_names = [f["name"] for f in favorites]
    
    # 取得所有動作名稱供下拉式選單使用
    all_names = sorted([ex["name"] for ex in exercises_data])

    return render_template_string(HTML_TEMPLATE,
                                  exercises=filtered,
                                  keyword=keyword,
                                  category=category, 
                                  categories=CATEGORIES, 
                                  favorites=fav_names,
                                  fav_count=len(favorites),
                                  
                                  # 傳遞新的動作名稱相關變數
                                  all_exercise_names=all_names,
                                  selected_exercise=exercise_name)


@app.route('/add_favorite/<name>')
def add_favorite(name):
    favorites = session.get("favorites", [])
    ex_to_add = next((ex for ex in exercises_data if ex["name"] == name), None)
    
    if ex_to_add and ex_to_add["name"] not in [f["name"] for f in favorites]:
        favorites.append(ex_to_add)
    
    session["favorites"] = favorites
    
    # 導回主頁並保留當前的篩選狀態 (包含新增的 exercise_name)
    keyword = request.args.get("search", "")
    category = request.args.get("category", "")
    exercise_name = request.args.get("exercise_name", "") # <<< 新增
    return redirect(url_for('index', search=keyword, category=category, exercise_name=exercise_name))


@app.route('/remove_favorite/<name>')
def remove_favorite(name):
    favorites = session.get("favorites", [])
    favorites = [ex for ex in favorites if ex["name"] != name]
    session["favorites"] = favorites
    
    referrer = request.referrer or url_for('index')
    if url_for('show_favorites') in referrer:
        return redirect(url_for('show_favorites'))
    else:
        # 導回主頁並保留當前的篩選狀態 (包含新增的 exercise_name)
        keyword = request.args.get("search", "")
        category = request.args.get("category", "")
        exercise_name = request.args.get("exercise_name", "") # <<< 新增
        return redirect(url_for('index', search=keyword, category=category, exercise_name=exercise_name))


@app.route('/favorites')
def show_favorites():
    favorites = session.get("favorites", [])
    return render_template_string(FAV_TEMPLATE, favorites=favorites)


def open_browser():
    # 僅用於本地執行，在線上環境中不需要
    # webbrowser.open("http://127.0.0.1:5000/")
    pass 

if __name__ == "__main__":
    # 在 Spyder 或其他 IDE 中執行時，可以註釋掉下面這行，然後手動開啟瀏覽器
    # threading.Timer(1.5, open_browser).start() 
    
    # 運行 Flask 應用程式。當您在 Spyder 中執行此檔案後，
    # 請在瀏覽器中手動輸入：http://127.0.0.1:5000/
    app.run(debug=False)

