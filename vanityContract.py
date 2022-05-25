# This script generates private key for a deployer address to deploy contract with vanity address
# Contract addresses are deterministic, calculated from the deployer address and the transaction nonce
# Hence we can bruteforce the private key, that would generate the contract address with the desired prefix
# Implementation is naive and slow, using only single thread of the CPU
# 
# To deploy the contract with the found vanity address, use the found private key and make sure the nonce of the transaction is same as what is defined in the 'nonce' variable, 
# Default nonce is 5
#
# Result is case sensitive regarding the address checksum
#
# Example:
# prefix 0xABC
#
# private_key: 83beac9399513ad49c4253affd71b6a4b8dd9b69c9d4b21d126d8ad93386a707_don't use this key to store your funds, you will lose them
# eth addr: 0xda74cb644eca35c56ae5f5d315bdc642e8b37716
# nonce: 5
# eth addr: 0x0xABCb4D8A465Cd7eA98e4b3711060DAD74AA80FC1
# 
# result transaction:
# https://rinkeby.etherscan.io/tx/0xefc1122febf351b694ef9f66bf197573ebcb4a02c23cd08bff0f69778a1ec2b9
# deployed contract
# https://rinkeby.etherscan.io/address/0xabcb4d8a465cd7ea98e4b3711060dad74aa80fc1
# checksummed: 0xABCb4D8A465Cd7eA98e4b3711060DAD74AA80FC1

vanity_prefix = '0xABC'
nonce = 5

import rlp
#pip install pysha3
from sha3 import keccak_256
from secrets import token_bytes
#pip install coincurve
from coincurve import PublicKey
from web3 import Web3   
i = 0

prefixLength  = len(vanity_prefix)
while True:
    private_key = keccak_256(token_bytes(32)).digest()
    public_key = PublicKey.from_valid_secret(private_key).format(compressed=False)[1:]
    addr = keccak_256(public_key).digest()[-20:]
    i = i + 1
    sender = bytes.fromhex(addr.hex())
    contract_address = keccak_256(rlp.encode([sender, nonce])).hexdigest()[-40:]
    contract_address = Web3.toChecksumAddress(contract_address)
    contract_prefix = (contract_address[0:prefixLength])

    if (contract_prefix == vanity_prefix) :
        print('private_key:', private_key.hex())
        print('eth addr: 0x' + addr.hex())
        print('nonce: ' + str(nonce))
        print('eth addr: 0x' + contract_address)       
        break 