import asyncio
import json
import requests
from web3 import Web3
from eth_account import Account
import time
import os

# Pharos Testnet configuration
RPC_URL = "https://testnet.dplabs-internal.com"
CHAIN_ID = 688688
KYC_API_URL = "https://www.spout.finance/api/kyc-signature"

# Contract addresses
IDENTITY_FACTORY_CONTRACT = "0x18cB5F2774a80121d1067007933285B32516226a"
GATEWAY_CONTRACT = "0x126F0c11F3e5EafE37AB143D4AA688429ef7DCB3"
ORDERS_CONTRACT = "0x81b33972f8bdf14fD7968aC99CAc59BcaB7f4E9A"
USDC_CONTRACT = "0x72df0bcd7276f2dFbAc900D1CE63c272C4BCcCED"
RWA_TOKEN_CONTRACT = "0x54b753555853ce22f66Ac8CB8e324EB607C4e4eE"

# ABIs
IDENTITY_FACTORY_ABI = [
    {"inputs": [{"internalType": "address", "name": "_wallet", "type": "address"}, {"internalType": "string", "name": "_salt", "type": "string"}], "name": "createIdentity", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "_wallet", "type": "address"}], "name": "getIdentity", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
]

IDENTITY_ABI = [
    {"inputs": [{"internalType": "uint256", "name": "_topic", "type": "uint256"}, {"internalType": "uint256", "name": "_scheme", "type": "uint256"}, {"internalType": "address", "name": "_issuer", "type": "address"}, {"internalType": "bytes", "name": "_signature", "type": "bytes"}, {"internalType": "bytes", "name": "_data", "type": "bytes"}, {"internalType": "string", "name": "_uri", "type": "string"}], "name": "addClaim", "outputs": [{"internalType": "bytes32", "name": "claimRequestId", "type": "bytes32"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "_topic", "type": "uint256"}], "name": "getClaimIdsByTopic", "outputs": [{"internalType": "bytes32[]", "name": "claimIds", "type": "bytes32[]"}], "stateMutability": "view", "type": "function"}
]

