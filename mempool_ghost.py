#!/usr/bin/env python3
"""
MempoolGhost — мониторинг больших незавершённых транзакций в Ethereum txpool.
"""

import os
import time
from web3 import Web3

def fetch_pending_txs(w3):
    try:
        content = w3.manager.request_blocking("txpool_content", [])
        return content.get('pending', {})
    except Exception as e:
        print(f"[Error] не удалось получить txpool: {e}")
        return {}

def filter_large_txs(pending, threshold_wei):
    large = []
    for sender, nonces in pending.items():
        for nonce, txdata in nonces.items():
            # в разных клиентах структура может отличаться
            txs = txdata if isinstance(txdata, list) else [txdata]
            for tx in txs:
                value = int(tx.get('value', 0))
                if value > threshold_wei:
                    large.append(tx)
    return large

def main():
    rpc_url = os.getenv("ETH_RPC_URL")
    if not rpc_url:
        print("Установите ETH_RPC_URL в окружении — адрес вашего Ethereum RPC.")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("Ошибка: не удалось подключиться к RPC‑узлу.")
        return

    threshold_eth = float(os.getenv("THRESHOLD_ETH", "100"))
    threshold_wei = w3.to_wei(threshold_eth, 'ether')
    print(f"Запуск мониторинга txpool: фильтрация транзакций > {threshold_eth} ETH")

    try:
        while True:
            pending = fetch_pending_txs(w3)
            large = filter_large_txs(pending, threshold_wei)
            if large:
                print(f"\nНайдено {len(large)} «крупных» транзакций:")
                for tx in large:
                    h = tx.get('hash') or tx.get('transactionHash')
                    frm = tx.get('from')
                    to = tx.get('to')
                    val = w3.from_wei(int(tx.get('value', 0)), 'ether')
                    print(f"  • Tx {h} | от {frm} → {to} | {val} ETH")
            else:
                print(".", end="", flush=True)
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nВыход.")

if __name__ == "__main__":
    main()
