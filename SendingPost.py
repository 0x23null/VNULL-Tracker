import time
import tls_client # Thư viện quan trọng để bypass lỗi auth_failure

# ================= CẤU HÌNH =================
# API Key của bạn tại 2crawler
API_KEY_2CRAWLER = "f0d12152-e100-42e4-81cb-0eb007f6528d"

# Tài khoản Riot Games cần đăng nhập
USERNAME = "z0z0z04455"
PASSWORD = "dailoi123"

# URL Endpoint của Riot
RIOT_AUTH_URL = "https://auth.riotgames.com/api/v1/authorization"
# ============================================

# Khởi tạo Session với vân tay giả lập Chrome 120 (Mấu chốt để sửa lỗi Handshake)
session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

def solve_hcaptcha(site_key, rqdata):
    """
    Hàm giải Captcha Enterprise sử dụng API 2crawler.
    """
    print(f"   [2Crawler] Đang gửi yêu cầu giải Captcha Enterprise...")
    print(f"   [2Crawler] SiteKey: {site_key[:20]}...")
    if rqdata:
        print(f"   [2Crawler] RQData: Có (Độ dài: {len(rqdata)})")

    # 1. Tạo Task giải [cite: 12]
    create_url = "https://tools.2crawler.rest/api/v1/solver/"
    payload = {
        "key": API_KEY_2CRAWLER,        # Key trong JSON body [cite: 7]
        "captcha": "hcaptcha",          # Loại captcha [cite: 19]
        "site_key": site_key,           # Site Key của Riot [cite: 21]
        "solver_url": "https://auth.riotgames.com/", # [cite: 20]
        "rqdata": rqdata                # Tham số quan trọng cho Enterprise
    }

    try:
        # Gửi POST request
        resp = session.post(create_url, json=payload).json()
        
        if "id" not in resp:
            print(f"   ❌ [2Crawler] Lỗi tạo task: {resp}")
            return None
        
        task_id = resp["id"] # Lấy ID task [cite: 25]
        print(f"   ✅ [2Crawler] Task ID: {task_id}. Đang chờ kết quả...")

        # 2. Lấy kết quả (Polling) [cite: 39]
        result_url = f"https://tools.2crawler.rest/api/v1/solver/{task_id}/"
        # GET request yêu cầu Token trong Header [cite: 10]
        headers = {"Authorization": f"Token {API_KEY_2CRAWLER}"}

        for i in range(20): # Thử tối đa 100 giây
            time.sleep(5)
            check_resp = session.get(result_url, headers=headers).json()
            
            status = check_resp.get("status")
            if status == "su": # su = Success [cite: 47]
                token = check_resp.get("resolver_solution") # [cite: 48]
                print(f"   🎉 [2Crawler] Giải thành công!")
                return token
            elif status == "pr": # pr = Processing
                print(".", end="", flush=True)
            else:
                print(f"\n   ❌ [2Crawler] Lỗi hoặc trạng thái lạ: {status}")
                return None
                
    except Exception as e:
        print(f"   ❌ [2Crawler] Lỗi kết nối API: {e}")
        return None
    
    print("\n   ❌ [2Crawler] Hết thời gian chờ.")
    return None

def login_riot_flow():
    print(f"🚀 Bắt đầu đăng nhập cho tài khoản: {USERNAME}")
    
    # Headers chuẩn như trình duyệt thật
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    # --- BƯỚC 1: HANDSHAKE & INIT (Sửa lỗi auth_failure tại đây) ---
    print(">> Bước 1: Gửi yêu cầu khởi tạo (Handshake)...")
    init_payload = {
        "client_id": "riot-client",
        "nonce": "1",
        "redirect_uri": "http://localhost/redirect",
        "response_type": "token id_token",
        "scope": "openid link ban lol_region"
    }
    # tls_client sẽ tự động xử lý cookies và handshake chuẩn
    session.post(RIOT_AUTH_URL, json=init_payload, headers=headers)

    # --- BƯỚC 2: GỬI THÔNG TIN ĐĂNG NHẬP ---
    print(">> Bước 2: Gửi Username & Password...")
    auth_payload = {
        "type": "auth",
        "username": USERNAME,
        "password": PASSWORD,
        "remember": True
    }
    
    # Sử dụng PUT cho bước đăng nhập
    resp = session.put(RIOT_AUTH_URL, json=auth_payload, headers=headers)
    data = resp.json()

    # --- BƯỚC 3: XỬ LÝ PHẢN HỒI ---
    if data.get("type") == "response":
        # Trường hợp 1: Vào thẳng luôn (Do tls_client giả lập tốt)
        print("\n✅ ĐĂNG NHẬP THÀNH CÔNG (Không cần Captcha)!")
        # Token ở đây: data['response']['parameters']['uri']
        return True

    elif data.get("type") == "captcha":
        # Trường hợp 2: Riot yêu cầu Captcha
        print("\n🛡️  Phát hiện Captcha! Đang xử lý...")
        
        captcha_info = data.get("captcha", {})
        site_key = captcha_info.get("sitekey")
        rqdata = captcha_info.get("rqdata") # Lấy rqdata từ Riot
        
        # Gọi hàm giải
        solution = solve_hcaptcha(site_key, rqdata)
        
        if solution:
            # Gửi lại kèm token giải được
            print(">> Bước 3: Gửi lại thông tin kèm Token Captcha...")
            auth_payload["h-captcha-response"] = solution
            
            final_resp = session.put(RIOT_AUTH_URL, json=auth_payload, headers=headers)
            final_data = final_resp.json()
            
            if final_data.get("type") == "response":
                print("\n✅ ĐĂNG NHẬP THÀNH CÔNG (Sau khi giải Captcha)!")
                return True
            else:
                print(f"\n❌ Đăng nhập thất bại sau khi giải: {final_data}")
        else:
            print("\n❌ Không lấy được token từ 2crawler.")

    elif "error" in data:
        # Trường hợp 3: Lỗi (Nếu vẫn auth_failure thì là sai pass thật, vì TLS đã chuẩn)
        print(f"\n❌ Lỗi từ Riot: {data['error']}")
        if data['error'] == 'auth_failure':
            print("   -> Kiểm tra lại chính xác Username/Password.")
    else:
        print(f"\n❓ Phản hồi lạ: {data}")

if __name__ == "__main__":
    login_riot_flow()