import tkinter as tk

window = tk.Tk()

username = tk.StringVar()

entry = tk.Entry(window, textvariable=username)
entry.pack()

def show():
    print(username.get())

button = tk.Button(window, text="Print", command=show)
button.pack()

window.mainloop()