#!/usr/bin/env python3
"""Native desktop chat for a local llama.cpp server or an OpenAI-compatible API."""
import json
import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

MODEL = "Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M"
LOCAL_BASE = "http://127.0.0.1:8080/v1"
LOCAL_HEALTH = "http://127.0.0.1:8080/health"

class DesktopAI:
    def __init__(self, root):
        self.root = root
        self.root.title("Render Browser · Local AI")
        self.root.geometry("900x680")
        self.root.minsize(620, 480)
        self.root.configure(bg="#111722")
        self.proc = None
        self.events = queue.Queue()
        self.messages = []
        self.api_key = ""
        self.base = LOCAL_BASE
        self.model = MODEL
        self.local_mode = tk.BooleanVar(value=True)
        self._build()
        self.root.after(100, self._drain_events)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.set_status("Ready. Start the local model or enter an API endpoint.")

    def _build(self):
        # Modern dark desktop layout using native Tk widgets.
        bg = "#0b1020"
        panel = "#121a2b"
        panel2 = "#182338"
        muted = "#91a2bd"
        accent = "#6d8cff"
        self.root.configure(bg=bg)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground="#e8eef8")
        style.configure("TCheckbutton", background=panel, foreground="#dce6f7")
        style.map("TCheckbutton", background=[("active", panel)], foreground=[("active", "#ffffff")])

        header = tk.Frame(self.root, bg=bg, padx=22, pady=17)
        header.pack(fill="x")
        brand = tk.Frame(header, bg=bg)
        brand.pack(side="left")
        tk.Label(brand, text="✦", bg=accent, fg="white", font=("Sans", 15, "bold"),
                 width=2, height=1).pack(side="left", padx=(0, 10))
        titlebox = tk.Frame(brand, bg=bg)
        titlebox.pack(side="left")
        tk.Label(titlebox, text="Render Browser", bg=bg, fg="#f2f5ff",
                 font=("Sans", 15, "bold")).pack(anchor="w")
        tk.Label(titlebox, text="LOCAL AI WORKSPACE", bg=bg, fg=muted,
                 font=("Sans", 8, "bold")).pack(anchor="w", pady=(2, 0))
        self.status = tk.StringVar(value="Ready")
        tk.Label(header, textvariable=self.status, bg=panel2, fg="#b9c9e8",
                 font=("Sans", 9), padx=12, pady=7).pack(side="right")

        settings = tk.Frame(self.root, bg=panel, padx=16, pady=13,
                            highlightthickness=1, highlightbackground="#26334b")
        settings.pack(fill="x", padx=18, pady=(0, 12))
        topbar = tk.Frame(settings, bg=panel)
        topbar.pack(fill="x")
        tk.Label(topbar, text="Connection", bg=panel, fg="#f2f5ff",
                 font=("Sans", 11, "bold")).pack(side="left")
        self.settings_hint = tk.Label(topbar, text="LOCAL MODEL", bg=panel2, fg="#9eb6ff",
                                      font=("Sans", 8, "bold"), padx=9, pady=4)
        self.settings_hint.pack(side="right")

        fields = tk.Frame(settings, bg=panel)
        fields.pack(fill="x", pady=(10, 8))
        self.endpoint = tk.StringVar(value=LOCAL_BASE)
        self.model_var = tk.StringVar(value=MODEL)
        self.key_var = tk.StringVar(value="")
        for row, (label, var, secret) in enumerate((
            ("API endpoint", self.endpoint, False),
            ("Model ID", self.model_var, False),
            ("API key", self.key_var, True),
        )):
            tk.Label(fields, text=label, bg=panel, fg=muted,
                     font=("Sans", 9)).grid(row=row, column=0, sticky="w", padx=(0, 14), pady=4)
            entry = tk.Entry(fields, textvariable=var, bg="#0c1424", fg="#e8eef8",
                             insertbackground="white", relief="flat", bd=0,
                             highlightthickness=1, highlightbackground="#2a3954",
                             highlightcolor=accent, font=("Sans", 10),
                             show="•" if secret else "")
            entry.grid(row=row, column=1, sticky="ew", ipady=7, padx=2, pady=4)
        fields.columnconfigure(1, weight=1)

        controls = tk.Frame(settings, bg=panel)
        controls.pack(fill="x", pady=(4, 0))
        self.local_mode = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="Use local model", variable=self.local_mode,
                        command=self._toggle_mode).pack(side="left")
        tk.Button(controls, text="Apply API settings", command=self.apply_settings,
                  bg=panel2, fg="#dce6f7", activebackground="#263653",
                  activeforeground="white", relief="flat", bd=0,
                  padx=13, pady=8, cursor="hand2").pack(side="right")
        tk.Button(controls, text="▶  Start local model", command=self.start_local,
                  bg=accent, fg="white", activebackground="#5878ed",
                  activeforeground="white", relief="flat", bd=0,
                  padx=15, pady=8, cursor="hand2").pack(side="right", padx=(0, 8))

        chat_card = tk.Frame(self.root, bg="#0e1626", padx=2, pady=2,
                             highlightthickness=1, highlightbackground="#202e46")
        chat_card.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        self.chat = tk.Text(chat_card, bg="#0e1626", fg="#e8eef8",
                            insertbackground="white", wrap="word",
                            font=("Sans", 11), relief="flat", padx=22, pady=18,
                            state="disabled", spacing1=3, spacing3=5,
                            selectbackground="#31466d")
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_configure("user_name", foreground="#9db6ff",
                                font=("Sans", 10, "bold"), spacing1=14)
        self.chat.tag_configure("ai_name", foreground="#72dfb2",
                                font=("Sans", 10, "bold"), spacing1=14)
        self.chat.tag_configure("body", foreground="#e1e8f5",
                                font=("Sans", 11), lmargin1=8, lmargin2=8, spacing3=9)
        self.chat.tag_configure("welcome", foreground=muted, justify="center",
                                font=("Sans", 10), spacing1=12, spacing3=12)
        self._append("Render Browser AI", "Your private AI workspace is ready. Start the local model or connect an API, then write your first message below.", "welcome")

        composer = tk.Frame(self.root, bg=bg, padx=18, pady=(0, 10))
        composer.pack(fill="x")
        input_card = tk.Frame(composer, bg=panel, padx=10, pady=8,
                              highlightthickness=1, highlightbackground="#2a3954")
        input_card.pack(fill="x")
        self.prompt = tk.Text(input_card, height=3, bg=panel, fg="#f0f4ff",
                              insertbackground="white", wrap="word", relief="flat",
                              font=("Sans", 11), padx=5, pady=5)
        self.prompt.pack(side="left", fill="both", expand=True)
        self.prompt.insert("1.0", "Message your AI…")
        self.prompt.configure(fg="#73839e")
        self.prompt.bind("<FocusIn>", self._prompt_focus_in)
        self.prompt.bind("<FocusOut>", self._prompt_focus_out)
        self.prompt.bind("<Return>", self._enter_to_send)
        self.prompt.bind("<Shift-Return>", self._newline_shortcut)
        self.send_btn = tk.Button(input_card, text="Send  ➤", command=self.send,
                                  bg=accent, fg="white", activebackground="#5878ed",
                                  activeforeground="white", relief="flat", bd=0,
                                  padx=17, pady=11, cursor="hand2",
                                  font=("Sans", 10, "bold"))
        self.send_btn.pack(side="right", padx=(8, 0))
        footer = tk.Frame(composer, bg=bg)
        footer.pack(fill="x", pady=(6, 0))
        tk.Label(footer, text="Enter to send  ·  Shift + Enter for a new line",
                 bg=bg, fg="#71819b", font=("Sans", 8)).pack(side="left")
        tk.Button(footer, text="Clear chat", command=self.clear_chat,
                  bg=bg, fg=muted, activebackground=bg, activeforeground="white",
                  relief="flat", bd=0, cursor="hand2").pack(side="right")
        self._toggle_mode()

    def _prompt_focus_in(self, _event):
        if self.prompt.get("1.0", "end-1c") == "Message your AI…":
            self.prompt.delete("1.0", "end")
            self.prompt.configure(fg="#f0f4ff")

    def _prompt_focus_out(self, _event):
        if not self.prompt.get("1.0", "end-1c").strip():
            self.prompt.insert("1.0", "Message your AI…")
            self.prompt.configure(fg="#73839e")

    def _enter_to_send(self, event):
        self.send()
        return "break"

    def _newline_shortcut(self, _event):
        self.prompt.insert("insert", "\\n")
        return "break"

    def clear_chat(self):
        self.messages = []
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self.set_status("Chat cleared.")

    def _toggle_mode(self):
        if self.local_mode.get():
            self.endpoint.set(LOCAL_BASE); self.model_var.set(MODEL); self.key_var.set("")
            self.set_status("Local mode selected. Start the local model.")
        else:
            self.set_status("API mode selected. Enter a trusted OpenAI-compatible endpoint and model ID.")

    def set_status(self, value): self.status.set(value)

    def apply_settings(self):
        base=self.endpoint.get().strip().rstrip("/")
        model=self.model_var.get().strip()
        if not base.startswith(("http://","https://")) or not model:
            messagebox.showerror("Invalid settings","Enter a valid http(s) API base URL and model ID."); return
        self.base=base; self.model=model; self.api_key=self.key_var.get().strip(); self.messages=[]
        self.chat.configure(state="normal"); self.chat.delete("1.0","end"); self.chat.configure(state="disabled")
        self.set_status("Settings applied. API key is kept in memory only until the app closes.")

    def _request(self,url,body=None,headers=None,timeout=15):
        data=None if body is None else json.dumps(body).encode()
        req=Request(url,data=data,headers=headers or {},method="GET" if body is None else "POST")
        with urlopen(req,timeout=timeout) as response: return response.status,response.read()

    def start_local(self):
        if not self.local_mode.get(): self.local_mode.set(True); self._toggle_mode()
        if shutil.which("llama") is None:
            messagebox.showerror("llama not found","Install llama.cpp CLI and make sure `llama` is on PATH."); return
        self.apply_settings()
        self.set_status("Checking local model server…")
        threading.Thread(target=self._start_local_worker,daemon=True).start()

    def _start_local_worker(self):
        try:
            try:
                self._request(LOCAL_HEALTH,timeout=2)
                self.events.put(("status","Local model server is already running.")); return
            except Exception: pass
            cmd=["llama","serve","-hf",MODEL,"--alias",MODEL,"--host","127.0.0.1","--port","8080","--ctx-size","2048","--n-predict","256","--parallel","1"]
            self.proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
            for _ in range(240):
                if self.proc.poll() is not None: raise RuntimeError("llama serve stopped. Run `llama serve --help` in a terminal to check your installed version.")
                try:
                    self._request(LOCAL_HEALTH,timeout=2)
                    self.events.put(("status","Local model is ready. You can chat offline.")); return
                except Exception: time.sleep(1)
            raise TimeoutError("Model startup timed out. Check RAM and model download/cache status.")
        except Exception as exc: self.events.put(("error",str(exc)))

    def send(self):
        text=self.prompt.get("1.0","end").strip()
        if not text: return
        self.prompt.delete("1.0","end")
        self._append("You",text,"user")
        self.messages.append({"role":"user","content":text})
        self.send_btn.configure(state="disabled"); self.set_status("Generating…")
        threading.Thread(target=self._send_worker,daemon=True).start()

    def _send_worker(self):
        try:
            headers={"Content-Type":"application/json"}
            if self.api_key: headers["Authorization"]="Bearer "+self.api_key
            body={"model":self.model,"messages":self.messages,"temperature":0.7,"max_tokens":256,"stream":False}
            code,raw=self._request(self.base+"/chat/completions",body,headers,timeout=300)
            data=json.loads(raw.decode("utf-8")); answer=data["choices"][0]["message"]["content"]
            self.messages.append({"role":"assistant","content":answer})
            self.events.put(("answer",answer))
        except HTTPError as exc:
            detail=exc.read().decode("utf-8","replace")[:500]; self.messages.pop(); self.events.put(("error",f"API HTTP {exc.code}: {detail}"))
        except Exception as exc:
            if self.messages and self.messages[-1].get("role")=="user": self.messages.pop()
            self.events.put(("error",f"Could not get a response: {exc}"))

    def _append(self,label,text,tag):
        self.chat.configure(state="normal"); self.chat.insert("end",label+"\n","bold"); self.chat.insert("end",text+"\n\n",tag); self.chat.configure(state="disabled"); self.chat.see("end")

    def _drain_events(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=="answer": self._append("AI",value,"assistant"); self.set_status("Ready."); self.send_btn.configure(state="normal")
                elif kind=="error": self.set_status(value); self.send_btn.configure(state="normal"); messagebox.showerror("AI error",value)
                else: self.set_status(value)
        except queue.Empty: pass
        self.root.after(100,self._drain_events)

    def _send_shortcut(self,event): self.send(); return "break"

    def close(self):
        if self.proc and self.proc.poll() is None:
            try: self.proc.terminate()
            except Exception: pass
        self.root.destroy()

if __name__=="__main__":
    root=tk.Tk(); app=DesktopAI(root); root.mainloop()
