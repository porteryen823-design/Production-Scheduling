
import socket


# =====================================================
# Windows Unicode Output Encoding Fix
# =====================================================
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def tcp_client():
    # 建立 TCP socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 連線到指定 IP 和 Port
        client.connect(("192.168.0.50", 5000))
        print("已連線到 192.168.0.50:5000")

        # 傳送 ASCII 訊息
        message = "ABC"
        client.sendall(message.encode("ascii"))
        print(f"已送出: {message}")

    except Exception as e:
        print(f"連線錯誤: {e}")
    finally:
        # 關閉連線
        client.close()
        print("連線已關閉")

if __name__ == "__main__":
    tcp_client()