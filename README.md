OffGrid Messenger is a Python Flask-based application for **offline messaging and file sharing** between devices connected to the same local network or mobile hotspot.

The application does not require an internet connection.

To RUN

### Install Required Package
pip install -r requirements.txt
or
pip install flask

### Start the Server
python server.py

Open a browser and enter:
http://127.0..... continues


###  Turn On Phone Hotspot
###  Connect Laptop
###  Find Laptop IP Address
or type on cmd  
ipconfig

Under:

```text
Wireless LAN adapter Wi-Fi
```

find the IPv4 Address.
Example:

```text
IPv4 Address . . . . . : 10.205.75.74
```

### 4. Open on Phone

Keep `server.py` running on the laptop.

Open Chrome on the phone and enter:

```text
http://LAPTOP-IP:5000
```

If the application works on the laptop but does not open on another device, check Windows Firewall and make sure Python/Flask is allowed on the private network.


## Author

Adithya Nayak   
MIT Manipal

