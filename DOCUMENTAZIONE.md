# Gestione Ordini Ristorante - Documentazione Completa

## 📋 Panoramica del Progetto

Un sistema completo per la gestione degli ordini di ristoranti e bar, sviluppato in Python con interfaccia grafica PyQt5. Il programma è ottimizzato per l'uso su tablet con pulsanti grandi e interfaccia intuitiva per i camerieri.

### Caratteristiche Principali:
- ✅ Gestione simultanea di più tavoli
- ✅ Menu organizzato per categorie
- ✅ Aggiunta/modifica/rimozione prodotti dagli ordini
- ✅ Calcolo automatico totali
- ✅ Gestione stati ordini (In sospeso, In preparazione, Servito, Pagato)
- ✅ Database SQLite per persistenza dati
- ✅ Interfaccia responsive per tablet
- ✅ Interfaccia italiana e intuitiva

---

## 🏗️ Struttura del Progetto

```
ristorante-ordini/
├── modelli.py              # Classi base (Prodotto, Ordine, Tavolo)
├── database.py             # Gestione database SQLite
├── gestione_ordini.py      # Logica di business
├── interfaccia_grafica.py  # Interfaccia PyQt5
├── setup_database.py       # Script inizializzazione
├── ristorante_ordini.db    # Database (creato automaticamente)
└── README.md               # Questo file
```

---

## 🔧 Installazione e Setup

### Prerequisiti:
```bash
Python 3.7+
PyQt5 5.0+
```

### Installazione dipendenze:
```bash
pip install PyQt5
```

### Inizializzazione database:
```bash
# Esegui una volta per creare il database con menu di esempio
python setup_database.py
```

### Avvio applicazione:
```bash
python interfaccia_grafica.py
```

---

## 📚 Struttura delle Classi

### 1. Prodotto (`modelli.py`)
Rappresenta un prodotto del menu.

```python
class Prodotto:
    def __init__(self, id_prodotto, nome, categoria, prezzo, descrizione=""):
        self.id_prodotto      # ID univoco
        self.nome             # Nome prodotto
        self.categoria        # Categoria (bevande, antipasti, etc.)
        self.prezzo           # Prezzo in euro
        self.descrizione      # Descrizione opzionale
```

**Metodi principali:**
- `to_dict()` - Converte in dizionario

---

### 2. RigaOrdine (`modelli.py`)
Rappresenta una riga di un ordine (prodotto + quantità).

```python
class RigaOrdine:
    def __init__(self, prodotto, quantita=1, note=""):
        self.prodotto         # Oggetto Prodotto
        self.quantita         # Quantità ordinata
        self.note             # Note (senza peperoncino, etc.)
```

**Metodi principali:**
- `get_subtotale()` - Calcola prezzo * quantità

---

### 3. Ordine (`modelli.py`)
Rappresenta un ordine di un tavolo.

```python
class Ordine:
    def __init__(self, id_tavolo):
        self.id_ordine        # ID univoco
        self.id_tavolo        # Numero tavolo
        self.righe            # Lista di RigaOrdine
        self.stato            # StatoOrdine (enum)
        self.data_creazione   # Timestamp
        self.data_modifica    # Timestamp
```

**Metodi principali:**
- `aggiungi_prodotto(prodotto, quantita, note)` - Aggiunge un prodotto
- `rimuovi_prodotto(indice)` - Rimuove un prodotto
- `modifica_quantita(indice, nuova_quantita)` - Modifica quantità
- `get_totale()` - Calcola il totale
- `get_numero_articoli()` - Numero totale articoli
- `cambia_stato(nuovo_stato)` - Cambia lo stato
- `is_vuoto()` - Verifica se ordine vuoto

---

### 4. Tavolo (`modelli.py`)
Rappresenta un tavolo del ristorante.

```python
class Tavolo:
    def __init__(self, numero_tavolo, posti=4):
        self.numero_tavolo    # Numero identificativo
        self.posti            # Numero di posti
        self.ordine_attivo    # Ordine corrente
        self.occupato         # Flag stato
```

**Metodi principali:**
- `crea_nuovo_ordine()` - Crea nuovo ordine
- `chiudi_ordine()` - Chiude ordine e libera tavolo
- `get_info()` - Restituisce info tavolo

---

### 5. DatabaseOrdini (`database.py`)
Gestisce tutte le operazioni sul database SQLite.

```python
class DatabaseOrdini:
    def __init__(self, nome_db="ristorante_ordini.db"):
        # Inizializza connessione e crea tabelle
```

**Metodi principali:**
- `aggiungi_prodotto(prodotto)` - Aggiunge prodotto
- `get_tutti_prodotti()` - Recupera tutti i prodotti
- `get_prodotti_per_categoria(categoria)` - Filtra per categoria
- `salva_ordine(ordine)` - Salva ordine nuovo
- `aggiorna_ordine(ordine)` - Aggiorna ordine esistente
- `get_ordine(id)` - Recupera ordine
- `get_ordini_per_stato(stato)` - Filtra per stato
- `chiudi_ordine(id)` - Marca ordine come pagato
- `elimina_ordine(id)` - Elimina ordine

