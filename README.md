# Secure Chat Application
Loosely based on WhatsApp, written in Python, This is a TCP chat application with E2EE
Allowing for high security on a language like python!

## FAQ

### How safe is this application?
- The use of [AES-256Bit](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) makes the messages about as secure as they can be.
  Even if someone gets a hold of your message history they would need a quantum computer
  for it to be feasible to be cracked

- The server software its self uses SSL when it sends and receives messages, so they
  MiTM attacks are unfeasible in this instance. 

- The client uses os.urandom to generate the AES key and Initialisation vector this uses the devices 
  random generator which is considered cryptographically secure in many instances.

### What platforms will have releases?
- These ones [MacOS](https://en.wikipedia.org/wiki/MacOS), [IOS](https://en.wikipedia.org/wiki/IOS), [Android](https://en.wikipedia.org/wiki/Android), [Windows](https://en.wikipedia.org/wiki/Microsoft_Windows)
  and [Linux](https://en.wikipedia.org/wiki/Linux)


### Inspirations
[This kivy tutorial by Sentdex](https://pythonprogramming.net/introduction-kivy-application-python-tutorial/) and
[This sockets tutorial Sentdex](https://pythonprogramming.net/sockets-tutorial-python-3/)

