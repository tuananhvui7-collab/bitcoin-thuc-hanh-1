# Hướng Dẫn Đóng Gói Docker (Giai đoạn 3)

Docker là công cụ tối thượng để đảm bảo dự án chạy được trên **bất kỳ máy tính nào** mà không cần phải cài cắm thủ công (Không cần cài Node, không cần cài Python). 
Chỉ với 1 lệnh `docker-compose up`, hệ thống sẽ tự động tải Bitcoin, tải Python, cài thư viện và bật Web App lên.

## 1. Cấu trúc file `docker-compose.yml`
File này nằm ở thư mục gốc, định nghĩa 2 cỗ máy ảo (Services) chạy song song và nối mạng LAN với nhau (Network `btc-lab`):

### Service A: `bitcoind`
- **Image:** `bitcoin/bitcoin:28.0` (Tải bộ cài Node nguyên bản từ DockerHub).
- **Command:** Chạy các lệnh khởi tạo y hệt như cấu hình tay (`-regtest=1`, `-server=1`, v.v...).
- **Ports:** Ánh xạ cổng `18443` (Cổng RPC mặc định) ra ngoài máy thật.

### Service B: `app`
- **Context:** Thư mục `./src`. Nó sẽ nhìn vào file `Dockerfile` trong thư mục `src` để build ra môi trường Python.
- **Environment:** 
  - `RPC_HOST=bitcoind`: (Đặc biệt lưu ý) Khi chạy trong Docker, Web App KHÔNG ĐƯỢC gọi Node bằng `127.0.0.1` nữa. Thay vào đó, nó phải gọi bằng Tên Service của Node là `bitcoind`. Docker sẽ tự phân giải DNS.
- **Depends_on:** `bitcoind` (Ép máy ảo Node phải khởi động xong thì Web App mới được phép bật).
- **Ports:** Ánh xạ cổng `5000` ra ngoài để bạn xem Web.

## 2. Cấu trúc file `src/Dockerfile`
File này hướng dẫn Docker cách bọc cái Backend Flask của ta lại:
1. `FROM python:3.10-slim`: Lấy một bản Windows/Linux mini chỉ có Python.
2. `COPY requirements.txt`: Chép danh sách thư viện vào.
3. `RUN pip install -r`: Cài `flask`, `python-bitcoin-utils`...
4. `COPY . .`: Chép toàn bộ mã nguồn của ta vào.
5. `CMD ["python", "app.py"]`: Bật server!

## 3. Cách Sử Dụng
Giảng viên (hoặc bạn) chỉ cần ném toàn bộ thư mục này vào máy tính có cài sẵn Docker Desktop, mở Terminal và gõ:

```bash
docker-compose up -d --build
```
Và bùm! Vào thẳng `http://localhost:5000` tận hưởng thành quả.
