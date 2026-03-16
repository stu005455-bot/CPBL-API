import requests
from bs4 import BeautifulSoup
import json
import datetime

print("啟動中職爬蟲...")
today_str = datetime.datetime.now().strftime("%Y/%m/%d")

# 🌟 先把大框架準備好，不管成功或失敗，最後都能存檔
final_data = {"date": today_str, "games": []}

try:
    session = requests.Session()
    url_get = "https://www.cpbl.com.tw/schedule"
    
    # 🌟 高級偽裝術：假裝我們是台灣的繁體中文瀏覽器，並且是從首頁點進來的
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.cpbl.com.tw/"
    }

    print("正在取得最新 Token...")
    response_get = session.get(url_get, headers=headers, timeout=10)
    soup = BeautifulSoup(response_get.text, "html.parser")

    token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
    
    if token_tag:
        token = token_tag["value"]
        print("✅ 成功偷到 Token! 偽裝成功！")
        
        # 帶著 Token 去要分數
        url_api = "https://www.cpbl.com.tw/home/getdetaillist"
        payload = {
            "__RequestVerificationToken": token,
            "GameSno": "",
            "KindCode": "",
            "GameDate": today_str  
        }
        
        response_post = session.post(url_api, data=payload, headers=headers)
        raw_data = response_post.json()
        
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)
            
        if raw_data.get("Success") and raw_data.get("GameADetailJson"):
            game_list_str = raw_data["GameADetailJson"]
            game_list = json.loads(game_list_str) 
            
            if len(game_list) > 0:
                for game in game_list:
                    match_data = {
                        "status": "比賽結束", 
                        "team_away": game.get("VisitingTeamName", "客隊"),
                        "score_away": game.get("VisitingTotalScore", 0),
                        "team_home": game.get("HomeTeamName", "主隊"),
                        "score_home": game.get("HomeTotalScore", 0)
                    }
                    final_data["games"].append(match_data)
            else:
                final_data["games"].append({"status": "這天沒有中職比賽資料喔！"})
        else:
            final_data["games"].append({"status": "無法取得資料，可能沒有比賽。"})
            
    else:
        # 🌟 如果還是被擋，優雅地記錄失敗原因，不要直接當機
        print("❌ 找不到 Token，被中職防火牆擋住了！")
        final_data["games"].append({"status": "爬蟲在國外雲端被中職阻擋了！"})

except Exception as e:
    print("發生未知的錯誤:", e)
    final_data["games"].append({"status": f"發生錯誤: {e}"})

# 🌟 無論如何，最後一定會生出這個檔案交差！
with open("cpbl_score.json", "w", encoding="utf-8") as file:
    json.dump(final_data, file, ensure_ascii=False, indent=4)

print("✅ 程式執行完畢，檔案已寫入。")
