# Secure Chat Application
Loosely based on WhatsApp, written in Python, This is a TCP chat application with E2EE
Allowing for high security on a language like python!

## How to deploy
- Deploying the server is very easy! As simple as running `python3 server.py <ip> <port>` and you have yourself a 
chat server all nice and ready to go! Just connect with your client!

## FAQ

### Why did you choose to make this?
- I choose to make an easy deployable chat server because those more security aware of us never believe
apps like [WhatsApp<sup>TM</sup>](https://en.wikipedia.org/wiki/WhatsApp) that promise End-To-End Encryption 
  (I am by no means saying they are lying. Just that you never really know.) so by deploying your own server and telling your friends to connect! You know for sure that your messages
  are safe from prying eyes.

- Bored Sixth Form Student looking for a challenge this was a great way to get exactly that.  

- This project also gave me some experience in cryptographic area of Computer Science

### How safe is this application?
- The use of [AES-256Bit](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) makes the messages about as secure as they can be.
  Even if someone gets a hold of your message history they would need a quantum computer
  for it to be feasible to be cracked

- The server software its self uses SSL when it sends and receives messages, so they
  MiTM attacks are unfeasible in this instance. 

- The client uses os.urandom to generate the AES key and Initialisation vector this uses the devices 
  random generator which is considered cryptographically secure in many instances.

- Even if some gains access to the Machine you host the server on, it won't matter
  because everything the server receives are encrypted. Also, the key is stored on the client never 
  sent to the server.

### What platforms will have releases?
- These ones [MacOS](https://en.wikipedia.org/wiki/MacOS), [IOS](https://en.wikipedia.org/wiki/IOS), [Android](https://en.wikipedia.org/wiki/Android), [Windows](https://en.wikipedia.org/wiki/Microsoft_Windows)
  and [Linux](https://en.wikipedia.org/wiki/Linux)


### Inspirations
[This kivy tutorial __from__ Sentdex](https://pythonprogramming.net/introduction-kivy-application-python-tutorial/) and
[This sockets tutorial __from__ Sentdex](https://pythonprogramming.net/sockets-tutorial-python-3/)

