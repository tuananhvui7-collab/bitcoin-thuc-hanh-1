document.addEventListener("DOMContentLoaded", () => {

    // =========================================================
    // STATE
    // =========================================================
    let currentWif = localStorage.getItem("last_wif") || "";
    let currentPage = 1;
    const historyLimit = 10;
    let isFetching = false;         // Guard tránh concurrent requests
    let fetchInterval = null;
    let mempoolInterval = null;

    // =========================================================
    // DOM REFS
    // =========================================================
    const walletSelector    = document.getElementById("wallet-selector");
    const btnCustomWif      = document.getElementById("btn-custom-wif");
    const mainDashboard     = document.getElementById("main-dashboard");
    const loginPrompt       = document.getElementById("login-prompt");
    const myBalance         = document.getElementById("my-balance");
    const addrLegacy        = document.getElementById("addr-legacy");
    const addrNative        = document.getElementById("addr-native");
    const addrTaproot       = document.getElementById("addr-taproot");
    const formTransfer      = document.getElementById("transfer-form");
    const inputRecipient    = document.getElementById("recipient-addr");
    const inputAmount       = document.getElementById("amount");
    const inputFeeBtc       = document.getElementById("fee-btc");
    const btnMineBlock      = document.getElementById("btn-mine-block");
    const ledgerBody        = document.getElementById("ledger-body");
    const userTab           = document.getElementById("user-tab");
    const minerTab          = document.getElementById("miner-tab");
    const userControls      = document.getElementById("user-nav-controls");
    const toastEl           = document.getElementById("liveToast");
    const toastBody         = document.getElementById("toast-body");
    const toast             = new bootstrap.Toast(toastEl, { delay: 7000 });

    // =========================================================
    // TOAST
    // =========================================================
    function showToast(message, isSuccess = true) {
        toastBody.innerText = message;
        toastEl.classList.remove("text-bg-primary", "text-bg-danger", "text-bg-success");
        toastEl.classList.add(isSuccess ? "text-bg-success" : "text-bg-danger");
        toast.show();
    }

    // =========================================================
    // 9-STEP FLOW
    // =========================================================
    function setFlowStep(n, state) {
        const el = document.getElementById(`step-flow-${n}`);
        if (!el) return;
        el.classList.remove("done", "active");
        if (state) el.classList.add(state);
    }

    function updateFlowFromBalance(totalBalance) {
        const bal = parseFloat(totalBalance) || 0;
        // Bước 1 & 2: luôn "done" khi đã đăng nhập
        setFlowStep(1, "done");
        setFlowStep(2, "done");
        if (bal > 0) {
            setFlowStep(3, "done");   // đã nạp coin
            setFlowStep(4, "done");   // đã có UTXO
        } else {
            setFlowStep(3, "active"); // cần nạp coin
            setFlowStep(4, null);
        }
    }

    // Toggle collapse flow panel
    const btnToggleFlow = document.getElementById("btn-toggle-flow");
    const flowSteps     = document.getElementById("flow-steps");
    if (btnToggleFlow && flowSteps) {
        btnToggleFlow.addEventListener("click", () => {
            const hidden = flowSteps.style.display === "none";
            flowSteps.style.display = hidden ? "flex" : "none";
            btnToggleFlow.innerHTML = hidden
                ? '<i class="bi bi-chevron-up"></i>'
                : '<i class="bi bi-chevron-down"></i>';
        });
    }

    // =========================================================
    // COPY TO CLIPBOARD
    // =========================================================
    document.addEventListener("click", (e) => {
        const btn = e.target.closest(".btn-copy");
        if (!btn) return;
        const targetId = btn.dataset.target;
        const el = document.getElementById(targetId);
        if (!el) return;
        const text = el.dataset.addr || el.innerText.trim();
        if (!text || text === "Đang tải...") return;
        navigator.clipboard.writeText(text).then(() => {
            const icon = btn.querySelector("i");
            icon.className = "bi bi-clipboard-check";
            btn.classList.add("copied");
            setTimeout(() => {
                icon.className = "bi bi-clipboard";
                btn.classList.remove("copied");
            }, 1800);
        });
    });

    // =========================================================
    // SAVED WALLETS (localStorage)
    // =========================================================
    let savedWallets = JSON.parse(localStorage.getItem("saved_wallets") || "[]");
    savedWallets.forEach((wif, index) => {
        const option = document.createElement("option");
        option.value = wif;
        option.text = `Ví Tạo Ra #${index + 1} (${wif.substring(0, 6)}...)`;
        walletSelector.appendChild(option);
    });

    if (currentWif) {
        walletSelector.value = currentWif;
        login(currentWif);
    }

    // =========================================================
    // WALLET INFO & LEDGER
    // =========================================================
    async function fetchWalletInfo(append = false) {
        if (!currentWif || isFetching) return;
        isFetching = true;
        try {
            const res  = await fetch(`/api/wallet/info?wif=${currentWif}&page=${currentPage}&limit=${historyLimit}`);
            const data = await res.json();
            if (data.success) {
                const info = data.data;

                // Cập nhật số dư & địa chỉ
                myBalance.innerText = info.total_balance;

                const setAddr = (elemId, addr, bal, balElemId) => {
                    const el = document.getElementById(elemId);
                    el.innerText = addr;
                    el.dataset.addr = addr;
                    document.getElementById(balElemId).innerText = bal;
                };
                setAddr("addr-legacy",  info.addresses.legacy,        info.balances.legacy,        "bal-legacy");
                setAddr("addr-nested",  info.addresses.nested_segwit,  info.balances.nested_segwit, "bal-nested");
                setAddr("addr-native",  info.addresses.native_segwit,  info.balances.native_segwit, "bal-native");
                setAddr("addr-taproot", info.addresses.taproot,        info.balances.taproot,       "bal-taproot");

                // Cập nhật 9-step flow
                updateFlowFromBalance(info.total_balance);

                // Sổ cái
                renderLedger(data.history, append);

                // Phân trang
                const pagination = document.getElementById("ledger-pagination");
                pagination.style.display = (currentPage < data.total_pages) ? "block" : "none";

            } else {
                showToast(`❌ Lỗi: ${data.error}`, false);
            }
        } catch (err) {
            console.error("fetchWalletInfo error:", err);
            showToast("❌ Mất kết nối với máy chủ Flask", false);
        } finally {
            isFetching = false;
        }
    }

    // =========================================================
    // RENDER LEDGER — phân biệt gửi / nhận
    // =========================================================
    function renderLedger(history, append = false) {
        if (!history || history.length === 0) {
            if (!append) {
                ledgerBody.innerHTML = `
                    <tr><td colspan="7" class="text-center text-muted py-4">
                        Chưa có giao dịch nào
                    </td></tr>`;
            }
            return;
        }

        let html = append ? ledgerBody.innerHTML : "";

        history.forEach(tx => {
            const isSent    = (tx.sender_wif === currentWif);
            const direction = isSent
                ? '<span class="badge text-bg-danger"><i class="bi bi-arrow-up-circle"></i> Gửi đi</span>'
                : '<span class="badge text-bg-success"><i class="bi bi-arrow-down-circle"></i> Nhận về</span>';

            const amountClass = isSent ? "tx-sent" : "tx-received";
            const amountSign  = isSent ? "−" : "+";
            const amountFixed = parseFloat(tx.amount).toFixed(8);

            const statusBadge = tx.status === "Mempool"
                ? '<span class="badge text-bg-warning">Đang chờ</span>'
                : '<span class="badge text-bg-success">✅ Confirmed</span>';

            const addrDisplay = tx.recipient
                ? `<span title="${tx.recipient}">${tx.recipient.substring(0, 12)}…</span>`
                : "N/A";

            html += `
                <tr>
                    <td class="text-muted">${tx.time || "—"}</td>
                    <td>${direction}</td>
                    <td>${addrDisplay}</td>
                    <td class="${amountClass} fw-bold">${amountSign}${amountFixed}</td>
                    <td class="text-muted">${parseFloat(tx.fee).toFixed(8)}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <a href="javascript:void(0)"
                           onclick="viewTransactionDetails('${tx.txid}', ${parseFloat(tx.amount).toFixed(8)}, ${parseFloat(tx.fee).toFixed(8)}, '${isSent ? 'sent' : 'received'}')"
                           class="text-info text-decoration-none font-monospace"
                           title="${tx.txid}">${tx.txid.substring(0, 8)}…</a>
                    </td>
                </tr>`;
        });

        ledgerBody.innerHTML = html;

        // Expose globally for onclick in dynamic HTML
        window.viewTransactionDetails = async function(txid, amount = null, fee = null, direction = null) {
            const txModal = new bootstrap.Modal(document.getElementById("txModal"));
            const content = document.getElementById("tx-modal-content");
            content.innerHTML = '<div class="text-center"><span class="spinner-border text-info"></span> Đang tải...</div>';
            txModal.show();
            try {
                const res  = await fetch(`/api/transaction/${txid}`);
                const data = await res.json();
                if (data.success) {
                    const tx = data.data;

                    // ---- TÓM TẮT TÀI CHÍNH (nếu có dữ liệu từ sổ cái) ----
                    let html = '';
                    if (amount !== null && fee !== null) {
                        const total       = (parseFloat(amount) + parseFloat(fee)).toFixed(8);
                        const amtClass    = direction === 'sent' ? 'text-danger' : 'text-success';
                        const amtSign     = direction === 'sent' ? '−' : '+';
                        const dirLabel    = direction === 'sent' ? '💸 Chuyển đi' : '📥 Nhận về';
                        html += `
                        <div class="row g-2 mb-4">
                            <div class="col-4">
                                <div class="p-3 rounded text-center" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1)">
                                    <div class="text-muted small mb-1">${dirLabel}</div>
                                    <div class="fw-bold fs-5 ${amtClass}">${amtSign}${parseFloat(amount).toFixed(8)}</div>
                                    <div class="text-muted" style="font-size:0.75rem">BTC</div>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="p-3 rounded text-center" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1)">
                                    <div class="text-muted small mb-1">⛽ Phí thợ đào</div>
                                    <div class="fw-bold fs-5 text-warning">+${parseFloat(fee).toFixed(8)}</div>
                                    <div class="text-muted" style="font-size:0.75rem">BTC</div>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="p-3 rounded text-center" style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,107,107,0.3)">
                                    <div class="text-muted small mb-1">📊 Tổng trừ ví</div>
                                    <div class="fw-bold fs-5 text-light">${direction === 'sent' ? '−' : '+'}${total}</div>
                                    <div class="text-muted" style="font-size:0.75rem">BTC</div>
                                </div>
                            </div>
                        </div>
                        <hr style="border-color:rgba(255,255,255,0.1)" class="mb-3">`;
                    }

                    html += `<div class="mb-2 d-flex gap-3 flex-wrap">
                        <span><strong class="text-muted">TXID:</strong> <span class="text-info font-monospace" style="font-size:0.8rem">${tx.txid}</span></span>
                    </div>`;
                    html += `<div class="mb-3 text-muted small"><strong>Size:</strong> ${tx.size} bytes &nbsp;|&nbsp; <strong>Weight:</strong> ${tx.weight} &nbsp;|&nbsp; <strong>Inputs:</strong> ${tx.vin.length} &nbsp;|&nbsp; <strong>Outputs:</strong> ${tx.vout.length}</div>`;
                    html += `<h6>Inputs (${tx.vin.length}):</h6>`;
                    tx.vin.forEach(vin => {
                        if (vin.coinbase) {
                            html += `<div class="mb-2 p-2 border border-secondary rounded small">
                                🏅 Coinbase (Phần thưởng thợ đào)</div>`;
                        } else {
                            html += `<div class="mb-2 p-2 border border-secondary rounded small">
                                <div><strong>Txid:</strong> ${vin.txid}:${vin.vout}</div>
                                ${vin.txinwitness ? `<div><strong>Witness:</strong> Có (${vin.txinwitness.length} phần tử)</div>` : ""}
                            </div>`;
                        }
                    });
                    html += `<h6 class="mt-3">Outputs (${tx.vout.length}):</h6>`;
                    tx.vout.forEach(vout => {
                        if (vout.scriptPubKey.type === "nulldata") {
                            let msg = "";
                            try {
                                const hex = vout.scriptPubKey.asm.split(" ")[1] || "";
                                msg = decodeURIComponent("%" + hex.match(/.{1,2}/g).join("%"));
                            } catch (e) { msg = "Không thể giải mã"; }
                            html += `<div class="mb-2 p-2 border border-info rounded bg-info bg-opacity-10 small">
                                <div><strong class="text-info"><i class="bi bi-chat-left-text"></i> OP_RETURN:</strong></div>
                                <div class="fst-italic">"${msg}"</div></div>`;
                        } else {
                            const addr = vout.scriptPubKey.address || "N/A";
                            html += `<div class="mb-2 p-2 border border-secondary rounded small">
                                <div class="text-success fw-bold">${vout.value} BTC</div>
                                <div><strong>To:</strong> ${addr}</div>
                                <div><strong>Type:</strong> ${vout.scriptPubKey.type}</div></div>`;
                        }
                    });
                    content.innerHTML = html;
                } else {
                    content.innerHTML = `<div class="alert alert-danger">Lỗi: ${data.error}</div>`;
                }
            } catch (err) {
                content.innerHTML = `<div class="alert alert-danger">Lỗi kết nối mạng</div>`;
            }
        };
    }

    // =========================================================
    // LOGIN
    // =========================================================
    function login(wif) {
        currentWif = wif;
        localStorage.setItem("last_wif", currentWif);
        currentPage = 1;
        loginPrompt.style.display  = "none";
        mainDashboard.style.display = "block";
        fetchWalletInfo();
        if (fetchInterval) clearInterval(fetchInterval);
        // Auto-refresh mỗi 15s (scantxoutset chậm, tránh lag)
        fetchInterval = setInterval(() => {
            if (currentPage === 1) fetchWalletInfo();
        }, 15000);
    }

    // =========================================================
    // WALLET SELECTOR
    // =========================================================
    walletSelector.addEventListener("change", (e) => {
        if (!e.target.value) return;
        currentWif = e.target.value;
        localStorage.setItem("last_wif", currentWif);
        currentPage = 1;
        // Tự động chuyển sang Tab Ví người dùng
        const userTabEl = document.getElementById("user-tab");
        bootstrap.Tab.getOrCreateInstance(userTabEl).show();
        login(currentWif);
    });

    btnCustomWif.addEventListener("click", () => {
        const wif = prompt("Vui lòng nhập Private Key (WIF) của bạn:");
        if (wif && wif.trim()) {
            walletSelector.selectedIndex = 0;
            const userTabEl = document.getElementById("user-tab");
            bootstrap.Tab.getOrCreateInstance(userTabEl).show();
            login(wif.trim());
        }
    });

    document.getElementById("btn-load-more").addEventListener("click", () => {
        currentPage++;
        fetchWalletInfo(true);
    });

    // =========================================================
    // CREATE WALLET
    // =========================================================
    const btnCreateWallet = document.getElementById("btn-create-wallet");
    btnCreateWallet.addEventListener("click", async () => {
        try {
            btnCreateWallet.innerHTML = '<span class="spinner-border spinner-border-sm"></span>...';
            btnCreateWallet.disabled = true;
            const res  = await fetch("/api/wallet/new");
            const data = await res.json();
            if (data.success) {
                const wif = data.wif;
                savedWallets.push(wif);
                localStorage.setItem("saved_wallets", JSON.stringify(savedWallets));
                const option = document.createElement("option");
                option.value = wif;
                option.text  = `Ví Tạo Ra #${savedWallets.length} (${wif.substring(0, 6)}...)`;
                walletSelector.appendChild(option);
                prompt("🎉 Ví mới đã được tạo!\n\nHãy COPY lại WIF này:", wif);
                walletSelector.value = wif;
                login(wif);
                showToast("Ví mới đã được tạo và tự động đăng nhập!");
            } else {
                showToast("❌ Lỗi tạo ví: " + data.error, false);
            }
        } catch (e) {
            showToast("❌ Lỗi mạng", false);
        } finally {
            btnCreateWallet.innerHTML = '<i class="bi bi-plus-circle"></i> Tạo Ví';
            btnCreateWallet.disabled = false;
        }
    });

    // =========================================================
    // BUILD TRANSACTION (Bước 5-7)
    // =========================================================
    let pendingTxPayload = null;

    formTransfer.addEventListener("submit", async (e) => {
        e.preventDefault();
        const amount    = inputAmount.value;
        const recipient = inputRecipient.value.trim();
        const feeBtc    = inputFeeBtc.value;
        if (!amount || amount <= 0 || !recipient || !currentWif || !feeBtc) return;

        const btnBuild   = document.getElementById("btn-build-tx");
        const origText   = btnBuild.innerHTML;
        btnBuild.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang tạo mã Hex...';
        btnBuild.disabled  = true;

        // Step 5 → active
        setFlowStep(5, "active");
        setFlowStep(6, null);
        setFlowStep(7, null);

        try {
            const res = await fetch("/api/transaction/build", {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body:    JSON.stringify({
                    sender_wif:        currentWif,
                    recipient_address: recipient,
                    amount:            amount,
                    absolute_fee:      feeBtc,
                    op_return_msg:     document.getElementById("op-return-msg").value
                })
            });
            const data = await res.json();

            if (data.success) {
                pendingTxPayload = {
                    hex:               data.hex,
                    sender_wif:        currentWif,
                    recipient_address: recipient,
                    amount:            amount,
                    fee:               data.fee,
                    selected_utxos:    data.selected_utxos
                };

                // Render UTXO list
                const utxoList = document.getElementById("utxo-list");
                utxoList.innerHTML = "";
                data.selected_utxos.forEach(u => {
                    const isTaproot   = u.addr_type === "taproot";
                    const sigType     = isTaproot ? "SCHNORR" : "ECDSA";
                    const sigClass    = isTaproot ? "sig-schnorr" : "sig-ecdsa";
                    const addrTypeMap = {
                        legacy: "Legacy", native_segwit: "Native Segwit",
                        nested_segwit: "Nested Segwit", taproot: "Taproot"
                    };
                    const addrTypeName = addrTypeMap[u.addr_type] || u.addr_type;
                    utxoList.innerHTML += `
                        <div class="utxo-item fade-in">
                            <div>
                                <div class="text-light fw-bold">${u.amount} BTC</div>
                                <div class="text-muted" style="font-size:0.7rem">
                                    ${u.txid.substring(0, 8)}…:${u.vout}
                                </div>
                            </div>
                            <span class="utxo-signature ${sigClass}"
                                title="Nguồn: ví ${addrTypeName}">
                                <i class="bi bi-pen"></i> ${addrTypeName} — ${sigType}
                            </span>
                        </div>`;
                });

                document.getElementById("raw-hex-box").innerText = data.hex;
                document.getElementById("step2-panel").style.display = "block";

                // Step flow: 5 done, 6 done, 7 done (build & sign đã xong)
                setFlowStep(5, "done");
                setFlowStep(6, "done");
                setFlowStep(7, "done");
                setFlowStep(8, "active");

                showToast("✅ Đã tạo Raw TX Hex! Kiểm tra kỹ rồi phát sóng.");
            } else {
                showToast(`❌ Lỗi: ${data.error}`, false);
                setFlowStep(5, null);
            }
        } catch (err) {
            showToast("❌ Lỗi mạng khi gọi API", false);
            setFlowStep(5, null);
        } finally {
            btnBuild.innerHTML = origText;
            btnBuild.disabled  = false;
        }
    });

    document.getElementById("btn-cancel-tx").addEventListener("click", () => {
        document.getElementById("step2-panel").style.display = "none";
        pendingTxPayload = null;
        // Rollback flow
        setFlowStep(5, "done");
        setFlowStep(6, "done");
        setFlowStep(7, "done");
        setFlowStep(8, null);
    });

    // =========================================================
    // BROADCAST (Bước 8)
    // =========================================================
    document.getElementById("btn-broadcast-tx").addEventListener("click", async () => {
        if (!pendingTxPayload) return;
        const btnBroadcast = document.getElementById("btn-broadcast-tx");
        const origText     = btnBroadcast.innerHTML;
        btnBroadcast.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang phóng lên Mempool...';
        btnBroadcast.disabled  = true;

        try {
            const res  = await fetch("/api/transaction/broadcast", {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body:    JSON.stringify(pendingTxPayload)
            });
            const data = await res.json();

            if (data.success) {
                setFlowStep(8, "done");
                setFlowStep(9, "active");
                showToast(`✅ Phát sóng thành công!\nTXID: ${data.txid}`);
                inputAmount.value = "";
                inputRecipient.value = "";
                document.getElementById("op-return-msg").value = "";
                document.getElementById("step2-panel").style.display = "none";
                pendingTxPayload = null;
                fetchWalletInfo();
            } else {
                showToast(`❌ Lỗi Node: ${data.error}`, false);
            }
        } catch (err) {
            showToast("❌ Lỗi kết nối đến Node", false);
        } finally {
            btnBroadcast.innerHTML = origText;
            btnBroadcast.disabled  = false;
        }
    });

    // =========================================================
    // MINER DASHBOARD
    // =========================================================
    async function fetchMinerInfo() {
        try {
            const res  = await fetch("/api/miner/info");
            const data = await res.json();
            if (data.success) {
                document.getElementById("miner-balance").innerText = data.balance;
                const addrEl = document.getElementById("miner-address");
                addrEl.innerText   = data.address;
                addrEl.dataset.addr = data.address;
            }
        } catch (e) {
            console.error("fetchMinerInfo error:", e);
        }
    }

    async function fetchMempoolData() {
        try {
            const res  = await fetch("/api/miner/mempool");
            const data = await res.json();
            if (data.success) {
                document.getElementById("mempool-count").innerText = data.tx_count;
                document.getElementById("mempool-vsize").innerText = data.total_vsize;
                document.getElementById("mempool-fee").innerText   = data.total_fee.toFixed(8);

                const tbody = document.getElementById("mempool-body");
                if (data.txs.length === 0) {
                    tbody.innerHTML = `
                        <tr><td colspan="4" class="text-center text-muted py-4">
                            <i class="bi bi-wind fs-3 d-block mb-2"></i> Mempool đang trống
                        </td></tr>`;
                } else {
                    let html = "";
                    data.txs.forEach(tx => {
                        const date = new Date(tx.time * 1000);
                        html += `
                            <tr>
                                <td>${date.toLocaleTimeString()}</td>
                                <td>
                                    <a href="javascript:void(0)"
                                       onclick="viewTransactionDetails('${tx.txid}')"
                                       class="text-info text-decoration-none font-monospace">
                                        ${tx.txid.substring(0, 10)}…
                                    </a>
                                </td>
                                <td>${tx.vsize} vB</td>
                                <td class="text-end text-success fw-bold">+${tx.fee}</td>
                            </tr>`;
                    });
                    tbody.innerHTML = html;
                }
            }
        } catch (e) {
            console.error("fetchMempoolData error:", e);
        }
    }

    // =========================================================
    // TAB SWITCHING
    // =========================================================
    userTab.addEventListener("show.bs.tab", () => {
        userControls.style.display = "flex";
        if (mempoolInterval) { clearInterval(mempoolInterval); mempoolInterval = null; }
        if (!fetchInterval && currentWif) {
            currentPage = 1;
            fetchWalletInfo();
            fetchInterval = setInterval(() => {
                if (currentPage === 1) fetchWalletInfo();
            }, 15000);
        }
    });

    minerTab.addEventListener("show.bs.tab", () => {
        userControls.style.display = "none";
        if (fetchInterval) { clearInterval(fetchInterval); fetchInterval = null; }
        fetchMinerInfo();
        fetchMempoolData();
        mempoolInterval = setInterval(() => {
            fetchMinerInfo();
            fetchMempoolData();
        }, 10000);
    });

    // =========================================================
    // MINE BLOCK (Bước 9)
    // =========================================================
    btnMineBlock.addEventListener("click", async () => {
        const origText   = btnMineBlock.innerHTML;
        btnMineBlock.innerHTML = '<i class="bi bi-gear-wide-connected spin"></i> ĐANG TẠO BLOCK...';
        btnMineBlock.disabled  = true;

        try {
            const res  = await fetch("/api/mine", { method: "POST" });
            const data = await res.json();

            if (data.success) {
                setFlowStep(9, "done");
                showToast(
                    `⛏️ Block #${data.height} đã được khai thác!\n` +
                    `Đóng gói ${data.tx_count} giao dịch.\n` +
                    `Phần thưởng: ${data.reward} BTC`
                );
                fetchMinerInfo();
                fetchMempoolData();

                // Tự cập nhật sổ cái người dùng (trạng thái → Confirmed)
                if (currentWif) {
                    currentPage = 1;
                    setTimeout(() => fetchWalletInfo(), 500);
                }
            } else {
                showToast(`❌ Lỗi: ${data.error}`, false);
            }
        } catch (err) {
            showToast("❌ Lỗi mạng", false);
        } finally {
            btnMineBlock.innerHTML = origText;
            btnMineBlock.disabled  = false;
        }
    });

});
