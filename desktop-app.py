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
        style = ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("TFrame", background="#111722")
        style.configure("TLabel", background="#111722", foreground="#e8eef8")
        style.configure("TButton", padding=8)
        top = ttk.Frame(self.root, padding=14); top.pack(fill="x")
        ttk.Label(top, text="Local AI", font=("Sans", 19, "bold")).pack(side="left")
        ttk.Label(top, text="Native desktop app · no browser window", foreground="#9fb0c7").pack(side="left", padx=14, pady=(7,0))
        settings = ttk.LabelFrame(self.root, text=" Model / API settings ", padding=10); settings.pack(fill="x", padx=14, pady=(0,10))
        self.endpoint = tk.StringVar(value=LOCAL_BASE)
        self.model_var = tk.StringVar(value=MODEL)
        self.key_var = tk.StringVar(value="")
        ttk.Label(settings, text="API base URL").grid(row=0,column=0,sticky="w",padx=4,pady=4)
        ttk.Entry(settings,textvariable=self.endpoint).grid(row=0,column=1,sticky="ew",padx=4,pady=4)
        ttk.Label(settings, text="Model ID").grid(row=1,column=0,sticky="w",padx=4,pady=4)
        ttk.Entry(settings,textvariable=self.model_var).grid(row=1,column=1,sticky="ew",padx=4,pady=4)
        ttk.Label(settings, text="API key (optional)").grid(row=2,column=0,sticky="w",padx=4,pady=4)
        ttk.Entry(settings,textvariable=self.key_var,show="•").grid(row=2,column=1,sticky="ew",padx=4,pady=4)
        settings.columnconfigure(1,weight=1)
        actions=ttk.Frame(settings); actions.grid(row=3,column=0,columnspan=2,sticky="ew",pady=(8,0))
        ttk.Checkbutton(actions,text="Use local model",variable=self.local_mode,command=self._toggle_mode).pack(side="left")
        ttk.Button(actions,text="Apply API settings",command=self.apply_settings).pack(side="right")
        ttk.Button(actions,text="Start local model",command=self.start_local).pack(side="right",padx=8)
        self.chat=tk.Text(self.root,bg="#0b111b",fg="#e8eef8",insertbackground="white",wrap="word",font=("Sans",11),relief="flat",padx=14,pady=12,state="disabled")
        self.chat.pack(fill="both",expand=True,padx=14,pady=(0,10))
        self.chat.tag_configure("user",foreground="#9bc5ff",spacing1=10,spacing3=8)
        self.chat.tag_configure("assistant",foreground="#e8eef8",spacing1=10,spacing3=12)
        bottom=ttk.Frame(self.root,padding=(14,0,14,14)); bottom.pack(fill="x")
        self.prompt=tk.Text(bottom,height=3,bg="#202b3b",fg="white",insertbackground="white",wrap="word",relief="flat",padx=10,pady=8)
        self.prompt.pack(side="left",fill="both",expand=True)
        self.prompt.bind("<Control-Return>",self._send_shortcut)
        self.send_btn=ttk.Button(bottom,text="Send",command=self.send); self.send_btn.pack(side="left",padx=(10,0),fill="y")
        self.status=tk.StringVar(value="Starting…")
        ttk.Label(self.root,textvariable=self.status,anchor="w",padding=(14,5)).pack(fill="x")
        self._toggle_mode()

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