---

### 6. GestioneOrdini (`gestione_ordini.py`)
Gestisce la logica di business e orchestrazione.

```python
class GestioneOrdini:
    def __init__(self, numero_tavoli=10, database="ristorante_ordini.db"):
        self.tavoli           # Dict di Tavolo
        self.db               # Istanza DatabaseOrdini
```

**Metodi principali:**
- `get_tavolo(numero)` - Recupera tavolo
- `get_tutti_tavoli()` - Lista tavoli
- `get_tavoli_occupati()` - Tavoli con ordini attivi
- `occupa_tavolo(numero)` - Crea nuovo ordine
- `libera_tavolo(numero)` - Chiude ordine e libera
- `get_ordine_attivo(numero)` - Ordine corrente tavolo
- `aggiungi_al_ordine(numero, prodotto, quantita, note)` - Aggiungi item
- `cambia_stato_ordine(numero, stato)` - Cambia stato
- `salva_ordine_attivo(numero)` - Salva nel DB

---

### 7. InterfacciaOrdini (`interfaccia_grafica.py`)
Interfaccia grafica PyQt5 ottimizzata per tablet.

**Layout principale:**
- **Sinistra:** Panel tavoli con grid di pulsanti
- **Centro:** Menu con tabella prodotti per categoria
- **Destra:** Ordine attivo con totale e controlli stati

**Sezioni:**
1. **Gestione Tavoli:** Occupa/Libera tavolo
2. **Visualizzazione Menu:** Categorie + Prodotti con quantità
3. **Ordine Attivo:** Tabella con modifica in tempo reale
4. **Controlli Stato:** Pulsanti per cambio stato ordine

---

## 💾 Schema Database SQLite

### Tabella: prodotti
```sql
CREATE TABLE prodotti (
    id_prodotto INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    categoria TEXT NOT NULL,
    prezzo REAL NOT NULL,
    descrizione TEXT,
    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Tabella: ordini
```sql
CREATE TABLE ordini (
    id_ordine INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tavolo INTEGER NOT NULL,
    stato TEXT NOT NULL DEFAULT 'In sospeso',
    totale REAL DEFAULT 0,
    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_chiusura TIMESTAMP
)
```

### Tabella: righe_ordini
```sql
CREATE TABLE righe_ordini (
    id_riga INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ordine INTEGER NOT NULL,
    id_prodotto INTEGER NOT NULL,
    quantita INTEGER NOT NULL,
    prezzo_unitario REAL NOT NULL,
    note TEXT,
    FOREIGN KEY (id_ordine) REFERENCES ordini(id_ordine),
    FOREIGN KEY (id_prodotto) REFERENCES prodotti(id_prodotto)
)
```

---

## 🚀 Guida Utente - Uso dell'Interfaccia

### 1. Avvio Applicazione
```bash
python interfaccia_grafica.py
```

### 2. Gestione Tavoli

#### Occupare un tavolo:
1. Seleziona il tavolo dal panel sinistro (si evidenzierà in verde)
2. Clicca "Occupa Tavolo"
3. Il tavolo è ora pronto per un ordine

#### Liberare un tavolo:
1. Seleziona il tavolo occupato
2. Clicca "Libera Tavolo"
3. Conferma per completare

### 3. Aggiungere Prodotti all'Ordine

1. Seleziona il **Tavolo** dal panel sinistro
2. Seleziona la **Categoria** dal menu a dropdown (Bevande, Antipasti, etc.)
3. Scegli la **Quantità** nel campo spinbox
4. Clicca **"Aggiungi"** per aggiungere all'ordine

### 4. Modificare un Ordine

#### Cambiare quantità:
- Clicca sullo spinbox nella colonna "Qtà" della tabella ordine
- Modifica il valore direttamente
- La quantità si aggiorna in tempo reale

#### Rimuovere un articolo:
- Clicca "Rimuovi" nella riga dell'articolo
- L'articolo viene rimosso istantaneamente

### 5. Gestire gli Stati dell'Ordine

Dopo aver aggiunto i prodotti, puoi cambiare lo stato:

- **"In Preparazione"** - L'ordine è stato inviato in cucina
- **"Servito"** - Il piatto è stato servito al tavolo
- **"Pagato"** - L'ordine è stato pagato e chiuso

Clicca il pulsante corrispondente per cambiare stato.

---

## 📊 Esempio di Utilizzo

### Scenario: Servire un tavolo

```
1. Cameriere seleziona Tavolo 3
2. Clicca "Occupa Tavolo"
3. Seleziona categoria "Bevande"
4. Aggiunge: 2x Coca Cola, 1x Prosecco
5. Seleziona categoria "Primi"
6. Aggiunge: 2x Spaghetti alla carbonara, 1x Risotto ai funghi
7. Clicca "In Preparazione" per inviare in cucina
8. Dopo preparazione: Clicca "Servito"
9. Dopo pagamento: Clicca "Pagato"
10. Clicca "Libera Tavolo" per liberare il tavolo 3
```

---

## 🔍 Personalizzazione

### Aggiungere Nuovi Prodotti

#### Metodo 1: Programmaticamente
```python
from modelli import Prodotto
from gestione_ordini import GestioneOrdini

