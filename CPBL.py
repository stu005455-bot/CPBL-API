import requests
import datetime
from bs4 import BeautifulSoup
import json

print("啟動中職爬蟲...")

# 1. 建立一個「會話 (Session)」
# 這非常重要！它可以幫我們記住伺服器給的隱形 Cookie，沒有它 Token 會失效
session = requests.Session()

# 2. 先去中職首頁「偷」出最新的防機器人 Token
url_get = "https://www.cpbl.com.tw/schedule"

# 假裝我們是正常的瀏覽器 (這是爬蟲必備的防護罩)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("正在取得最新 Token...")
response_get = session.get(url_get, headers=headers)
soup = BeautifulSoup(response_get.text, "html.parser")

# 用 BS4 從幾萬字原始碼中，精準挖出名為 __RequestVerificationToken 的隱藏欄位
token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
if token_tag:
    token = token_tag["value"]
    print("✅ 成功偷到 Token!")
else:
    print("❌ 找不到 Token，可能網頁改版了")
    exit()

# 3. 帶著新鮮的 Token，去敲那支隱藏版 API 的門！
today_str = datetime.datetime.now().strftime("%Y/%m/%d")
url_api = "https://www.cpbl.com.tw/home/getdetaillist"
payload = {
    "__RequestVerificationToken": token,
    "GameSno": "",
    "KindCode": "",
    "GameDate": today_str  # 🌟 把原本硬寫的日期，換成這個自動變數！
}

print("正在向中職伺服器索取比分...")
response_post = session.post(url_api, data=payload, headers=headers)
raw_data = response_post.json()

# 4. 拆解中職特有的「雙層紙箱」包裝
# 先建立一個最終要存檔的「大框架」，準備把所有比賽塞進 games 裡面
#today_str = "2026/03/15" # 測試用，測完記得改回 datetime 自動抓今天
final_data = {
    "date": today_str,
    "games": []
}

if raw_data.get("Success") and raw_data.get("GameADetailJson"):
    game_list_str = raw_data["GameADetailJson"]
    game_list = json.loads(game_list_str) 
    
    if len(game_list) > 0:
        # 🌟 魔法改裝：用 for 迴圈把當天「所有」比賽一次抓齊！
        for game in game_list:
            match_data = {
                "status": "比賽結束", 
                "team_away": game.get("VisitingTeamName", "客隊"),
                "score_away": game.get("VisitingTotalScore", 0),
                "team_home": game.get("HomeTeamName", "主隊"),
                "score_home": game.get("HomeTotalScore", 0)
            }
            # 把每一場比賽的資料，新增到 final_data 的 games 清單裡
            final_data["games"].append(match_data)
    else:
        final_data["games"].append({"status": "這天沒有中職比賽資料喔！"})
else:
    final_data["games"].append({"status": "無法取得資料，可能沒有比賽。"})

# 5. 存成 cpbl_score.json 檔案
with open("cpbl_score.json", "w", encoding="utf-8") as file:
    json.dump(final_data, file, ensure_ascii=False, indent=4)

print("✅ 大功告成！完美破解中職 API！")
print("今日戰況：", json.dumps(final_data, ensure_ascii=False, indent=2))