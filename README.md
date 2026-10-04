

#  LivePulse  

**LivePulse** takes raw live ICMP traffic, measures how the network is behaving, converts those measurements into behavioral signals, classifies the observed behavior, and displays the reasoning in real time.  

> Real-time network behavior monitoring from live packet traffic.  

LivePulse is a **V1 network-monitoring project** that transforms raw ICMP traffic into measurable and explainable network behavior.  

It captures packets with **TShark**, parses them into structured data, calculates network metrics, extracts behavioral signals, compares them against a behavior matrix, and presents the results through a **terminal monitor** and **Streamlit dashboard**.  

---

## 🎯 Problem  

Normal ping output mainly answers:  
- Did the host reply?  
- How long did it take?  

**LivePulse goes further** by describing how the network is behaving using signals such as:  
- RTT spikes  
- RTT instability  
- Sudden RTT changes  
- Traffic bursts  
- Packet loss  

**Problem Statement:**  
*How can live network traffic be transformed into measurable, interpretable network behavior in real time?*  

---

## 🏗️ Architecture  

<img width="1408" height="768" alt="image" src="https://github.com/user-attachments/assets/08b8df46-3ceb-4244-9f29-7b199413697f" />


### Component Responsibilities  

| Component     | Responsibility |
|---------------|----------------|
| `capture.py`  | Captures live ICMP traffic using TShark |
| `parser.py`   | Converts raw TShark output into Packet objects |
| `metrics.py`  | Calculates RTT, jitter, loss, and behavioral signals |
| `monitor.py`  | Coordinates the pipeline and terminal output |
| `dashboard.py`| Visualizes live network behavior |
| `main.py`     | Starts LivePulse |

---

## 🔄 How It Works  

1. **Capture**  
   - TShark streams: timestamp, source, destination, ICMP type, sequence number  

2. **Parse**  
   - Raw text → structured packet → `Packet(...)`  

3. **Measure**  
   - Matches ICMP requests/replies using sequence numbers  
   - Calculates RTT = reply timestamp − request timestamp  
   - Maintains history for jitter & changes  

4. **Detect Packet Loss**  
   - Tracks outstanding requests  
   - If reply doesn’t arrive within timeout → **Packet Loss**  

5. **Extract Behavior**  
   - Measurements → behavioral signals:  
     - RTT Spike → 0/1  
     - RTT Instability → 0/1  
     - Sudden RTT Change → 0/1  
     - Traffic Burst → 0/1  
     - Packet Loss → 0/1  

6. **Classify**  
   - Signals compared against predefined patterns  
   - Results explained via: matched, missing, unexpected signals + similarity %  

<img width="1408" height="768" alt="image" src="https://github.com/user-attachments/assets/fd0cd800-b51c-4b40-91ae-5c16428a8921" />


---

## 🧠 Important Engineering Decisions  

- **No self-influence baseline**  
  - Previous history → analyze current → classify → store current  
- **Request/reply correlation**  
  - RTT calculated via ICMP sequence numbers, not packet order  
- **Explainable behavior**  
  - Instead of “Anomaly,” LivePulse explains:  
    - *Possible Network Instability*  
    - Matched: RTT Spike, Sudden RTT Change  
    - Missing: RTT Instability  

---

## 📊 Dashboard  

The Streamlit dashboard provides:  
- Average RTT  
- Jitter  
- Packet loss  
- Live RTT chart  
- Current behavior  
- Behavioral signals  
- Recent behavior timeline  

---

## 🖥️ Run  

1. **Activate environment**  
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
  
2. **Start LivePulse terminal monitor**  
   ```bash
   python main.py
   ```
  
3. **Generate traffic**  
   ```bash
   ping -n 30 8.8.8.8
   ```
  
4. **Start dashboard**  
   ```bash
   streamlit run dashboard.py
   ```
     Streamlit will display a local URL → open in browser.  

---

## 📁 Project Structure  

```
livepulse/
│
├── livepulse/
│   ├── __init__.py
│   ├── capture.py
│   ├── parser.py
│   ├── metrics.py
│   └── monitor.py
│
├── dashboard.py
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🧪 V1 Scope  

LivePulse V1 is a **lightweight, rule-based network behavior monitoring system** focused on live ICMP traffic.  

It is designed to be:  
-  Real-time  
-  Explainable  
-  Modular  
-  Lightweight  
-  Easy to inspect & extend  

**LivePulse turns raw network traffic into an interpretable view of network behavior.**  

---

Would you like me to also add **badges** (like Python version, license, build status) at the top to make it look even more professional?