USDC_ABI = [
    {"inputs": [{"internalType": "address", "name": "_spender", "type": "address"}, {"internalType": "uint256", "name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "balance", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}
]

RWA_TOKEN_ABI = [
    {"inputs": [{"internalType": "address", "name": "_spender", "type": "address"}, {"internalType": "uint256", "name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "balance", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}
]

ORDERS_ABI = [
    {"inputs": [{"internalType": "uint256", "name": "adfsFeedId", "type": "uint256"}, {"internalType": "string", "name": "ticker", "type": "string"}, {"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "usdcAmount", "type": "uint256"}], "name": "buyAsset", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "feedId", "type": "uint256"}, {"internalType": "string", "name": "ticker", "type": "string"}, {"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "tokenAmount", "type": "uint256"}], "name": "sellAsset", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "feedId", "type": "uint256"}], "name": "getAssetPrice", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

def load_private_keys():
    try:
        with open("accounts.txt", "r") as f:
            lines = f.readlines()
        private_keys = [line.strip() for line in lines if line.strip()]
        return private_keys
    except FileNotFoundError:
        print("❌ accounts.txt file not found!")
        return []

def get_web3():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise Exception("Cannot connect to Pharos testnet")
    return w3

def get_kyc_signature(user_address, onchain_id):
    payload = {
        "userAddress": user_address,
        "onchainIDAddress": onchain_id,
        "claimData": "KYC passed",
        "topic": 1,
        "countryCode": 91
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.post(KYC_API_URL, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ KYC API error: {response.status_code}")
            # Return fallback data
            return {
                "signature": {
                    "r": "0xb2e2622d765ed8c5ba78ffa490cecd95693571031b3954ca429925e69ed15f57",
                    "s": "0x614a040deef613d026382a9f745ff13963a75ff8a6f4032b177350a25364f8c4",
                    "v": 28
                },
                "issuerAddress": "0x92b9baA72387Fb845D8Fe88d2a14113F9cb2C4E7",
                "dataHash": "0x7de3cf25b2741629c9158f89f92258972961d4357b9f027487765f655caec367",
                "topic": 1
            }
    except Exception as e:
        print(f"⚠️ Using fallback KYC data: {e}")
        return {
            "signature": {
                "r": "0xb2e2622d765ed8c5ba78ffa490cecd95693571031b3954ca429925e69ed15f57",
                "s": "0x614a040deef613d026382a9f745ff13963a75ff8a6f4032b177350a25364f8c4",
                "v": 28
            },
            "issuerAddress": "0x92b9baA72387Fb845D8Fe88d2a14113F9cb2C4E7",
            "dataHash": "0x7de3cf25b2741629c9158f89f92258972961d4357b9f027487765f655caec367",
            "topic": 1
        }

async def create_identity(w3, account, private_key):
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.to_wei('1.25', 'gwei')
        
        salt = f"wallet_{account.address.lower()}_{int(time.time())}"
        
        contract = w3.eth.contract(address=w3.to_checksum_address(IDENTITY_FACTORY_CONTRACT), abi=IDENTITY_FACTORY_ABI)
        
        tx = contract.functions.createIdentity(account.address, salt).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 1000000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'from': account.address,
            'value': 0
        })

        print(f"🔐 Creating identity for: {account.address}")
        print(f"   Salt: {salt}")
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"   Transaction hash: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt.status == 1 or receipt.logs:
            print(f"✅ Identity created successfully!")
            return receipt
        else:
            print(f"❌ Identity creation failed")
            return None
    except Exception as e:
        print(f"❌ Error creating identity: {e}")
        return None

def get_onchain_id(w3, wallet_address):
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(IDENTITY_FACTORY_CONTRACT), abi=IDENTITY_FACTORY_ABI)
        result = contract.functions.getIdentity(wallet_address).call()
        if result and result != "0x0000000000000000000000000000000000000000":
            return w3.to_checksum_address(result)
        return None
    except Exception as e:
        print(f"❌ Error getting onchain ID: {e}")
        return None

async def add_claim(w3, account, private_key, onchain_id, kyc_response):
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.to_wei('1.25', 'gwei')

        # Reconstruct signature
        signature_r = kyc_response['signature']['r']
        signature_s = kyc_response['signature']['s']
        signature_v = kyc_response['signature']['v']
        
        r_hex = signature_r[2:] if signature_r.startswith('0x') else signature_r
        s_hex = signature_s[2:] if signature_s.startswith('0x') else signature_s
        
        r_padded = r_hex.zfill(64)
        s_padded = s_hex.zfill(64)
        
        full_signature = bytes.fromhex(r_padded + s_padded + hex(signature_v)[2:].zfill(2))
        
        issuer = kyc_response['issuerAddress']
        data_hash = kyc_response['dataHash']
        data_bytes = bytes.fromhex(data_hash[2:] if data_hash.startswith('0x') else data_hash)
        
        print(f"🔐 Adding KYC claim to identity: {onchain_id}")
        print(f"   Issuer: {issuer}")
        print(f"   Topic: {kyc_response['topic']}")
        
        contract = w3.eth.contract(address=onchain_id, abi=IDENTITY_ABI)
        
        tx = contract.functions.addClaim(
            kyc_response['topic'],
            1,
            issuer,
            full_signature,
            data_bytes,
            ""
        ).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 800000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'from': account.address,
            'value': 0
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"   Transaction hash: {tx_hash.hex()}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt.status == 1 or receipt.logs:
            print(f"✅ KYC claim added successfully!")
            return receipt
        else:
            print(f"❌ KYC claim addition failed")
            return None
    except Exception as e:
        print(f"❌ Error adding claim: {e}")
        return None

async def run_kyc_process():
    print("\n" + "="*60)
    print("🔐 KYC PROCESS - IDENTITY CREATION & VERIFICATION")
    print("="*60)
    
    w3 = get_web3()
    private_keys = load_private_keys()
    
    if not private_keys:
        print("❌ No private keys found!")
        return
    
    for i, private_key in enumerate(private_keys):
        account = Account.from_key(private_key)
        print(f"\n📱 Processing Account {i+1}/{len(private_keys)}: {account.address}")
        
        # Check balance
        balance = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"   Balance: {balance_eth} PHRS")
        
        if balance == 0:
            print("   ❌ No balance, skipping...")
            continue
        
        # Check existing identity
        existing_id = get_onchain_id(w3, account.address)
        if existing_id:
            print(f"   ✅ Identity exists: {existing_id}")
            onchain_id = existing_id
        else:
            print("   🔐 Creating new identity...")
            receipt = await create_identity(w3, account, private_key)
            if not receipt:
                continue
            
            time.sleep(3)
            onchain_id = get_onchain_id(w3, account.address)
            if not onchain_id:
                print("   ❌ Identity creation failed")
                continue
        
        # Get KYC signature
        print("   🔐 Getting KYC signature...")
        kyc_response = get_kyc_signature(account.address, onchain_id)
        
        # Check existing claims
        try:
            contract = w3.eth.contract(address=onchain_id, abi=IDENTITY_ABI)
            existing_claims = contract.functions.getClaimIdsByTopic(kyc_response['topic']).call()
            if existing_claims:
                print("   ✅ KYC claim already exists")
                continue
        except:
            pass
        
        # Add claim
        print("   🔐 Adding KYC claim...")
        await add_claim(w3, account, private_key, onchain_id, kyc_response)
        
        time.sleep(5)
    
    print("\n🎉 KYC process completed!")

async def buy_tokens():
    print("\n" + "="*60)
    print("💰 BUY TOKENS - USDC TO RWA TOKEN")
    print("="*60)
    
    w3 = get_web3()
    private_keys = load_private_keys()
    
    if not private_keys:
        print("❌ No private keys found!")
        return
    
    # Get user input for transaction parameters
    try:
        num_transactions = int(input("Enter number of transactions to perform: "))
        if num_transactions <= 0:
            print("❌ Invalid number of transactions!")
            return
        
        min_usdc = float(input("Enter minimum USDC amount: "))
        max_usdc = float(input("Enter maximum USDC amount: "))
        if min_usdc <= 0 or max_usdc <= 0 or min_usdc > max_usdc:
            print("❌ Invalid amount range!")
            return
        
        min_delay = int(input("Enter minimum delay between transactions (seconds): "))
        max_delay = int(input("Enter maximum delay between transactions (seconds): "))
        if min_delay < 0 or max_delay < 0 or min_delay > max_delay:
            print("❌ Invalid delay range!")
            return
        
    except ValueError:
        print("❌ Invalid input!")
        return
    
    print(f"\n💰 Will perform {num_transactions} transactions")
    print(f"   Amount range: {min_usdc} - {max_usdc} USDC")
    print(f"   Delay range: {min_delay} - {max_delay} seconds")
    
    # Confirm before proceeding
    confirm = input("\nProceed with these settings? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Transaction cancelled!")
        return
    
    import random
    
    for transaction_num in range(1, num_transactions + 1):
        print(f"\n" + "="*60)
        print(f"🔄 TRANSACTION {transaction_num}/{num_transactions}")
        print("="*60)
        
        # Generate random amount and delay
        random_usdc = round(random.uniform(min_usdc, max_usdc), 2)
        random_delay = random.randint(min_delay, max_delay)
        
        print(f"💰 Random amount: {random_usdc} USDC")
        print(f"⏳ Next delay: {random_delay} seconds")
        
        for i, private_key in enumerate(private_keys):
            account = Account.from_key(private_key)
            print(f"\n📱 Processing Account {i+1}/{len(private_keys)}: {account.address}")
            
            try:
                # Check USDC balance
                usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=USDC_ABI)
                usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
                usdc_decimals = usdc_contract.functions.decimals().call()
                usdc_balance_formatted = usdc_balance / (10 ** usdc_decimals)
                
                print(f"   USDC Balance: {usdc_balance_formatted:.2f} USDC")
                
                if usdc_balance_formatted < random_usdc:
                    print(f"   ❌ Insufficient USDC balance")
                    continue
                
                # Check if identity exists
                existing_id = get_onchain_id(w3, account.address)
                if not existing_id:
                    print(f"   ❌ No identity found - complete KYC first")
                    continue
                
                # Approve USDC spending
                usdc_amount_wei = int(random_usdc * (10 ** usdc_decimals))
                orders_contract = w3.eth.contract(address=w3.to_checksum_address(ORDERS_CONTRACT), abi=ORDERS_ABI)
                
                print(f"   🔐 Approving USDC spending...")
                
                approve_tx = usdc_contract.functions.approve(
                    w3.to_checksum_address(ORDERS_CONTRACT),
                    usdc_amount_wei
                ).build_transaction({
                    'chainId': CHAIN_ID,
                    'gas': 100000,
                    'gasPrice': w3.to_wei('1.25', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'from': account.address,
                    'value': 0
                })
                
                signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
                approve_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
                print(f"   Approval hash: {approve_hash.hex()}")
                
                w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                print(f"   ✅ USDC approved")
                
                # Buy tokens
                print(f"   🚀 Buying RWA tokens...")
                
                buy_tx = orders_contract.functions.buyAsset(
                    2000002,  # feed ID
                    "LQD",    # ticker
                    w3.to_checksum_address(RWA_TOKEN_CONTRACT),
                    usdc_amount_wei
                ).build_transaction({
                    'chainId': CHAIN_ID,
                    'gas': 400000,
                    'gasPrice': w3.to_wei('1.25', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'from': account.address,
                    'value': 0
                })
                
                signed_buy_tx = w3.eth.account.sign_transaction(buy_tx, private_key)
                buy_hash = w3.eth.send_raw_transaction(signed_buy_tx.raw_transaction)
                print(f"   Buy hash: {buy_hash.hex()}")
                
                receipt = w3.eth.wait_for_transaction_receipt(buy_hash, timeout=60)
                
                if receipt.status == 1:
                    print(f"   ✅ Tokens bought successfully!")
                else:
                    print(f"   ❌ Buy transaction failed")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            time.sleep(3)
        
        # Delay before next transaction (except for the last one)
        if transaction_num < num_transactions:
            print(f"\n⏳ Waiting {random_delay} seconds before next transaction...")
            time.sleep(random_delay)
    
    print("\n🎉 All buy transactions completed!")

async def sell_tokens():
    print("\n" + "="*60)
    print("💸 SELL TOKENS - RWA TOKEN TO USDC")
    print("="*60)
    
    w3 = get_web3()
    private_keys = load_private_keys()
    
    if not private_keys:
        print("❌ No private keys found!")
        return
    
    # Get user input for transaction parameters
    try:
        num_transactions = int(input("Enter number of transactions to perform: "))
        if num_transactions <= 0:
            print("❌ Invalid number of transactions!")
            return
        
        min_tokens = float(input("Enter minimum RWA token amount: "))
        max_tokens = float(input("Enter maximum RWA token amount: "))
        if min_tokens <= 0 or max_tokens <= 0 or min_tokens > max_tokens:
            print("❌ Invalid amount range!")
            return
        
        min_delay = int(input("Enter minimum delay between transactions (seconds): "))
        max_delay = int(input("Enter maximum delay between transactions (seconds): "))
        if min_delay < 0 or max_delay < 0 or min_delay > max_delay:
            print("❌ Invalid delay range!")
            return
        
    except ValueError:
        print("❌ Invalid input!")
        return
    
    print(f"\n💸 Will perform {num_transactions} transactions")
    print(f"   Amount range: {min_tokens} - {max_tokens} LQD")
    print(f"   Delay range: {min_delay} - {max_delay} seconds")
    
    # Confirm before proceeding
    confirm = input("\nProceed with these settings? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Transaction cancelled!")
        return
    
    import random
    
    for transaction_num in range(1, num_transactions + 1):
        print(f"\n" + "="*60)
        print(f"🔄 TRANSACTION {transaction_num}/{num_transactions}")
        print("="*60)
        
        # Generate random amount and delay
        random_tokens = round(random.uniform(min_tokens, max_tokens), 4)
        random_delay = random.randint(min_delay, max_delay)
        
        print(f"💸 Random amount: {random_tokens} LQD")
        print(f"⏳ Next delay: {random_delay} seconds")
        
        for i, private_key in enumerate(private_keys):
            account = Account.from_key(private_key)
            print(f"\n📱 Processing Account {i+1}/{len(private_keys)}: {account.address}")
            
            try:
                # Check RWA token balance
                rwa_contract = w3.eth.contract(address=w3.to_checksum_address(RWA_TOKEN_CONTRACT), abi=RWA_TOKEN_ABI)
                token_balance = rwa_contract.functions.balanceOf(account.address).call()
                token_decimals = rwa_contract.functions.decimals().call()
                token_balance_formatted = token_balance / (10 ** token_decimals)
                
                print(f"   RWA Token Balance: {token_balance_formatted:.4f} LQD")
                
                if token_balance_formatted < random_tokens:
                    print(f"   ❌ Insufficient token balance")
                    continue
                
                # Check if identity exists
                existing_id = get_onchain_id(w3, account.address)
                if not existing_id:
                    print(f"   ❌ No identity found - complete KYC first")
                    continue
                
                # Approve token spending
                token_amount_wei = int(random_tokens * (10 ** token_decimals))
                orders_contract = w3.eth.contract(address=w3.to_checksum_address(ORDERS_CONTRACT), abi=ORDERS_ABI)
                
                print(f"   🔐 Approving token spending...")
                
                approve_tx = rwa_contract.functions.approve(
                    w3.to_checksum_address(ORDERS_CONTRACT),
                    token_amount_wei
                ).build_transaction({
                    'chainId': CHAIN_ID,
                    'gas': 100000,
                    'gasPrice': w3.to_wei('1.25', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'from': account.address,
                    'value': 0
                })
                
                signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
                approve_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
                print(f"   Approval hash: {approve_hash.hex()}")
                
                w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
                print(f"   ✅ Tokens approved")
                
                # Sell tokens
                print(f"   🚀 Selling RWA tokens...")
                
                sell_tx = orders_contract.functions.sellAsset(
                    2000002,  # feed ID
                    "LQD",    # ticker
                    w3.to_checksum_address(RWA_TOKEN_CONTRACT),
                    token_amount_wei
                ).build_transaction({
                    'chainId': CHAIN_ID,
                    'gas': 400000,
                    'gasPrice': w3.to_wei('1.25', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'from': account.address,
                    'value': 0
                })
                
                signed_sell_tx = w3.eth.account.sign_transaction(sell_tx, private_key)
                sell_hash = w3.eth.send_raw_transaction(signed_sell_tx.raw_transaction)
                print(f"   Sell hash: {sell_hash.hex()}")
                
                receipt = w3.eth.wait_for_transaction_receipt(sell_hash, timeout=60)
                
                if receipt.status == 1:
                    print(f"   ✅ Tokens sold successfully!")
                else:
                    print(f"   ❌ Sell transaction failed")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            time.sleep(3)
        
        # Delay before next transaction (except for the last one)
        if transaction_num < num_transactions:
            print(f"\n⏳ Waiting {random_delay} seconds before next transaction...")
            time.sleep(random_delay)
    
    print("\n🎉 All sell transactions completed!")

def show_menu():
    print("\n" + "="*60)
    print("🚀 SPOUT FINANCE BOT - MAIN MENU")
    print("="*60)
    print("1. 🔐 KYC Process (Create Identity & Add Claims)")
    print("2. 💰 Buy RWA Tokens (USDC → RWA)")
    print("3. 💸 Sell RWA Tokens (RWA → USDC)")
    print("4. 📊 Check Balances")
    print("5. 🔍 Check Identity Status")
    print("6. ❌ Exit")
    print("="*60)

async def check_balances():
    print("\n" + "="*60)
    print("📊 ACCOUNT BALANCES")
    print("="*60)
    
    w3 = get_web3()
    private_keys = load_private_keys()
    
    if not private_keys:
        print("❌ No private keys found!")
        return
    
    for i, private_key in enumerate(private_keys):
        account = Account.from_key(private_key)
        print(f"\n📱 Account {i+1}/{len(private_keys)}: {account.address}")
        
        try:
            # ETH balance
            eth_balance = w3.eth.get_balance(account.address)
            eth_balance_formatted = w3.from_wei(eth_balance, 'ether')
            print(f"   PHRS: {eth_balance_formatted:.6f} PHRS")
            
            # USDC balance
            usdc_contract = w3.eth.contract(address=w3.to_checksum_address(USDC_CONTRACT), abi=USDC_ABI)
            usdc_balance = usdc_contract.functions.balanceOf(account.address).call()
            usdc_decimals = usdc_contract.functions.decimals().call()
            usdc_balance_formatted = usdc_balance / (10 ** usdc_decimals)
            print(f"   USDC: {usdc_balance_formatted:.2f} USDC")
            
            # RWA token balance
            rwa_contract = w3.eth.contract(address=w3.to_checksum_address(RWA_TOKEN_CONTRACT), abi=RWA_TOKEN_ABI)
            token_balance = rwa_contract.functions.balanceOf(account.address).call()
            token_decimals = rwa_contract.functions.decimals().call()
            token_balance_formatted = token_balance / (10 ** token_decimals)
            print(f"   RWA: {token_balance_formatted:.4f} LQD")
            
            # Identity status
            existing_id = get_onchain_id(w3, account.address)
            if existing_id:
                print(f"   🔐 Identity: {existing_id}")
            else:
                print(f"   ❌ No Identity")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def check_identity_status():
    print("\n" + "="*60)
    print("🔍 IDENTITY STATUS CHECK")
    print("="*60)
    
    w3 = get_web3()
    private_keys = load_private_keys()
    
    if not private_keys:
        print("❌ No private keys found!")
        return
    
    for i, private_key in enumerate(private_keys):
        account = Account.from_key(private_key)
        print(f"\n📱 Account {i+1}/{len(private_keys)}: {account.address}")
        
        try:
            # Check identity
            existing_id = get_onchain_id(w3, account.address)
            if existing_id:
                print(f"   ✅ Identity: {existing_id}")
                
                # Check KYC claims
                try:
                    contract = w3.eth.contract(address=existing_id, abi=IDENTITY_ABI)
                    existing_claims = contract.functions.getClaimIdsByTopic(1).call()
                    if existing_claims:
                        print(f"   ✅ KYC Claim: {existing_claims[0].hex()}")
                    else:
                        print(f"   ❌ No KYC Claim")
                except:
                    print(f"   ❌ Error checking claims")
            else:
                print(f"   ❌ No Identity")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                await run_kyc_process()
            elif choice == "2":
                await buy_tokens()
            elif choice == "3":
                await sell_tokens()
            elif choice == "4":
                await check_balances()
            elif choice == "5":
                await check_identity_status()
            elif choice == "6":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid option! Please select 1-6.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    asyncio.run(main())
