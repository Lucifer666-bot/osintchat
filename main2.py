#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSINTChat – busca pública por número de telefone
"""
import os, sys, json, csv, time, re, argparse, subprocess, tempfile, shutil
from datetime import datetime
from pathlib import Path

import phonenumbers
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------- CONFIGURAÇÕES ----------
NUMVERIFY_KEY = os.getenv("NUMVERIFY_KEY", "SEU_TOKEN_AQUI")
BREACH_KEY    = os.getenv("BREACH_KEY", "SEU_TOKEN_AQUI")
OUTPUT_DIR    = Path("resultados")
LOG_FILE      = OUTPUT_DIR / "log.txt"
CSV_FILE      = OUTPUT_DIR / "dados.csv"
JSON_FILE     = OUTPUT_DIR / "dados.json"
SCREEN_DIR    = OUTPUT_DIR / "screenshots"

# ---------- FUNÇÕES AUXILIARES ----------
def log(msg):
    LOG_FILE.parent.mkdir(exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} - {msg}\n")
    print(msg)

def salvar_json(data):
    OUTPUT_DIR.mkdir(exist_ok=True)
    with JSON_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def salvar_csv(linha):
    OUTPUT_DIR.mkdir(exist_ok=True)
    file_exists = CSV_FILE.exists()
    with CSV_FILE.open("a", newline='', encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=linha.keys())
        if not file_exists:
            w.writeheader()
        w.writerow(linha)

def screenshot(url, nome):
    SCREEN_DIR.mkdir(exist_ok=True)
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--window-size=1280,720")
    driver = webdriver.Chrome(options=chrome_opts)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        driver.save_screenshot(str(SCREEN_DIR / f"{nome}.png"))
    finally:
        driver.quit()

# ---------- VALIDAÇÃO DO NÚMERO ----------
def parse_num(raw):
    try:
        num = phonenumbers.parse(raw, None)
        if not phonenumbers.is_valid_number(num):
            raise ValueError
        return {
            "e164": phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164),
            "international": phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "country_code": num.country_code,
            "national_number": str(num.national_number),
            "region": phonenumbers.region_code_for_number(num)
        }
    except Exception as e:
        log(f"Número inválido: {e}")
        sys.exit(1)

# ---------- CONSULTAS ----------
def numverify_lookup(num):
    if NUMVERIFY_KEY == "SEU_TOKEN_AQUI":
        return {}
    url = f"http://apilayer.net/api/validate?access_key={NUMVERIFY_KEY}&number={num['e164']}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.json()
    return {}

def breach_lookup(num):
    if BREACH_KEY == "SEU_TOKEN_AQUI":
        return []
    url = f"https://breachdirectory.p.rapidapi.com/"
    headers = {"X-RapidAPI-Key": BREACH_KEY}
    params = {"func": "auto", "term": num["e164"]}
    r = requests.get(url, headers=headers, params=params, timeout=10)
    if r.status_code == 200:
        return r.json().get("result", [])
    return []

def google_dork(num):
    query = f'"{num["e164"]}" OR "{num["national_number"]}"'
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    return url

def whatsapp_url(num):
    return f"https://wa.me/{num['e164'][1:]}"

# ---------- PIPELINE ----------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("numero", help="Número com DDI, ex: +5511999999999")
    args = parser.parse_args()

    log("Iniciando OSINTChat")
    num = parse_num(args.numero)
    log(f"Alvo: {num['international']} ({num['region']})")

    data = {"numero": num, "timestamp": str(datetime.now())}

    # NumVerify
    log("Consultando NumVerify...")
    data["numverify"] = numverify_lookup(num)

    # Breaches
    log("Buscando breaches...")
    data["breaches"] = breach_lookup(num)

    # URLs úteis
    data["urls"] = {
        "google_dork": google_dork(num),
        "whatsapp": whatsapp_url(num)
    }

    # Screenshots
    log("Capturando screenshots...")
    screenshot(data["urls"]["google_dork"], "google")
    screenshot(data["urls"]["whatsapp"], "whatsapp")

    # Salvamento
    salvar_json(data)
    salvar_csv({
        "numero": num["e164"],
        "pais": num["region"],
        "carrier": data["numverify"].get("carrier", ""),
        "line_type": data["numverify"].get("line_type", ""),
        "breaches": len(data["breaches"]),
        "screenshots": 2
    })

    log("Concluído. Arquivos salvos em 'resultados/'")

if __name__ == "__main__":
    main()
