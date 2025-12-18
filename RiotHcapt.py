import requests
import time
import sys


API_KEY = 'f0d12152-e100-42e4-81cb-0eb007f6528d' 

SITE_KEY = 'a5f74b19-9e45-40e0-b45d-47ff91b7a6c2' # Kiểm tra lại sitekey thực tế của Riot
PAGE_URL = 'https://auth.riotgames.com/' # URL trang đăng nhập Riot
API_URL = "https://tools.2crawler.rest/api/v1/solver/"

def test_2crawler_final():
    print(f">> Sending request hcaptcha...")


    payload = {
        "key": API_KEY,
        "captcha": "hcaptcha",
        "site_key": SITE_KEY,
        "solver_url": PAGE_URL
    }

    try:
        resp = requests.post(API_URL, json=payload)
        data = resp.json()
    except Exception as e:
        print(f"Network connection error: {e}")
        return

    task_id = data.get("id")
    if not task_id:
        print(f"Creating task eror: {data}")
        return

    print(f"✅ Send successfully [Task ID]: {task_id}")
    print("⏳ Waiting for result")

    
    result_url = f"{API_URL}{task_id}/"
    
    
    for i in range(60): 
        time.sleep(5) 
        try:
            
            check_resp = requests.get(result_url, params={"key": API_KEY})
            res_json = check_resp.json()
        except:
            continue

        
        if res_json.get('status') == 'su':
            token = res_json.get('resolver_solution')
            print("\n" + "="*40)
            print("🎉 Solve successfully")
            print("="*40)
            print(f"Token: {token}")
            return token

        
        if res_json.get('status') == 'pr':
            print(".", end="", flush=True)
            continue

        
        detail_msg = res_json.get('detail', '')
        
        
        if 'ready' in detail_msg or 'wait' in detail_msg:
            print(".", end="", flush=True)
            continue
        
        
        if detail_msg:
            print(f"\n❌ Error from server: {detail_msg}")
            return
            
        
        print(".", end="", flush=True)

    print("\n❌ Timeout")

if __name__ == "__main__":
    test_2crawler_final()