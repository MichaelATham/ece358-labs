import socket
import struct
import random

def constructQuery(domainName):
    # Generate a random transaction ID in the range 0 to 65535
    transactionId = struct.pack('!H', random.randint(0, 65535))  # Pack the random number into 2 bytes
    
    flags = b'\x04\x00'             # Standard query as specified in lab3 manual
    qdcount = struct.pack('!H', 1)  # Pack the QDCOUNT parameter
    ancount = nscount = arcount = struct.pack('!H', 0) 

    query = transactionId + flags + qdcount + ancount + nscount + arcount  # Construct the query

    for part in domainName.split('.'):
        query += struct.pack('!B', len(part)) + part.encode()
    query += b'\x00'  # End of QNAME
    query += struct.pack('!HH', 1, 1)  # QTYPE A, QCLASS IN

    return query

def parse_response(response):
    # Define mappings for Type and Class
    typeMapping = {1: "A"}
    classMapping = {1: "IN"}

    # DNS Header is 12 bytes, and Question section ends with the first null byte + 4 bytes for QTYPE & QCLASS
    headerSize = 12
    questionEnd = response[headerSize:].find(b'\x00') + 1
    questionSize = questionEnd + 4  # +4 for QTYPE and QCLASS that follows QNAME
    answerStart = headerSize + questionSize

    # Extract answer count (ancount) from the response header
    ancount = struct.unpack('!H', response[6:8])[0]
    
    # If there are no answers, return an empty list (AKA request domain name is not in the table of DNS records on server side)
    if ancount == 0:
        print("No answers in response.")
        return []

    # Parse each answer record
    answers = []
    while answerStart < len(response) and ancount > 0:
        # Each answer section starts with NAME pointer (2 bytes), followed by TYPE, CLASS (2 bytes each), TTL, and RDLENGTH
        # Unpack the rest of the answer section (Type, Class, TTL, rdlength)
        answerType, answerClass, ttl, rdlength = struct.unpack('!HHIH', response[answerStart + 2 : answerStart + 12])

        # Check if the expected number of bytes are available for the answer
        if len(response) < answerStart + 12 + rdlength:
            print("Error: Response is smaller than expected. Possibly a malformed response.")
            return []

        # Extract the IP address (should be 4 bytes for the provided records in lab manual)
        addr = socket.inet_ntoa(response[answerStart + 12 : answerStart + 12 + rdlength])

        # Use type and class maps to convert to human-readable labels (in this case Type A and Class IN)
        type_str = typeMapping.get(answerType, str(answerType))
        class_str = classMapping.get(answerClass, str(answerClass))
        
        answers.append(f"type {type_str}, class {class_str}, TTL {ttl}, addr ({rdlength}) {addr}")
        
        # Update the answer start position, skip over the current answer
        answerStart += 12 + rdlength
        ancount -= 1  # Decrement the number of answers remaining

    return answers



def startDnsClient():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # Initialize UDP socket

    while True:
        domainName = input("Enter Domain Name: ")
        if domainName.lower() == "end":
            print("Session ended")
            break

        query = constructQuery(domainName)
        client.sendto(query, ('127.0.0.1', 10053))   # Send query to the IP address and port number defined in server.py
        
        response, _ = client.recvfrom(512)
        for answer in parse_response(response):
            print(f"{domainName}: {answer}")

def main():
    startDnsClient()


main()