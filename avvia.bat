@echo off
REM avvia.bat - Script di avvio per Windows
REM Clicca due volte su questo file per avviare l'applicazione

echo.
echo ============================================================
echo      GESTIONE ORDINI RISTORANTE - AVVIO
echo ============================================================
echo.

REM Elimina cache Python
echo [1/5] Pulizia cache...
if exist __pycache__ (
    rmdir /s /q __pycache__
    echo  OK: Cache eliminata
) else (
    echo  OK: Nessuna cache trovata
)

REM Installa PyQt5 se necessario
echo [2/5] Verifica PyQt5...
python -c "from PyQt5.QtWidgets import QApplication" 2>nul
if errorlevel 1 (
    echo  INSTALLAZIONE: PyQt5 non trovato, installing...
    pip install PyQt5
) else (
    echo  OK: PyQt5 trovato
)

REM Verifica moduli
echo [3/5] Verifica moduli...
python -c "from modelli import Prodotto" 2>nul
if errorlevel 1 (
    echo  ERRORE: modelli.py non è leggibile
    echo  Soluzione: scarica di nuovo i file
    pause
    exit /b 1
) else (
    echo  OK: modelli.py OK
)

REM Crea database se non esiste
echo [4/5] Preparazione database...
if not exist ristorante_ordini.db (
    echo  CREAZIONE: Database nuovo...
    python setup_database.py
    echo  OK: Database creato
) else (
    echo  OK: Database già presente
)

REM Avvia applicazione
echo [5/5] Avvio interfaccia...
echo.
echo ============================================================
python interfaccia_grafica.py

if errorlevel 1 (
    echo.
    echo ERRORE: Applicazione non avviata correttamente
    pause
)