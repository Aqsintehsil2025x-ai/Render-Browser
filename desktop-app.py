#!/usr/bin/env python3
"""Render Browser + XFA native dark chat workspace."""
import json, queue, shutil, subprocess, threading, time, tkinter as tk
from tkinter import ttk, messagebox
from urllib.request import Request, urlopen
from urllib.error import HTTPError

MODEL="Qwen/Qwen2.5-0.5B-Instruct-GGUF:Q4_K_M"
LOCAL_BASE="http://127.0.0.1:8080/v1"
LOCAL_HEALTH="http://127.0.0.1:8080/health"
BG="#0b1020"; SIDE="#0e1628"; PANEL="#121d30"; PANEL2="#1a2940"
FG="#e8eef8"; MUTED="#91a2bb"; ACCENT="#9aa8ff"; GREEN="#69d6ae"

class DesktopAI:
    def __init__(self, root):
        self.root=root; root.title("Render Browser · XFA"); root.geometry("1180x780"); root.minsize(760,560); root.configure(bg=BG)
        self.proc=None; self.events=queue.Queue(); self.messages=[]; self.api_key=""; self.base=LOCAL_BASE; self.model=MODEL
        self.xfa_url="https://ai-bot-2--aqsintehsil2025.replit.app/xfa/api"; self.xfa_token=""
        self.mode=tk.StringVar(value="Local AI"); self.busy=False
        self._build(); root.after(100,self._drain_events); root.protocol("WM_DELETE_WINDOW",self.close)
        self.set_status("Hazır · Yerel model başlatılmayı bekliyor")

    def _build(self):
        st=ttk.Style(); st.theme_use("clam")
        st.configure("TButton",padding=(12,8),background=PANEL2,foreground=FG,borderwidth=0)
        st.map("TButton",background=[("active","#2a3b59")])
        st.configure("Accent.TButton",padding=(16,10),background=ACCENT,foreground="#0b1020",font=("Sans",10,"bold"))
        st.map("Accent.TButton",background=[("active","#b5beff")])
        st.configure("TEntry",fieldbackground=PANEL2,foreground=FG,insertcolor=FG,padding=9)
        shell=tk.Frame(self.root,bg=BG); shell.pack(fill="both",expand=True)
        side=tk.Frame(shell,bg=SIDE,width=230); side.pack(side="left",fill="y"); side.pack_propagate(False)
        tk.Label(side,text="✿  RENDER / XFA",bg=SIDE,fg=FG,font=("Sans",13,"bold")).pack(anchor="w",padx=18,pady=(24,25))
        tk.Button(side,text="＋   Yeni sohbet",command=self.new_chat,bg="#202e47",fg=FG,activebackground="#2a3b59",activeforeground=FG,relief="flat",anchor="w",padx=13,pady=11).pack(fill="x",padx=12)
        tk.Label(side,text="ÇALIŞMA ALANI",bg=SIDE,fg="#71839f",font=("Sans",8,"bold")).pack(anchor="w",padx=18,pady=(28,9))
        self.nav=tk.Label(side,text="●  Local AI",bg=SIDE,fg=GREEN,font=("Sans",10),anchor="w"); self.nav.pack(fill="x",padx=18,pady=5)
        tk.Label(side,text="●  XFA Agent",bg=SIDE,fg=MUTED,font=("Sans",10),anchor="w").pack(fill="x",padx=18,pady=5)
        tk.Button(side,text="▶   Yerel modeli başlat",command=self.start_local,bg=SIDE,fg=GREEN,activebackground=PANEL2,activeforeground=GREEN,relief="flat",anchor="w",padx=13,pady=10).pack(fill="x",padx=8,pady=(10,0))
        tk.Frame(side,bg="#25324a",height=1).pack(fill="x",padx=14,pady=20)
        tk.Button(side,text="⚙   Ayarlar ve bağlantılar",command=self.open_settings,bg=SIDE,fg=MUTED,activebackground=PANEL2,activeforeground=FG,relief="flat",anchor="w",padx=13,pady=10).pack(fill="x",padx=8,side="bottom",pady=14)
        main=tk.Frame(shell,bg=BG); main.pack(side="left",fill="both",expand=True)
        head=tk.Frame(main,bg=BG); head.pack(fill="x",padx=28,pady=(20,12))
        tk.Label(head,text="Sohbet",bg=BG,fg=FG,font=("Sans",17,"bold")).pack(side="left")
        self.modebox=ttk.Combobox(head,textvariable=self.mode,values=("Local AI","API Model","XFA Agent"),state="readonly",width=15); self.modebox.pack(side="right"); self.modebox.bind("<<ComboboxSelected>>",self._mode_changed)
        self.chat=tk.Text(main,bg=BG,fg=FG,insertbackground=FG,wrap="word",font=("Sans",11),relief="flat",padx=28,pady=12,state="disabled",borderwidth=0)
        self.chat.pack(fill="both",expand=True,padx=4)
        self.chat.tag_configure("un",foreground=ACCENT,font=("Sans",10,"bold"),spacing1=18)
        self.chat.tag_configure("ub",foreground=FG,lmargin1=12,lmargin2=12,rmargin=80,spacing3=16)
        self.chat.tag_configure("an",foreground=GREEN,font=("Sans",10,"bold"),spacing1=18)
        self.chat.tag_configure("ab",foreground=FG,lmargin1=12,lmargin2=12,rmargin=70,spacing3=18)
        self.chat.tag_configure("sys",foreground=MUTED,font=("Sans",9,"italic"),spacing1=8,spacing3=10)
        self._system("Merhaba! Yerel modelle çevrimdışı sohbet edebilir veya XFA Agent modunda görev planlayıp araştırma yapabilirsin.")
        wrap=tk.Frame(main,bg=BG); wrap.pack(fill="x",padx=26,pady=(8,8))
        comp=tk.Frame(wrap,bg=PANEL,highlightbackground="#293954",highlightthickness=1); comp.pack(fill="x")
        self.prompt=tk.Text(comp,height=3,bg=PANEL,fg=FG,insertbackground=FG,wrap="word",relief="flat",font=("Sans",11),padx=14,pady=12)
        self.prompt.pack(fill="x",padx=2,pady=(2,0)); self.prompt.bind("<Return>",self._enter); self.prompt.bind("<Shift-Return>",self._newline)
        bar=tk.Frame(comp,bg=PANEL); bar.pack(fill="x",padx=9,pady=(2,8))
        tk.Label(bar,text="Enter gönderir · Shift+Enter yeni satır",bg=PANEL,fg=MUTED,font=("Sans",8)).pack(side="left",padx=5)
        self.sendbtn=ttk.Button(bar,text="Gönder  ↑",style="Accent.TButton",command=self.send); self.sendbtn.pack(side="right")
        foot=tk.Frame(main,bg=BG); foot.pack(fill="x",padx=29,pady=(0,10))
        self.status=tk.StringVar(); tk.Label(foot,textvariable=self.status,bg=BG,fg=MUTED,font=("Sans",8),anchor="w").pack(side="left")
        tk.Label(foot,text="Yanıtlar model kapasitesiyle sınırlıdır",bg=BG,fg="#64748b",font=("Sans",8)).pack(side="right")

    def _system(self,s):
        self.chat.configure(state="normal"); self.chat.insert("end",s+"\n\n","sys"); self.chat.configure(state="disabled"); self.chat.see("end")
    def _append(self,s,user=False):
        self.chat.configure(state="normal"); self.chat.insert("end",("Sen" if user else "XFA / AI")+"\n","un" if user else "an"); self.chat.insert("end",s+"\n\n","ub" if user else "ab"); self.chat.configure(state="disabled"); self.chat.see("end")
    def set_status(self,s): self.status.set(s)
    def _mode_changed(self,_=None):
        m=self.mode.get(); self.nav.configure(text="●  "+m,fg=GREEN if m=="Local AI" else ACCENT)
        self.set_status({"Local AI":"Yerel mod · modeli başlat veya çalışan sunucuya bağ","API Model":"API modu · harici model bağlantısı","XFA Agent":"XFA modu · görev planlama ve salt-okunur araştırma"}[m])
    def _enter(self,e):
        if not (e.state & 1): self.send(); return "break"
    def _newline(self,e): self.prompt.insert("insert","\n"); return "break"
    def new_chat(self):
        if self.busy:return
        self.messages=[]; self.chat.configure(state="normal"); self.chat.delete("1.0","end"); self.chat.configure(state="disabled"); self._system("Yeni sohbet başladı. Nasıl yardımcı olayım?"); self.prompt.focus_set()

    def open_settings(self):
        w=tk.Toplevel(self.root); w.title("Bağlantı ayarları"); w.configure(bg=BG); w.geometry("650x480"); w.transient(self.root)
        body=tk.Frame(w,bg=BG,padx=22,pady=18); body.pack(fill="both",expand=True)
        tk.Label(body,text="Model ve XFA bağlantıları",bg=BG,fg=FG,font=("Sans",16,"bold")).pack(anchor="w",pady=(0,12))
        vals=[("OpenAI-compatible API URL",self.base,False),("Model ID",self.model,False),("API key (isteğe bağlı)",self.api_key,True),("XFA sunucu URL",self.xfa_url,False),("XFA erişim tokeni",self.xfa_token,True)]
        entries={}
        for label,value,secret in vals:
            tk.Label(body,text=label,bg=BG,fg=MUTED,font=("Sans",9)).pack(anchor="w",pady=(7,3))
            e=ttk.Entry(body,show="•" if secret else ""); e.pack(fill="x"); e.insert(0,value); entries[label]=e
        tk.Label(body,text="API anahtarı ve XFA tokeni yalnızca uygulama belleğinde tutulur.",bg=BG,fg="#71839f",font=("Sans",8)).pack(anchor="w",pady=8)
        def save():
            self.base=entries[vals[0][0]].get().strip().rstrip("/"); self.model=entries[vals[1][0]].get().strip()
            self.api_key=entries[vals[2][0]].get().strip(); self.xfa_url=entries[vals[3][0]].get().strip().rstrip("/")
            self.xfa_token=entries[vals[4][0]].get().strip()
            if not self.base.startswith(("http://","https://")) or not self.model or not self.xfa_url.startswith(("http://","https://")):
                messagebox.showerror("Ayarlar","Geçerli API URL, model ID ve XFA URL gir.",parent=w); return
            self.set_status("Ayarlar belleğe uygulandı."); w.destroy()
        ttk.Button(body,text="Kaydet",style="Accent.TButton",command=save).pack(anchor="e",pady=8)

    def _request(self,url,body=None,headers=None,timeout=30):
        data=None if body is None else json.dumps(body).encode()
        req=Request(url,data=data,headers=headers or {},method="GET" if body is None else "POST")
        with urlopen(req,timeout=timeout) as r:return r.status,r.read()
    def start_local(self):
        if not shutil.which("llama"):
            messagebox.showerror("llama.cpp bulunamadı","Arch tabanlı sistemde: sudo pacman -S --needed llama.cpp"); return
        self.mode.set("Local AI"); self._mode_changed(); self.set_status("Yerel model başlatılıyor…")
        threading.Thread(target=self._start_worker,daemon=True).start()
    def _start_worker(self):
        try:
            try:self._request(LOCAL_HEALTH,timeout=2); self.events.put(("status","Yerel model zaten çalışıyor.")); return
            except Exception:pass
            cmd=["llama","serve","-hf",MODEL,"--alias",MODEL,"--host","127.0.0.1","--port","8080","--ctx-size","2048","--n-predict","256","--parallel","1"]
            self.proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
            for _ in range(240):
                if self.proc.poll() is not None:raise RuntimeError("llama serve kapandı. Terminalde llama serve --help çıktısını kontrol et.")
                try:self._request(LOCAL_HEALTH,timeout=2); self.events.put(("status","Yerel model hazır · çevrimdışı sohbet edebilirsin.")); return
                except Exception:time.sleep(1)
            raise TimeoutError("Model başlatma zaman aşımına uğradı; RAM ve model indirme durumunu kontrol et.")
        except Exception as e:self.events.put(("error",str(e)))
    def send(self):
        if self.busy:return
        text=self.prompt.get("1.0","end").strip()
        if not text:return
        self.prompt.delete("1.0","end"); self._append(text,True); self.busy=True; self.sendbtn.configure(state="disabled")
        mode=self.mode.get(); self.set_status("XFA görevi yürütülüyor…" if mode=="XFA Agent" else "Yanıt hazırlanıyor…")
        if mode!="XFA Agent":self.messages.append({"role":"user","content":text})
        threading.Thread(target=self._send_worker,args=(mode,text),daemon=True).start()
    def _send_worker(self,mode,text):
        try:
            if mode=="XFA Agent":
                if not self.xfa_token:raise RuntimeError("Ayarlar bölümünden XFA erişim tokenini ekle.")
                h={"Content-Type":"application/json","Authorization":"Bearer "+self.xfa_token}
                _,raw=self._request(self.xfa_url+"/tasks/run",{"task":text},h,180)
                data=json.loads(raw.decode()); self.events.put(("answer",data.get("answer") or data.get("plan") or json.dumps(data,ensure_ascii=False))); return
            h={"Content-Type":"application/json"}
            if mode=="API Model" and self.api_key:h["Authorization"]="Bearer "+self.api_key
            base=LOCAL_BASE if mode=="Local AI" else self.base; model=MODEL if mode=="Local AI" else self.model
            body={"model":model,"messages":self.messages,"temperature":0.7,"max_tokens":512,"stream":False}
            _,raw=self._request(base+"/chat/completions",body,h,300)
            answer=json.loads(raw.decode())["choices"][0]["message"]["content"]
            self.messages.append({"role":"assistant","content":answer}); self.events.put(("answer",answer))
        except HTTPError as e:
            detail=e.read().decode("utf-8","replace")[:500]
            if mode!="XFA Agent" and self.messages and self.messages[-1]["role"]=="user":self.messages.pop()
            self.events.put(("error",f"HTTP {e.code}: {detail}"))
        except Exception as e:
            if mode!="XFA Agent" and self.messages and self.messages[-1]["role"]=="user":self.messages.pop()
            self.events.put(("error",str(e)))
    def _drain_events(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=="answer":self._append(value); self.set_status("Hazır."); self.busy=False; self.sendbtn.configure(state="normal")
                elif kind=="error":self.set_status(value); self.busy=False; self.sendbtn.configure(state="normal"); messagebox.showerror("AI / XFA hatası",value)
                else:self.set_status(value)
        except queue.Empty:pass
        self.root.after(100,self._drain_events)
    def close(self):
        if self.proc and self.proc.poll() is None:
            try:self.proc.terminate()
            except Exception:pass
        self.root.destroy()

if __name__=="__main__":
    root=tk.Tk(); app=DesktopAI(root); root.mainloop()
