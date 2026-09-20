from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey

# Khởi tạo môi trường Regtest
setup('regtest')

# Tạo một Private Key hoàn toàn ngẫu nhiên (chưa từng tồn tại)
priv = PrivateKey()

print("=========================================")
print("🎉 Đã tạo một Ví mới thành công!")
print("=========================================")
print("🔑 Private Key (WIF):", priv.to_wif())
print("=========================================")
print("👉 Hãy copy chuỗi WIF trên, quay lại Web App, bấm nút 'Dùng WIF Khác' và dán vào để đăng nhập nhé!")
