import socket
import os
from datetime import datetime
import mimetypes

# Defining constants for the servers host and port
HOST = '127.0.0.1'  # Localhost IP address
PORT = 8001         # Port number to run the server on

# Print the port number, just for reference
print(PORT)

# Set up server TCP socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverSocket:
    # Bind the server to the specified host and port so it knows where to listen
    serverSocket.bind((HOST, PORT))
    
    # Start listening for incoming connections. Up to 5 clients can wait in the queue
    serverSocket.listen(5)
    print(f"Server started at http://{HOST}:{PORT}")

    # Main loop where the server runs to handle client requests
    while True:
        # Accept a connection from a client
        # When a client connects, get its socket and address
        clientConnection, clientAddress = serverSocket.accept()
        try:
            with clientConnection:
                # Receive the client's HTTP request. Limit to 1024 bytes
                request = clientConnection.recv(1024).decode('utf-8')

                # If the request is empty (no data sent) wait for the next connection
                if not request:
                    continue

                # Parse the HTTP request line (the first line of the HTTP request)
                requestLine = request.splitlines()[0]
                try:
                    # Split the request line into method, path, and version
                    requestMethod, path, _ = requestLine.split()
                except ValueError:
                    # If the request line is invalid, send 400 Bad Request response. Not required but feels more complete this way
                    clientConnection.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                    continue

                # Check if the request method is supported
                if requestMethod in ['GET', 'HEAD']:
                    # Handle requests to the root path ("/").
                    if path == '/':
                        # If its a HEAD request only need to send the headers
                        if requestMethod == 'HEAD':
                            response = (
                                "HTTP/1.1 200 OK\r\n"
                                "Content-Type: text/html\r\n"
                                "Connection: close\r\n\r\n"
                            )
                        else:
                            # For a GET request, send both headers and the body content
                            response = (
                                "HTTP/1.1 200 OK\r\n"
                                "Content-Type: text/html\r\n"
                                "Connection: close\r\n\r\n"
                                "<html><body><h1>Welcome to the Server!</h1><p>Specify a file to view its content.</p></body></html>"
                            )
                        # Send the response to the client
                        clientConnection.sendall(response.encode())
                        continue

                    # If a specific file is requested, determine path
                    filePath = '.' + path

                    # Check if the file exists and is a regular file (not a directory)
                    if os.path.exists(filePath) and os.path.isfile(filePath):
                        # Gather file metadata like last modified time, content type, and size
                        lastModified = datetime.fromtimestamp(os.path.getmtime(filePath)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                        contentType = mimetypes.guess_type(filePath)[0] or 'application/octet-stream'
                        contentLength = os.path.getsize(filePath)

                        # Build the response headers
                        headers = {
                            "Connection": "close",
                            "Date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                            "Server": "PythonCustomServer/1.0",
                            "Last-Modified": lastModified,
                            "Content-Length": contentLength,
                            "Content-Type": contentType
                        }

                        # Format the headers into an HTTP response format
                        responseHeaders = "HTTP/1.1 200 OK\r\n" + "".join([f"{k}: {v}\r\n" for k, v in headers.items()]) + "\r\n"
                        clientConnection.sendall(responseHeaders.encode())

                        # If its a GET request send the files content as the response body
                        if requestMethod == 'GET':
                            with open(filePath, 'rb') as file:
                                clientConnection.sendfile(file)
                    else:
                        # If the file doesn't exist, respond with a 404 Not Found
                        response = (
                            "HTTP/1.1 404 Not Found\r\n"
                            "Content-Type: text/html\r\n"
                            "Connection: close\r\n\r\n"
                            "<html><body><h1>404 Not Found</h1><p>The requested file could not be found.</p></body></html>"
                        )
                        clientConnection.sendall(response.encode())
                else:
                    # For unsupported HTTP methods, send a 405 response
                    response = (
                        "HTTP/1.1 405 Method Not Allowed\r\n"
                        "Content-Type: text/html\r\n"
                        "Connection: close\r\n\r\n"
                        "<html><body><h1>405 Method Not Allowed</h1><p>Only GET and HEAD requests supported.</p></body></html>"
                    )
                    clientConnection.sendall(response.encode())
        finally:
            # Close the client connection once the request has been handled
            print("closing request")
            clientConnection.close()
