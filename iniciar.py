import webbrowser
import threading

def abrir():
    webbrowser.open('http://localhost:8000')

threading.Timer(1.5, abrir).start()
