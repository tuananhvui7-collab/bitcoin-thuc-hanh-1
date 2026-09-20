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
    const btnMineBlock = document.getElementById("btn-mine-block");
    
    const ledgerBody = document.getElementById("ledger-body");

    let currentWif = "";
    let fetchInterval = null;
    let mempoolInterval = null;

    const toastEl = document.getElementById('liveToast');
    const toast = new bootstrap.Toast(toastEl, { delay: 7000 });
    const toastBody = document.getElementById("toast-body");

    // Tải danh sách ví đã lưu từ localStorage
    let savedWallets = JSON.parse(localStorage.getItem("saved_wallets") || "[]");
    savedWallets.forEach((wif, index) => {
        const option = document.createElement("option");
        option.value = wif;
        option.text = `Ví Sinh Ra #${index + 1} (${wif.substring(0,6)}...)`;
        walletSelector.appendChild(option);
    });

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
                document.getElementById('bal-legacy').innerText = data.data.balances.legacy;
                
                document.getElementById('addr-nested').innerText = data.data.addresses.nested_segwit;
                document.getElementById('bal-nested').innerText = data.data.balances.nested_segwit;
                
                addrNative.innerText = data.data.addresses.native_segwit;
                document.getElementById('bal-native').innerText = data.data.balances.native_segwit;
                
                addrTaproot.innerText = data.data.addresses.taproot;
                document.getElementById('bal-taproot').innerText = data.data.balances.taproot;
                
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
                    <td><a href="javascript:void(0)" onclick="viewTransactionDetails('${tx.txid}')" class="text-info text-decoration-none" title="${tx.txid}">${tx.txid.substring(0, 8)}...</a></td>
                </tr>
            `;
        });
        ledgerBody.innerHTML = html;
        
        // Expose viewTransactionDetails globally
        window.viewTransactionDetails = async function(txid) {
            const txModal = new bootstrap.Modal(document.getElementById('txModal'));
            const content = document.getElementById('tx-modal-content');
            content.innerHTML = '<div class="text-center"><span class="spinner-border text-info"></span> Đang tải...</div>';
            txModal.show();
            
            try {
                const res = await fetch(`/api/transaction/${txid}`);
                const data = await res.json();
                
                if (data.success) {
                    const tx = data.data;
                    let html = `<div class="mb-3"><strong>TXID:</strong> <span class="text-info">${tx.txid}</span></div>`;
                    html += `<div class="mb-3"><strong>Size:</strong> ${tx.size} bytes | <strong>Weight:</strong> ${tx.weight}</div>`;
                    
                    html += `<h6>Inputs (${tx.vin.length}):</h6>`;
                    tx.vin.forEach((vin, i) => {
                        if (vin.coinbase) {
                            html += `<div class="mb-2 p-2 border border-secondary rounded" style="font-size:0.85rem">Coinbase (Phần thưởng thợ đào)</div>`;
                        } else {
                            html += `<div class="mb-2 p-2 border border-secondary rounded" style="font-size:0.85rem">
                                <div><strong>Txid:</strong> ${vin.txid} : ${vin.vout}</div>
                                ${vin.txinwitness ? `<div><strong>Witness:</strong> Có (${vin.txinwitness.length} phần tử)</div>` : ''}
                            </div>`;
                        }
                    });
                    
                    html += `<h6 class="mt-3">Outputs (${tx.vout.length}):</h6>`;
                    tx.vout.forEach((vout, i) => {
                        const addr = vout.scriptPubKey.address || "N/A";
                        html += `<div class="mb-2 p-2 border border-secondary rounded" style="font-size:0.85rem">
                            <div class="text-success fw-bold">${vout.value} BTC</div>
                            <div><strong>To:</strong> ${addr}</div>
                            <div><strong>Type:</strong> ${vout.scriptPubKey.type}</div>
                        </div>`;
                    });
                    
                    content.innerHTML = html;
                } else {
                    content.innerHTML = `<div class="alert alert-danger">Lỗi: ${data.error}</div>`;
                }
            } catch (error) {
                content.innerHTML = `<div class="alert alert-danger">Lỗi kết nối mạng</div>`;
            }
        };
        
        // Hiện nút Thợ đào nếu có giao dịch đang treo
        if (hasMempool) {
            btnMineBlock.style.display = "block";
        } else {
            btnMineBlock.style.display = "none";
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
                
                // Lưu vào localStorage
                savedWallets.push(wif);
                localStorage.setItem("saved_wallets", JSON.stringify(savedWallets));
                
                // Thêm vào UI
                const option = document.createElement("option");
                option.value = wif;
                option.text = `Ví Sinh Ra #${savedWallets.length} (${wif.substring(0,6)}...)`;
                walletSelector.appendChild(option);
                
                prompt("🎉 Đã tạo Ví thành công!\n\nHãy COPY lại Private Key (WIF) này để đề phòng mất:", wif);
                walletSelector.value = wif;
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

    let pendingTxPayload = null;

    formTransfer.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const amount = inputAmount.value;
        const recipient = inputRecipient.value.trim();
        const feeBtc = inputFeeBtc.value;
        
        if (!amount || amount <= 0 || !recipient || !currentWif || !feeBtc) return;

        const btnBuild = document.getElementById("btn-build-tx");
        const originalText = btnBuild.innerHTML;
        btnBuild.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang tạo mã Hex...';
        btnBuild.disabled = true;

        try {
            const res = await fetch('/api/transaction/build', {
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
                // Lưu dữ liệu để lát phát sóng
                pendingTxPayload = {
                    hex: data.hex,
                    sender_wif: currentWif,
                    recipient_address: recipient,
                    amount: amount,
                    fee: data.fee,
                    selected_utxos: data.selected_utxos
                };
                
                // Render UI Bước 2
                const utxoList = document.getElementById("utxo-list");
                utxoList.innerHTML = '';
                data.selected_utxos.forEach(u => {
                    const isTaproot = u.addr_type === 'taproot';
                    const sigType = isTaproot ? 'SCHNORR' : 'ECDSA';
                    const sigClass = isTaproot ? 'sig-schnorr' : 'sig-ecdsa';
                    
                    // Format addr_type để hiển thị đẹp hơn
                    let addrTypeName = "Legacy";
                    if(u.addr_type === "native_segwit") addrTypeName = "Native Segwit";
                    if(u.addr_type === "nested_segwit") addrTypeName = "Nested Segwit";
                    if(u.addr_type === "taproot") addrTypeName = "Taproot";
                    
                    utxoList.innerHTML += `
                        <div class="utxo-item fade-in">
                            <div>
                                <div class="text-light fw-bold">${u.amount} BTC</div>
                                <div class="text-muted" style="font-size:0.7rem">${u.txid.substring(0,8)}...:${u.vout}</div>
                            </div>
                            <span class="utxo-signature ${sigClass}" title="Được lấy từ ví ${addrTypeName}"><i class="bi bi-pen"></i> ${addrTypeName} - ${sigType}</span>
                        </div>
                    `;
                });
                
                document.getElementById("raw-hex-box").innerText = data.hex;
                
                // Trượt Bước 2 ra
                document.getElementById("step2-panel").style.display = 'block';
                showToast("✅ Đã dựng xong Raw Transaction Hex! Hãy kiểm tra kỹ trước khi phát sóng.");
            } else {
                showToast(`❌ Lỗi: ${data.error}`, false);
            }
        } catch (error) {
            showToast("❌ Lỗi mạng khi gọi API", false);
        } finally {
            btnBuild.innerHTML = originalText;
            btnBuild.disabled = false;
        }
    });

    document.getElementById("btn-cancel-tx").addEventListener("click", () => {
        document.getElementById("step2-panel").style.display = 'none';
        pendingTxPayload = null;
    });

    document.getElementById("btn-broadcast-tx").addEventListener("click", async () => {
        if (!pendingTxPayload) return;
        
        const btnBroadcast = document.getElementById("btn-broadcast-tx");
        const originalText = btnBroadcast.innerHTML;
        btnBroadcast.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang phóng lên Mempool...';
        btnBroadcast.disabled = true;

        try {
            const res = await fetch('/api/transaction/broadcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pendingTxPayload)
            });
            const data = await res.json();
            
            if (data.success) {
                showToast(`✅ Phát sóng thành công!\nTXID: ${data.txid}`);
                inputAmount.value = '';
                inputRecipient.value = '';
                document.getElementById("step2-panel").style.display = 'none';
                pendingTxPayload = null;
                fetchWalletInfo(); 
            } else {
                showToast(`❌ Lỗi Node: ${data.error}`, false);
            }
        } catch (error) {
            showToast("❌ Lỗi kết nối đến Node", false);
        } finally {
            btnBroadcast.innerHTML = originalText;
            btnBroadcast.disabled = false;
        }
    });

    // ---- MINER DASHBOARD LOGIC ---- //

    async function fetchMinerInfo() {
        try {
            const res = await fetch('/api/miner/info');
            const data = await res.json();
            if (data.success) {
                document.getElementById("miner-balance").innerText = data.balance;
                document.getElementById("miner-address").innerText = data.address;
            }
        } catch (e) {
            console.error("Lỗi lấy thông tin ví thợ đào", e);
        }
    }

    async function fetchMempoolData() {
        try {
            const res = await fetch('/api/miner/mempool');
            const data = await res.json();
            if (data.success) {
                document.getElementById("mempool-count").innerText = data.tx_count;
                document.getElementById("mempool-vsize").innerText = data.total_vsize;
                document.getElementById("mempool-fee").innerText = data.total_fee.toFixed(8);
                
                const tbody = document.getElementById("mempool-body");
                if (data.txs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4"><i class="bi bi-wind fs-3 d-block mb-2"></i> Mempool đang trống</td></tr>';
                    btnMineBlock.disabled = true;
                } else {
                    let html = '';
                    data.txs.forEach(tx => {
                        const date = new Date(tx.time * 1000);
                        html += `
                            <tr>
                                <td>${date.toLocaleTimeString()}</td>
                                <td><a href="javascript:void(0)" onclick="viewTransactionDetails('${tx.txid}')" class="text-info text-decoration-none">${tx.txid.substring(0, 10)}...</a></td>
                                <td>${tx.vsize} vB</td>
                                <td class="text-end text-success fw-bold">+${tx.fee}</td>
                            </tr>
                        `;
                    });
                    tbody.innerHTML = html;
                    btnMineBlock.disabled = false; // Bật nút đào
                }
            }
        } catch (e) {
            console.error("Lỗi lấy dữ liệu Mempool", e);
        }
    }

    // Tab switching listener
    const userTab = document.getElementById('user-tab');
    const minerTab = document.getElementById('miner-tab');
    const userControls = document.getElementById('user-nav-controls');

    userTab.addEventListener('show.bs.tab', function (event) {
        userControls.style.display = 'flex';
        if (mempoolInterval) clearInterval(mempoolInterval);
        if (!fetchInterval && currentWif) {
            fetchInterval = setInterval(fetchWalletInfo, 5000);
            fetchWalletInfo();
        }
    });

    minerTab.addEventListener('show.bs.tab', function (event) {
        userControls.style.display = 'none';
        if (fetchInterval) clearInterval(fetchInterval);
        
        // Load initial data
        fetchMinerInfo();
        fetchMempoolData();
        
        // Start polling
        mempoolInterval = setInterval(() => {
            fetchMinerInfo();
            fetchMempoolData();
        }, 5000);
    });

    btnMineBlock.addEventListener("click", async () => {
        const originalText = btnMineBlock.innerHTML;
        btnMineBlock.innerHTML = '<i class="bi bi-gear-wide-connected spin"></i> ĐANG TẠO BLOCK...';
        btnMineBlock.disabled = true;

        try {
            const res = await fetch('/api/mine', { method: 'POST' });
            const data = await res.json();
            
            if (data.success) {
                showToast(`⛏️ Đã khai thác thành công Block #${data.height}!\nĐóng gói ${data.tx_count} giao dịch.\nPhần thưởng: ${data.reward} BTC`);
                fetchMinerInfo();
                fetchMempoolData();
            } else {
                showToast(`❌ Lỗi: ${data.error}`, false);
            }
        } catch (error) {
            showToast("❌ Lỗi mạng", false);
        } finally {
            btnMineBlock.innerHTML = originalText;
            if (document.getElementById("mempool-count").innerText !== "0") {
                btnMineBlock.disabled = false;
            }
        }
    });
});
