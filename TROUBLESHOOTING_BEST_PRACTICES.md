# 🔧 Troubleshooting, Best Practices & Tips

## 📋 Indice
1. [Troubleshooting Comune](#troubleshooting-comune)
2. [Best Practices](#best-practices)
3. [Ottimizzazione Prestazioni](#ottimizzazione-prestazioni)
4. [Sicurezza Dati](#sicurezza-dati)
5. [Debug e Logging](#debug-e-logging)
6. [FAQ](#faq)
7. [Tips e Trucchi](#tips-e-trucchi)

---

## 🔍 Troubleshooting Comune

### ❌ Errore: "ModuleNotFoundError: No module named 'PyQt5'"

**Causa:** PyQt5 non è installato

**Soluzione:**
```bash
# Installazione standard
pip install PyQt5

# Se il precedente non funziona, prova:
pip install PyQt5 --upgrade

# Su Linux, potrebbe servire:
sudo apt-get install python3-pyqt5

# Su macOS:
brew install pyqt5
```

**Verifica installazione:**
```bash
python -c "from PyQt5 import QtCore; print('PyQt5 OK')"
```

---

### ❌ Errore: "sqlite3.OperationalError: table prodotti already exists"

**Causa:** Il database esiste già e si sta tentando di creare le tabelle di nuovo

**Soluzione:**
```bash
# Opzione 1: Elimina il database e riavvia
rm ristorante_ordini.db
python interfaccia_grafica.py

# Opzione 2: Copia il database e continua
cp ristorante_ordini.db ristorante_ordini.backup.db

# Opzione 3: Se i dati sono importanti, esegui setup una sola volta
python setup_database.py  # Una volta sola!
```

---

### ❌ Errore: "PermissionError: [Errno 13] Permission denied: 'ristorante_ordini.db'"

**Causa:** Mancano i permessi di lettura/scrittura sul file

**Soluzione su Linux/Mac:**
```bash
# Dai i permessi corretti
chmod 644 ristorante_ordini.db
chmod 755 .  # Directory corrente

# Se la directory è protetta, cambia proprietario
sudo chown $USER:$USER ristorante_ordini.db
```

**Soluzione su Windows:**
```cmd
# Controlla proprietà file
# Clicca destro → Proprietà → Sicurezza → Modifica
# Assicurati che il tuo utente abbia permessi "Modifica"
```

---

### ❌ L'applicazione non si avvia

**Primo step - Verifica Python:**
```bash
python --version  # Deve essere 3.7+
```

**Secondo step - Verifica dipendenze:**
```bash
python -m pip list | grep PyQt5
```

**Terzo step - Verifica file:**
```bash
ls -la modelli.py database.py gestione_ordini.py interfaccia_grafica.py
```

**Debug dettagliato:**
```bash
python -u interfaccia_grafica.py 2>&1 | head -50
```

---

### ❌ L'interfaccia è piccolissima su tablet/monitor grande

**Causa:** Il DPI del monitor non è gestito correttamente

**Soluzione nel codice:**
```python
# In interfaccia_grafica.py, prima di QApplication
import os
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

app = QApplication(sys.argv)
app.setAttribute(Qt.AA_EnableHighDpiScaling)
```

**Oppure modifica i font nel metodo configura_stili():**
```python
def configura_stili(self):
    self.setStyleSheet("""
        QPushButton {
            font-size: 20px;      # Aumenta la dimensione
            min-height: 100px;    # Aumenta altezza pulsanti
            min-width: 200px;     # Aumenta larghezza
        }
        QLabel {
            font-size: 18px;      # Più grande
        }
    """)
```

---

### ❌ Database corrotto - "database disk image is malformed"

**Causa:** Interruzione durante una operazione di scrittura

**Soluzione:**
```bash
# Ripristina dal backup
cp ristorante_ordini.backup.db ristorante_ordini.db

# Se non hai backup, ripristina il database
python -c "
import sqlite3
db = sqlite3.connect('ristorante_ordini.db')
db.execute('PRAGMA integrity_check')
result = db.fetchone()
print(result)
"

# Ripara (se possibile)
sqlite3 ristorante_ordini.db "VACUUM;"
sqlite3 ristorante_ordini.db "PRAGMA integrity_check;"
```

---

### ❌ Ordini non si salvano nel database

**Verifica:**
```bash
# 1. Il file database esiste?
ls -la ristorante_ordini.db

# 2. Contiene dati?
sqlite3 ristorante_ordini.db "SELECT COUNT(*) FROM ordini;"

# 3. Le tabelle esistono?
sqlite3 ristorante_ordini.db ".tables"

# 4. Importanza dei prodotti
sqlite3 ristorante_ordini.db "SELECT COUNT(*) FROM prodotti;"
```

**Debug nel codice:**
```python
# In gestione_ordini.py, aggiungi logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def salva_ordine_attivo(self, numero_tavolo):
    ordine = self.get_ordine_attivo(numero_tavolo)
    if ordine:
        logger.info(f"Salvataggio ordine {ordine.id_ordine}")
        result = self.db.salva_ordine(ordine)
        logger.info(f"Risultato salvataggio: {result}")
        return result
    return False
```

---

### ❌ Interfaccia si blocca quando salvo

**Causa:** L'operazione di database è bloccante

**Soluzione - Usa threading (avanzato):**
```python
from PyQt5.QtCore import QThread, pyqtSignal

class SalvaOrdineWorker(QThread):
    finito = pyqtSignal(bool)
    
    def __init__(self, gestione, numero_tavolo):
        super().__init__()
        self.gestione = gestione
        self.numero_tavolo = numero_tavolo
    
    def run(self):
        risultato = self.gestione.salva_ordine_attivo(self.numero_tavolo)
        self.finito.emit(risultato)

# Uso nella GUI:
def salva_non_bloccante(self):
    worker = SalvaOrdineWorker(self.gestione, self.tavolo_selezionato)
    worker.finito.connect(self.on_salvataggio_completato)
    worker.start()
```

---

### ❌ Su tablet, i pulsanti sono troppo vicini

**Soluzione:**
```python
# In interfaccia_grafica.py
layout_sinistra.setSpacing(15)  # Aumenta spazio tra elementi
layout_sinistra.setContentsMargins(10, 10, 10, 10)  # Più margini

# Per i pulsanti tavoli:
btn.setMinimumHeight(100)  # Più alti
btn.setMinimumWidth(200)   # Più larghi
grid_tavoli.setSpacing(12)  # Spazio tra pulsanti
```

---

## ✅ Best Practices

### 1. **Gestione Errori**

```python
# ✗ Non fare così:
def salva():
    ordine = self.get_ordine_attivo(tavolo)
    self.db.salva_ordine(ordine)  # Cosa se fallisce?

# ✓ Fai così:
def salva(self):
    try:
        ordine = self.get_ordine_attivo(tavolo)
        if not ordine:
            raise ValueError("Nessun ordine attivo")
        if ordine.is_vuoto():
            raise ValueError("Ordine vuoto, impossibile salvare")
        
        if self.db.salva_ordine(ordine):
            logger.info(f"Ordine {ordine.id_ordine} salvato")
            return True
        else:
            logger.error("Errore salvataggio database")
            raise Exception("Errore nel salvataggio")
            
    except Exception as e:
        logger.error(f"Errore: {e}", exc_info=True)
        QMessageBox.critical(self, "Errore", f"Impossibile salvare: {e}")
        return False
```

---

### 2. **Validazione Dati**

```python
# Valida gli input
def aggiungi_prodotto_menu(self, nome, categoria, prezzo):
    # Validazione
    if not nome or not nome.strip():
        raise ValueError("Nome prodotto vuoto")
    
    if prezzo <= 0:
        raise ValueError("Prezzo deve essere positivo")
    
    if not categoria:
        raise ValueError("Categoria richiesta")
    
    # Procedi se tutto ok
    prodotto = Prodotto(
        id_prodotto=max(p.id_prodotto for p in self.get_tutti_prodotti()) + 1,
        nome=nome.strip(),
        categoria=categoria,
        prezzo=round(prezzo, 2)
    )
    return self.aggiungi_prodotto_menu(prodotto)
```

---

### 3. **Logging Strutturato**

```python
# setup_logging.py
import logging
import logging.handlers

def setup_logging(log_file='ristorante.log'):
    logger = logging.getLogger('ristorante')
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

# Uso:
logger = setup_logging()
logger.info("Applicazione avviata")
logger.warning("Tavolo occupato da tempo")
logger.error("Errore salvataggio ordine", exc_info=True)
```

---

### 4. **Context Manager per Database**

```python
# Migliora la gestione della connessione
from contextlib import contextmanager

class DatabaseOrdini:
    @contextmanager
    def get_connection(self):
        conn = self.connessione or sqlite3.connect(self.nome_db)
        try:
            yield conn
        finally:
            if not self.connessione:
                conn.close()

# Uso:
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prodotti")
    # Automaticamente chiude la connessione
```

---

### 5. **Configuration Management**

```python
# config.py
import configparser

class Configurazione:
    def __init__(self, file_config='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(file_config)
    
    @property
    def numero_tavoli(self):
        return self.config.getint('ristorante', 'numero_tavoli', fallback=10)
    
    @property
    def nome_database(self):
        return self.config.get('database', 'nome', fallback='ristorante_ordini.db')
    
    @property
    def debug_mode(self):
        return self.config.getboolean('debug', 'enabled', fallback=False)

# config.ini
[ristorante]
numero_tavoli = 15
nome_ristorante = Pizzeria da Mario

[database]
nome = ristorante_ordini.db
backup_path = ./backups

[debug]
enabled = false
```

---

## ⚡ Ottimizzazione Prestazioni

### 1. **Caching Dati**

```python
class GestioneOrdini:
    def __init__(self):
        self._cache_prodotti = None
        self._cache_timestamp = 0
    
    def get_tutti_prodotti(self, use_cache=True):
        import time
        now = time.time()
        
        # Ricarica cache ogni 60 secondi
        if use_cache and self._cache_prodotti and (now - self._cache_timestamp) < 60:
            return self._cache_prodotti
        
        self._cache_prodotti = self.db.get_tutti_prodotti()
        self._cache_timestamp = now
        return self._cache_prodotti
```

---

### 2. **Lazy Loading**

```python
# Carica i dati solo quando necessario
class Tavolo:
    def __init__(self, numero):
        self.numero = numero
        self._ordine = None
    
    @property
    def ordine_attivo(self):
        if self._ordine is None:
            self._ordine = self.db.get_ordine_attivo(self.numero)
        return self._ordine
```

---

### 3. **Batch Operations**

```python
# Invece di salvare uno per uno
def salva_tutti_ordini(self, ordini):
    conn = self.db.connessione
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN TRANSACTION")
        for ordine in ordini:
            # Salva tutti in una transazione
            self._salva_ordine_interno(cursor, ordine)
        cursor.execute("COMMIT")
        return True
    except Exception as e:
        cursor.execute("ROLLBACK")
        logger.error(f"Errore batch save: {e}")
        return False
```

---

### 4. **Indici Database**

```python
# Aggiungi indici per query veloci
def aggiunta_indici(self):
    cursor = self.connessione.cursor()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ordini_tavolo ON ordini(id_tavolo)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ordini_stato ON ordini(stato)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_righe_ordine ON righe_ordini(id_ordine)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prodotti_categoria ON prodotti(categoria)')
    self.connessione.commit()
```

---

## 🔐 Sicurezza Dati

### 1. **Backup Automatico**

```python
# backup.py
import shutil
from datetime import datetime, timedelta
import os

class GestoreBackup:
    def __init__(self, db_name='ristorante_ordini.db', backup_dir='./backups'):
        self.db_name = db_name
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"{self.db_name}.{timestamp}")
        shutil.copy(self.db_name, backup_file)
        logger.info(f"Backup creato: {backup_file}")
        return backup_file
    
    def pulizia_vecchi_backup(self, giorni=30):
        """Rimuove backup più vecchi di 30 giorni"""
        cutoff_time = datetime.now() - timedelta(days=giorni)
        for filename in os.listdir(self.backup_dir):
            filepath = os.path.join(self.backup_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_time:
                    os.remove(filepath)
                    logger.info(f"Backup rimosso: {filename}")

# Usa nel main:
backup = GestoreBackup()
backup.backup()  # Backup giornaliero
backup.pulizia_vecchi_backup()  # Pulizia settimanale
```

---

### 2. **Validazione SQL (Prevenzione SQL Injection)**

```python
# ✗ Pericoloso:
def get_ordine_unsafe(self, id):
    query = f"SELECT * FROM ordini WHERE id_ordine = {id}"
    cursor.execute(query)  # SQL Injection!

# ✓ Sicuro:
def get_ordine_safe(self, id):
    query = "SELECT * FROM ordini WHERE id_ordine = ?"
    cursor.execute(query, (id,))  # Parametrizzato!
```

---

### 3. **Validazione Input**

```python
def is_valid_numero_tavolo(self, numero):
    if not isinstance(numero, int):
        return False
    if numero < 1 or numero > 1000:
        return False
    return True

def is_valid_prodotto_id(self, prod_id):
    if not isinstance(prod_id, int) or prod_id < 1:
        return False
    return True
```

---

## 🐛 Debug e Logging

### 1. **Debug Print Utility**

```python
# debug_utils.py
def print_ordine_debug(ordine):
    print(f"\n=== DEBUG ORDINE ===")
    print(f"ID: {ordine.id_ordine}")
    print(f"Tavolo: {ordine.id_tavolo}")
    print(f"Stato: {ordine.stato.value}")
    print(f"Righe: {len(ordine.righe)}")
    for i, riga in enumerate(ordine.righe):
        print(f"  [{i}] {riga.quantita}x {riga.prodotto.nome} = €{riga.get_subtotale():.2f}")
    print(f"Totale: €{ordine.get_totale():.2f}")
    print(f"Data creazione: {ordine.data_creazione}")
    print("================\n")
```

---

### 2. **Profiling delle Prestazioni**

```python
import cProfile
import pstats
from io import StringIO

def profile_operazione():
    pr = cProfile.Profile()
    pr.enable()
    
    # ... codice da profilare ...
    gestione = GestioneOrdini()
    for i in range(100):
        gestione.occupa_tavolo(1)
    
    pr.disable()
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    print(s.getvalue())
```

---

## ❓ FAQ

### P: Posso usare il programma in remoto?

**R:** Sì, con accorgimenti:
```python
# Per accesso remoto via SSH
ssh -L 5432:localhost:5432 user@server

# Per database remoto su rete
db = DatabaseOrdini("/mnt/network_share/ristorante.db")
```

---

### P: Come integro un lettore di codici a barre?

**R:** Ascolta l'evento tastiera:
```python
from PyQt5.QtCore import Qt

class InterfacciaOrdini(QMainWindow):
    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            codice = event.text()
            self.processa_codice_barre(codice)
        super().keyPressEvent(event)
    
    def processa_codice_barre(self, codice):
        # Cerca il prodotto per codice
        prodotto = self.trova_prodotto_per_codice(codice)
        if prodotto:
            self.aggiungi_prodotto_ordine(prodotto)
```

---

### P: Come stampo gli scontrini?

**R:** Usa la libreria `reportlab`:
```bash
pip install reportlab
```

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def stampa_scontrino(ordine):
    c = canvas.Canvas("scontrino.pdf", pagesize=letter)
    y = 750
    
    c.drawString(100, y, f"Ordine #{ordine.id_ordine}")
    y -= 20
    c.drawString(100, y, f"Tavolo {ordine.id_tavolo}")
    y -= 40
    
    for riga in ordine.righe:
        c.drawString(100, y, f"{riga.quantita}x {riga.prodotto.nome}")
        c.drawString(400, y, f"€{riga.get_subtotale():.2f}")
        y -= 20
    
    y -= 20
    c.drawString(100, y, f"TOTALE: €{ordine.get_totale():.2f}")
    
    c.save()
```

---

### P: Come sincronizziamo più dispositivi?

**R:** Usa un server centrale:
```python
# server.py (con Flask)
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/ordini/salva', methods=['POST'])
def salva_ordine_remoto():
    data = request.json
    # Salva in database centrale
    ordine = Ordine.from_dict(data)
    db.salva_ordine(ordine)
    return jsonify({'success': True, 'id': ordine.id_ordine})
```

---

## 💡 Tips e Trucchi

### 1. **Shortcut da Tastiera**

```python
# Aggiungi shortcut nell'interfaccia
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

class InterfacciaOrdini(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Salva con Ctrl+S
        QShortcut(QKeySequence.Save, self, self.salva_ordine_attivo)
        
        # Cancella con Ctrl+D
        QShortcut(QKeySequence("Ctrl+D"), self, self.rimuovi_riga_ordine)
        
        # Print con Ctrl+P
        QShortcut(QKeySequence.Print, self, self.stampa_scontrino)
```

---

### 2. **Temi Scuri e Chiari**

```python
def attiva_tema_scuro(self):
    self.setStyleSheet("""
        QMainWindow { background-color: #2b2b2b; }
        QLabel { color: #ffffff; }
        QPushButton { background-color: #404040; color: #ffffff; }
    """)

def attiva_tema_chiaro(self):
    self.setStyleSheet("""
        QMainWindow { background-color: #ffffff; }
        QLabel { color: #000000; }
        QPushButton { background-color: #3498db; color: #ffffff; }
    """)
```

---

### 3. **Audio Feedback**

```python
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

class InterfacciaOrdini(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
    
    def riproduci_beep(self):
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile('beep.wav')))
        self.player.play()
    
    def aggiungi_prodotto_ordine(self, prodotto, row):
        # ... aggiungi logica ...
        self.riproduci_beep()  # Feedback audio
```

---

### 4. **Statistiche Real-time**

```python
from PyQt5.QtCore import QTimer

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.aggiorna_statistiche)
        self.timer.start(5000)  # Aggiorna ogni 5 secondi
    
    def aggiorna_statistiche(self):
        stats = self.gestione.get_statistiche()
        self.label_revenue.setText(f"€{stats['revenue_totale']:.2f}")
        self.label_occupazione.setText(f"{stats['tavoli_occupati']}/{stats['tavoli_totali']}")
```

---

### 5. **Export in Tempo Reale**

```python
def export_csv_continuo(self):
    import csv
    
    ordini = self.db.get_ordini_per_stato(StatoOrdine.PAGATO)
    
    with open(f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Tavolo', 'Totale', 'Articoli', 'Ora'])
        
        for ordine in ordini:
            writer.writerow([
                ordine.id_ordine,
                ordine.id_tavolo,
                f"{ordine.get_totale():.2f}",
                ordine.get_numero_articoli(),
                ordine.data_creazione.strftime("%H:%M:%S")
            ])
```

---

## 🚀 Conclusione

Seguendo queste guide, riuscirai a:
- ✅ Risolvere rapidamente i problemi comuni
- ✅ Implementare best practices nel codice
- ✅ Ottimizzare le prestazioni
- ✅ Proteggere i dati
- ✅ Debuggare efficacemente
- ✅ Aggiungere funzionalità avanzate

**Buona programmazione!** 🎉