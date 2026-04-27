# 🍽️ Gestione Ordini Ristorante

Sistema completo per la gestione degli ordini di ristoranti e bar con interfaccia grafica PyQt5 ottimizzata per tablet.

## ⚡ Quick Start

### 1. Installazione
```bash
pip install PyQt5
```

### 2. Setup Database con Menu di Esempio
```bash
python setup_database.py
```

### 3. Avvia l'Applicazione
```bash
python interfaccia_grafica.py
```

## 📁 File Principali

| File | Descrizione |
|------|-------------|
| `modelli.py` | Classi base (Prodotto, Ordine, Tavolo) |
| `database.py` | Gestione database SQLite |
| `gestione_ordini.py` | Logica di business |
| `interfaccia_grafica.py` | Interfaccia PyQt5 |
| `setup_database.py` | Inizializzazione menu |
| `DOCUMENTAZIONE.md` | Documentazione completa |

## 🎯 Caratteristiche

✅ Gestione simultanea di 10+ tavoli  
✅ Menu organizzato per categorie  
✅ Aggiunta/modifica/rimozione prodotti  
✅ Calcolo automatico totali  
✅ 5 stati ordini diversi  
✅ Database SQLite persistente  
✅ Interfaccia responsive per tablet  
✅ Interfaccia in italiano  

## 🖼️ Layout Interfaccia

```
┌─────────────────────────────────────────────────────┐
│         GESTIONE ORDINI RISTORANTE                 │
├──────────────┬──────────────┬──────────────────────┤
│   TAVOLI     │    MENU      │   ORDINE ATTIVO     │
│              │              │                      │
│ [Tavolo 1]   │ Categoria ▼  │ Tavolo 1 - €50.00   │
│ [Tavolo 2]   │              │ ┌────────────────┐  │
│ [Tavolo 3]   │ Prodotto1 €5 │ │Prodotto │Qtà  │  │
│ [Tavolo 4]   │ + Aggiungi   │ │Prodotto │Qtà  │  │
│              │              │ │                │  │
│ Occupa ┐     │ Prodotto2 €7 │ │ TOTALE: €50   │  │
│ Libera │     │ + Aggiungi   │ │                │  │
│        └     │              │ │[Preparazione]  │  │
│              │              │ │[Servito]       │  │
│              │              │ │[Pagato]        │  │
└──────────────┴──────────────┴──────────────────────┘
```

## 🗄️ Schema Database

### Tabelle SQLite:
- `prodotti` - Catalogo menu
- `ordini` - Ordini tavoli
- `righe_ordini` - Items negli ordini

## 💡 Uso Base

### 1. Occupare un tavolo
```
1. Clicca tavolo nel panel sinistro
2. Clicca "Occupa Tavolo"
```

### 2. Aggiungere prodotti
```
1. Seleziona categoria dal dropdown
2. Scegli quantità
3. Clicca "Aggiungi"
```

### 3. Chiudere ordine
```
1. Clicca "In Preparazione" (invia in cucina)
2. Clicca "Servito" (servi al tavolo)
3. Clicca "Pagato" (chiudi ordine)
4. Clicca "Libera Tavolo"
```

## 🔧 Personalizzazione

### Cambia numero tavoli
In `interfaccia_grafica.py`:
```python
finestra = InterfacciaOrdini(numero_tavoli=15)
```

### Aggiungi prodotto al menu
```python
from modelli import Prodotto
from gestione_ordini import GestioneOrdini

gestione = GestioneOrdini()
pizza = Prodotto(31, "Pizza Margherita", "Piatti Speciali", 8.00)
gestione.aggiungi_prodotto_menu(pizza)
```

## 📊 Menu di Esempio

Il database viene precompilato con 30 prodotti:

**Bevande** (8)  
- Acqua, Coca Cola, Birra, Prosecco, Caffè, etc.

**Antipasti** (5)  
- Bruschette, Affettati, Formaggi, Calamari, etc.

**Primi** (6)  
- Carbonara, Risotto, Penne, Lasagna, Gnocchi, etc.

**Secondi** (6)  
- Branzino, Tagliata, Ossobuco, Pollo, etc.

**Dolci** (5)  
- Tiramisu, Panna Cotta, Gelato, etc.

## ⚙️ Requisiti Sistema

- Python 3.7+
- PyQt5 5.0+
- 50 MB spazio disco
- Monitor tablet o PC

## 📱 Uso su Tablet

L'interfaccia è ottimizzata per tablet:
- Pulsanti grandi (80px di altezza)
- Layout responsive
- Touch-friendly
- Supporta landscape e portrait

## 🚀 Funzionalità Avanzate

### Export Dati
```python
from database import DatabaseOrdini
from modelli import StatoOrdine

db = DatabaseOrdini()
ordini_pagati = db.get_ordini_per_stato(StatoOrdine.PAGATO)
```

### Statistiche
```python
stats = gestione.get_statistiche()
print(f"Tavoli occupati: {stats['tavoli_occupati']}")
print(f"Ricavi: €{stats['revenue_totale']}")
```

## 🔒 Backup Database

```bash
cp ristorante_ordini.db ristorante_ordini.backup.db
```

## 🐛 Troubleshooting

| Errore | Soluzione |
|--------|-----------|
| `ModuleNotFoundError: PyQt5` | `pip install PyQt5` |
| Database non si crea | `python setup_database.py` |
| Interfaccia piccola su tablet | Aumenta font in `configura_stili()` |

## 📖 Documentazione Completa

Vedi `DOCUMENTAZIONE.md` per:
- Struttura classi dettagliata
- Schema database completo
- Guida utente approfondita
- Guide personalizzazione
- Esempi avanzati
- API reference

## 🎓 Struttura Progetto Educativo

Perfetto per imparare:
- Programmazione OOP in Python
- Design patterns (MVC, DAO)
- SQLite e database relazionali
- GUI con PyQt5
- Architettura software

## 📈 Prossimi Step

Possibili estensioni:
- [ ] Sistema login camerieri
- [ ] Stampa ricevute
- [ ] Dashboard vendite
- [ ] App mobile
- [ ] Sincronizzazione multi-device
- [ ] Integrazione cassa
- [ ] Analytics

## 📞 Support

Per problemi o suggerimenti:
1. Controlla DOCUMENTAZIONE.md
2. Verifica il database: `sqlite3 ristorante_ordini.db ".tables"`
3. Controlla i log della console

## 📄 Licenza

Free to use and modify

---

**Versione:** 1.0  
**Ultimo aggiornamento:** 2024  
**Python:** 3.7+  
**Status:** ✅ Pronto per produzione

Buon utilizzo! 🍽️✨