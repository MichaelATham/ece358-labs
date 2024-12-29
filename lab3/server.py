import socket
import struct

# Define authoritative DNS records based on table in lab manual
dnsRecords = {
    "google.com": {
        "ips": ["192.165.1.1", "192.165.1.10"],
        "type": "A",
        "class": "IN",
        "ttl": 260
    },
    "youtube.com": {
        "ips": ["192.165.1.2"],
        "type": "A",
        "class": "IN",
        "ttl": 160
    },
    "uwaterloo.ca": {
        "ips": ["192.165.1.3"],
        "type": "A",
        "class": "IN",
        "ttl": 160
    },
    "wikipedia.org": {
        "ips": ["192.165.1.4"],
        "type": "A",
        "class": "IN",
        "ttl": 160
    },
    "amazon.ca": {
        "ips": ["192.165.1.5"],
        "type": "A",
        "class": "IN",
        "ttl": 160
    }
}

def createResponse(query, domain):
    transactionId = query[:2]      # Get Transaction ID from query
    flags = b'\x84\x00'             # Standard response with authoritative answer
    qdcount = struct.pack('!H', 1)  # Packing value into bytes
    ancount = struct.pack('!H', len(dnsRecords.get(domain, {}).get("ips", [])))  # Number of answers
    nscount = struct.pack('!H', 0)  # Constant for this lab
    arcount = struct.pack('!H', 0)  # Constant for this lab

    # Start response with the header
    response = transactionId + flags + qdcount + ancount + nscount + arcount
    question = query[12:]  # Copy question section from query
    response += question

    # Answer section
    record = dnsRecords.get(domain, {})
    ttl = record.get("ttl", 0)
        
    for ip in record.get("ips", []):
        response += struct.pack('!H', 0xC00C)       # Pointer to the name in question section
        response += struct.pack('!HHI', 1, 1, ttl)  # Type A, Class IN, TTL. Note CLASS and Type are constant despite being present in the DNS records
        response += struct.pack('!H', 4)            # RDLENGTH of IPv4 address
        response += socket.inet_aton(ip)            # IP address in binary format

    return response

def parse(query_body):
    domainParts = []
    i = 0
    while query_body[i] != 0:
        length = query_body[i]
        i += 1
        domainParts.append(query_body[i:i+length].decode())
        i += length
    return ".".join(domainParts).lower()

def startDnsServer():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # Initialize UDP socket
    port = 10053
    serverSocket.bind(('127.0.0.1', port))                             # Bind port number to socket
    print("DNS server has been started on port " + str(port) + " (http://127.0.0.1:" + str(port) + ").")

    while True:
        query, clientAddress = serverSocket.recvfrom(512)
        print("Request:", query.hex(' '))
        
        domain = parse(query[12:])
        response = createResponse(query, domain)
        
        serverSocket.sendto(response, clientAddress)
        print("Response:", response.hex(' '))

def main():
    startDnsServer()

main()