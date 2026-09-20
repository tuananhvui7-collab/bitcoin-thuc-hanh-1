document.addEventListener("DOMContentLoaded", () => {
    
    const walletSelector = document.getElementById("wallet-selector");
    const btnCustomWif = document.getElementById("btn-custom-wif");
    const mainDashboard = document.getElementById("main-dashboard");
    const loginPrompt = document.getElementById("login-prompt");
    
    const myBalance = document.getElementById("my-balance");
    const addrLegacy = document.getElementById("addr-legacy");
    const addrNative = document.getElementById("addr-native");
    const addrTaproot = document.getElementById("addr-taproot");
    
    const formTransfer = document.getElementById("transfer-form");
    const inputRecipient = document.getElementById("recipient-addr");
    const inputAmount = document.getElementById("amount");
    const inputFeeBtc = document.getElementById("fee-btc");
    const btnTransfer = document.getElementById("btn-transfer");
    const btnMine = document.getElementById("btn-mine");
    
    const ledgerBody = document.getElementById("ledger-body");

    let currentWif = "";
    let fetchInterval = null;

    const toastEl = document.getElementById('liveToast');
    const toast = new bootstrap.Toast(toastEl, { delay: 7000 });
    const toastBody = document.getElementById("toast-body");

    function showToast(message, isSuccess = true) {
        toastBody.innerText = message;
        toastEl.classList.remove('text-bg-primary', 'text-bg-danger', 'text-bg-success');
        toastEl.classList.add(isSuccess ? 'text-bg-success' : 'text-bg-danger');
        toast.show();
    }

    async function fetchWalletInfo() {
        if (!currentWif) return;
        try {
            const res = await fetch(`/api/wallet/info?wif=${currentWif}`);
            const data = await res.json();
            if (data.success) {
                if (myBalance.innerText !== data.data.total_balance) myBalance.innerText = data.data.total_balance;
                addrLegacy.innerText = data.data.addresses.legacy;
                addrNative.innerText = data.data.addresses.native_segwit;
                addrTaproot.innerText = data.data.addresses.taproot;
                
                // Hiển thị Sổ cái
                renderLedger(data.history);
            } else {
                showToast(`❌ Lỗi Node: ${data.error}`, false);
            }
        } catch (error) {
            console.error("Lỗi tải ví:", error);
            showToast("❌ Lỗi mất kết nối với Máy chủ Flask", false);
        }
    }
    
    function renderLedger(history) {
        if (!history || history.length === 0) {
            ledgerBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Chưa có giao dịch nào</td></tr>';
            btnMine.style.display = "none";
            return;
        }
        
        let html = '';
        let hasMempool = false;
        
        history.slice().reverse().forEach(tx => {
            if (tx.status === 'Mempool') hasMempool = true;
            
            const statusBadge = tx.status === 'Mempool' 
                ? '<span class="badge text-bg-warning">Đang chờ (Mempool)</span>' 
                : '<span class="badge text-bg-success">Hoàn thành</span>';
                
            html += `
                <tr>
                    <td>${tx.time}</td>
                    <td title="${tx.recipient}">${tx.recipient.substring(0, 10)}...</td>
                    <td class="text-danger">-${tx.amount}</td>
                    <td class="text-muted">${tx.fee}</td>
                    <td>${statusBadge}</td>
                    <td><a href="#" class="text-info text-decoration-none" title="${tx.txid}">${tx.txid.substring(0, 8)}...</a></td>
                </tr>
            `;
        });
        ledgerBody.innerHTML = html;
        
        // Hiện nút Thợ đào nếu có giao dịch đang treo
        if (hasMempool) {
            btnMine.style.display = "block";
        } else {
            btnMine.style.display = "none";
        }
    }

    function login(wif) {
        currentWif = wif;
        loginPrompt.style.display = "none";
        mainDashboard.style.display = "block";
        fetchWalletInfo();
        
        if (fetchInterval) clearInterval(fetchInterval);
        fetchInterval = setInterval(fetchWalletInfo, 5000);
    }

    walletSelector.addEventListener("change", (e) => {
        login(e.target.value);
    });

    btnCustomWif.addEventListener("click", () => {
        const wif = prompt("Vui lòng nhập Private Key (WIF) của bạn:");
        if (wif && wif.trim() !== "") {
            walletSelector.selectedIndex = 0;
            login(wif.trim());
        }
    });

    const btnCreateWallet = document.getElementById("btn-create-wallet");
    btnCreateWallet.addEventListener("click", async () => {
        try {
            btnCreateWallet.innerHTML = '<span class="spinner-border spinner-border-sm"></span>...';
            btnCreateWallet.disabled = true;
            
            const res = await fetch('/api/wallet/new');
            const data = await res.json();
            
            if (data.success) {
                const wif = data.wif;
                prompt("🎉 Đã tạo Ví thành công!\n\nHãy COPY lại Private Key (WIF) này để dùng lần sau:", wif);
                walletSelector.selectedIndex = 0;
                login(wif);
                showToast("Ví mới đã được tạo và tự động đăng nhập!");
            } else {
                showToast("❌ Lỗi tạo ví", false);
            }
        } catch (e) {
            showToast("❌ Lỗi mạng", false);
        } finally {
            btnCreateWallet.innerHTML = 'Tạo Ví Mới';
            btnCreateWallet.disabled = false;
        }
    });

    formTransfer.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const amount = inputAmount.value;
        const recipient = inputRecipient.value.trim();
        const feeBtc = inputFeeBtc.value;
        
        if (!amount || amount <= 0 || !recipient || !currentWif || !feeBtc) return;

        const originalText = btnTransfer.innerHTML;
        btnTransfer.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang xử lý...';
        btnTransfer.disabled = true;

        try {
            const res = await fetch('/api/transfer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    sender_wif: currentWif,
                    recipient_address: recipient,
                    amount: amount,
                    absolute_fee: feeBtc
                })
            });
            const data = await res.json();
            
            if (data.success) {
                showToast(`✅ ${data.message}\nTXID: ${data.txid}`);
                inputAmount.value = '';
                inputRecipient.value = '';
                fetchWalletInfo(); 
            } else {
                showToast(`❌ Lỗi: ${data.error}`, false);
            }
        } catch (error) {
            showToast("❌ Lỗi mạng khi gửi API", false);
        } finally {
            btnTransfer.innerHTML = originalText;
            btnTransfer.disabled = false;
        }
    });

    btnMine.addEventListener("click", async () => {
        const originalText = btnMine.innerHTML;
        btnMine.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang Đào...';
        btnMine.disabled = true;

        try {
            const res = await fetch('/api/mine', { method: 'POST' });
            const data = await res.json();
            
            if (data.success) {
                showToast(`⛏️ Thợ đào đóng Block thành công!\nHash: ${data.block_hash.substring(0, 15)}...\nTiền thưởng (Gồm cả phí): ${data.reward} BTC`);
                fetchWalletInfo();
            } else {
                showToast(`❌ Lỗi: ${data.error}`, false);
            }
        } catch (error) {
            showToast("❌ Lỗi mạng", false);
        } finally {
            btnMine.innerHTML = originalText;
            btnMine.disabled = false;
        }
    });
});
