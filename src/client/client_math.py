import os
import yaml

from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import AccountMeta, Transaction, TransactionInstruction
# from solana.rpc.types import TxOpts
from solana import system_program
from solana.rpc.commitment import Finalized
from client_util import create_keypair_from_file

# from base58 import b58encode
from solana.message import Message

from construct import Int32ul, Int64ul
from construct import Struct as cStruct

CONFIG_FILE_PATH = os.path.expanduser('~') + '/.config/solana/cli/config.yml'
PROGRAM_PATH = os.getcwd() + '/dist/program/'
ACCOUNT_SPACE_SIZE = 4
LAMPORTS_PER_SOL = 1000000000
SEED = 'test2'
CALC_INSTRUCTION_LAYOUT = cStruct(
        "operation" / Int32ul,
        "operating_value" / Int32ul,
        )


def connect() -> Client:
    ## Connection to cluster
    connection = Client("https://api.devnet.solana.com")  # http client
    if connection is not None:
        print("Connected to devnet :)")
    
    return connection

def get_local_account() -> Keypair:
    with open(CONFIG_FILE_PATH, 'r') as file:
        config_yml = yaml.safe_load(file)
    
    keypair_path = config_yml["keypair_path"]
    local_keypair = create_keypair_from_file(keypair_path)

    connection = connect()
    resp = connection.request_airdrop(local_keypair.public_key, LAMPORTS_PER_SOL)  # Airdrop 1 SOL 
    connection.confirm_transaction(resp.value)
    print("Loaded Accounts.")
    print(f"Local account address is: {local_keypair.public_key}")
    return local_keypair

def get_program() -> PublicKey:
    program_keypair = create_keypair_from_file(PROGRAM_PATH + 'calculator-keypair.json')
    program_id = program_keypair.public_key

    print(f"programme id is {program_id.to_base58()}")
    return program_id


def configute_client_account() -> PublicKey:
    local_keypair = get_local_account()
    program_id = get_program()
    client_pubkey = PublicKey.create_with_seed(local_keypair.public_key, SEED, program_id)

    print(f"The generated address is {client_pubkey.to_base58()}")

    # Make sure it doen't exist already
    connection = connect()
    client_account = connection.get_account_info(client_pubkey)
    # print(client_account)
    if client_account.value is None:

        print("Looks like that account doesn't exist. Let's create it")
        params = system_program.CreateAccountWithSeedParams(local_keypair.public_key, client_pubkey, local_keypair.public_key, SEED, LAMPORTS_PER_SOL, ACCOUNT_SPACE_SIZE, program_id)
        transaction = Transaction().add(system_program.create_account_with_seed(params))
        connection.send_transaction(transaction, local_keypair)
        print("Client account created successfully")

    else:
        print("Looks like that account already exists. We can just use it.")

    return client_pubkey
        


def ping_program(operation : int, operating_value : int):

    print(f"Pinging program...")
    
    client_pubkey = configute_client_account()
    program_id = get_program()
    local_keypair = get_local_account()
    connection = connect()

    instruction_data = CALC_INSTRUCTION_LAYOUT.build(
            dict(operation = operation, operating_value = operating_value)
            )

    print("Printing instruction_data bytes--------")
    print(instruction_data)

    txn = Transaction(fee_payer= local_keypair.public_key)
    txn.add(TransactionInstruction(
        keys =[AccountMeta(pubkey = client_pubkey, is_signer = False, is_writable = True)],
        program_id= program_id,
        data = instruction_data
        ))

    txn.sign(local_keypair)
    # resp = connection.send_transaction(txn, local_keypair, opts=TxOpts(skip_preflight=True, skip_confirmation=False))
    resp = connection.send_transaction(txn, local_keypair)
    connection.confirm_transaction(resp.value, commitment = Finalized)






    print("Pinged!")


if __name__ == "__main__":
    ping_program(1, 4) # Add 4
    ping_program(2, 1) # Subtract 4
    ping_program(3, 2) # Multiply by 2