gestione = GestioneOrdini()
prodotto = Prodotto(
    id_prodotto=31,
    nome="Pizza Margherita",
    categoria="Piatti Speciali",
    prezzo=8.00,
    descrizione="Con mozzarella fresca"
)
gestione.aggiungi_prodotto_menu(prodotto)
```

#### Metodo 2: Direttamente nel database
```bash
sqlite3 ristorante_ordini.db
INSERT INTO prodotti (id_prodotto, nome, categoria, prezzo, descrizione)
VALUES (31, 'Pizza Margherita', 'Piatti Speciali', 8.00, 'Con mozzarella fresca');
```

### Configurare il Numero di Tavoli

Nel file `interfaccia_grafica.py`, modifica:
```python
finestra = InterfacciaOrdini(numero_tavoli=20)  # Cambia numero tavoli
```

### Personalizzare i Colori

Modifica la sezione `configura_stili()` in `InterfacciaOrdini`:
```python
QPushButton {
    background-color: #3498db;  # Colore principale
    ...
}
```

---

## ⚙️ Configurazione Avanzata

### Connessione Remota Database

Se vuoi usare un database SQLite su rete:
```python
import shutil
# Copia il database su server remoto
shutil.copy('ristorante_ordini.db', '/path/to/network/drive/')
```

### Export Dati

Per esportare gli ordini in CSV:
```python
import csv
from database import DatabaseOrdini

db = DatabaseOrdini()
ordini = db.get_ordini_per_stato(StatoOrdine.PAGATO)

with open('ordini_export.csv', 'w') as f:
    writer = csv.writer(f)
    for ordine in ordini:
        writer.writerow([ordine.id_ordine, ordine.id_tavolo, ordine.get_totale()])
```

---

## 🐛 Troubleshooting

### Errore: "ModuleNotFoundError: No module named 'PyQt5'"
```bash
pip install PyQt5
```

### Database non si crea
Assicurati di avere i permessi di scrittura nella directory:
```bash
python setup_database.py
```

### Ordini non si salvano
Verifica che il database non sia corrotto:
```bash
sqlite3 ristorante_ordini.db "VACUUM;"
```

### Interfaccia non responsive su tablet
Modifica le dimensioni dei font in `configura_stili()`:
```python
QPushButton {
    font-size: 18px;  # Aumenta la dimensione
    min-height: 80px; # Aumenta altezza pulsanti
}
```

---

## 📈 Statistiche e Reporting

### Ottenere statistiche generali:
```python
from gestione_ordini import GestioneOrdini

gestione = GestioneOrdini()
stats = gestione.get_statistiche()

print(f"Tavoli occupati: {stats['tavoli_occupati']}")
print(f"Ordini in preparazione: {stats['ordini_in_preparazione']}")
print(f"Ricavi totali: €{stats['revenue_totale']:.2f}")
```

---

## 🔐 Sicurezza

- I dati sono salvati in SQLite locale
- Esegui backup regolari:
```bash
cp ristorante_ordini.db ristorante_ordini.backup.db
```

---

## 📞 Support e Miglioramenti Futuri

### Possibili estensioni:
- [ ] Sistema di login camerieri
- [ ] Stampa ricevute
- [ ] Integrazione con cassa
- [ ] Dashboard manager
- [ ] Statistiche vendite
- [ ] Sincronizzazione multi-device
- [ ] App mobile
- [ ] Pagamenti digitali integrati

---

## 📄 Licenza

Questo progetto è fornito come template educativo e può essere liberamente modificato e distribuito.

---

## 👨‍💻 Autore

Programma di gestione ordini ristorante sviluppato in Python con PyQt5.

**Data creazione:** 2024
**Versione:** 1.0

---

## ✅ Checklist di Setup

- [ ] Installare Python 3.7+
- [ ] Installare PyQt5: `pip install PyQt5`
- [ ] Eseguire setup_database.py
- [ ] Avviare interfaccia_grafica.py
- [ ] Testare aggiunta prodotto
- [ ] Testare cambio stato ordine
- [ ] Testare salvataggio database
- [ ] Personalizzare menu con propri prodotti

---

**Buon utilizzo! 🚀**