#!/usr/bin/env python3
"""
seed_data.py — Generate realistic multi-country banking customer data for CustIQ 360°.

Covers 90 customers across 11 countries (APAC, SEPA, EMEA, South Asia).
All monetary amounts are stored as INR equivalents (local_amount * inr_rate).

Usage:
    python seed_data.py

Outputs:
    customers.json  (in the same directory as this script)
"""

from __future__ import annotations

import json
import os
import random
import string
from collections import Counter
from datetime import date, timedelta

from faker import Faker

# India-specific Faker instance for Indian names only
fake_in = Faker("en_IN")
random.seed(42)

# ── Output path ───────────────────────────────────────────────────────────────

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "customers.json")

# ── Currency conversion rates (1 unit of local = X INR) ──────────────────────

INR_RATES = {
    "INR": 1.0,
    "SGD": 62.5,
    "AED": 22.7,
    "GBP": 105.3,
    "EUR": 90.9,
    "JPY": 0.562,
    "AUD": 52.6,
    "MYR": 17.9,
    "HKD": 10.6,
    "SAR": 22.2,
    "ZAR": 4.5,
}

# ── Country configuration ─────────────────────────────────────────────────────

COUNTRY_CONFIG = {
    "IN": {
        "country_name": "India",
        "region": "South Asia",
        "currency": "INR",
        "phone_prefix": "+91",
        "cities": [
            "Andheri West", "BKC", "Connaught Place", "MG Road Bangalore",
            "Anna Nagar Chennai", "Salt Lake Kolkata", "Hitech City Hyderabad",
            "Viman Nagar Pune", "Navrangpura Ahmedabad",
        ],
        "names": None,  # Use Faker("en_IN")
        "occupations": [
            "Software Engineer", "Chartered Accountant", "IAS Officer", "Entrepreneur",
            "Doctor", "Teacher", "Business Owner", "Investment Banker", "Architect", "Journalist",
        ],
        "loan_types": ["Home Loan", "Personal Loan", "Car Loan", "Education Loan"],
        "wealth_types": ["Fixed Deposit", "Mutual Fund", "Insurance", "PPF"],
        "account_types": ["Savings", "Savings", "Savings", "Current", "NRI"],
        "txn_debit": [
            "ATM Withdrawal", "NEFT Transfer", "UPI Payment", "Electricity Bill",
            "Loan EMI Debit", "GST Payment",
        ],
        "txn_credit": [
            "Salary Credit", "Dividend Credit", "NEFT Received", "UPI Received",
            "Interest Credit", "Bonus Credit",
        ],
        "kyc_docs": {
            "aadhaar_type": "Aadhaar",
            "pan_type": "PAN",
            "address_types": ["Passport", "Voter ID", "Driving Licence"],
        },
        "salary_range": (360000, 5000000),
        "balance_range": (50000, 2500000),
        "home_loan_range": (2000000, 15000000),
        "personal_loan_range": (100000, 1500000),
        "car_loan_range": (300000, 2000000),
        "fd_range": (25000, 5000000),
        "home_loan_label": "Home Loan",
        "personal_loan_label": "Personal Loan",
        "car_loan_label": "Car Loan",
        "edu_loan_label": "Education Loan",
        "home_loan_rate": (7.5, 9.5),
        "personal_loan_rate": (10.5, 16.0),
        "car_loan_rate": (8.5, 11.5),
        "edu_loan_rate": (9.0, 13.0),
    },
    "SG": {
        "country_name": "Singapore",
        "region": "APAC",
        "currency": "SGD",
        "phone_prefix": "+65",
        "cities": [
            "Marina Bay", "Orchard Road", "Jurong East", "Tampines",
            "Woodlands", "Raffles Place", "Bugis",
        ],
        "names": [
            "Li Wei", "Chen Hui Ling", "Ahmad Fauzi bin Rashid", "Siti Noorhaiza",
            "Rajesh Kumar Pillai", "Priya Subramaniam", "David Tan Kok Wei",
            "Lim Mei Xian", "Arjun Nair", "Nurul Ain Binte Mohamed",
        ],
        "occupations": [
            "Finance Analyst", "Tech Lead", "Civil Servant", "Private Banker",
            "Entrepreneur", "Doctor", "Regional Director", "Asset Manager",
        ],
        "loan_types": [
            "HDB Home Loan", "Private Property Loan", "Car Loan", "Personal Loan",
        ],
        "wealth_types": [
            "Fixed Deposit", "Unit Trust", "Endowment Insurance", "CPF Investment",
        ],
        "account_types": ["Savings", "Savings", "Current", "NRI"],
        "txn_debit": [
            "PayNow Transfer", "GIRO Deduction", "ATM Withdrawal",
            "NETS Payment", "CPF Deduction",
        ],
        "txn_credit": [
            "SAP Payroll", "SRS Contribution", "Interest Credit",
            "Dividend Credit", "Bonus Credit",
        ],
        "kyc_docs": {
            "aadhaar_type": "NRIC/FIN",
            "pan_type": "SingPass ID",
            "address_types": ["Utility Bill/Lease"],
        },
        "salary_range": (50000, 500000),
        "balance_range": (10000, 300000),
        "home_loan_range": (300000, 1500000),
        "personal_loan_range": (10000, 150000),
        "car_loan_range": (40000, 200000),
        "fd_range": (10000, 500000),
        "home_loan_label": "HDB Home Loan",
        "personal_loan_label": "Personal Loan",
        "car_loan_label": "Car Loan",
        "edu_loan_label": "Personal Loan",
        "home_loan_rate": (2.5, 3.5),
        "personal_loan_rate": (3.5, 6.5),
        "car_loan_rate": (2.8, 4.5),
        "edu_loan_rate": (3.5, 5.5),
    },
    "AE": {
        "country_name": "United Arab Emirates",
        "region": "EMEA",
        "currency": "AED",
        "phone_prefix": "+971",
        "cities": [
            "DIFC Dubai", "Dubai Marina", "Downtown Dubai",
            "Abu Dhabi ADGM", "Sharjah City Centre", "Business Bay", "JLT",
        ],
        "names": [
            "Mohammed Al-Rashidi", "Fatima bint Al-Mansouri", "James Mitchell",
            "Priya Krishnan Al-Hamdan", "Khalid Ibrahim Al-Falasi", "Sarah Thompson",
            "Omar Abdullah Al-Nuaimi", "Aisha Al-Suwaidi", "Robert Clarke",
            "Meena Pillai",
        ],
        "occupations": [
            "Oil & Gas Executive", "Finance Manager", "Real Estate Developer",
            "Expatriate Professional", "Medical Specialist", "Business Owner",
            "Investment Director",
        ],
        "loan_types": [
            "Islamic Home Finance", "Auto Finance",
            "Personal Finance (Takaful)", "Business Finance",
        ],
        "wealth_types": [
            "Fixed Deposit", "Islamic Sukuk", "Takaful Insurance", "Gold Savings",
        ],
        "account_types": ["Savings", "Savings", "Current", "NRI"],
        "txn_debit": [
            "SWIFT Transfer", "ATM Cash", "Etisalat Bill",
            "DEWA Payment", "ADCB Bill Payment",
        ],
        "txn_credit": [
            "Salary WPS Credit", "Bonus Credit", "Interest Credit",
            "Dividend Credit", "SWIFT Received",
        ],
        "kyc_docs": {
            "aadhaar_type": "Emirates ID",
            "pan_type": "Residency Visa",
            "address_types": ["DEWA Bill/Lease Agreement"],
        },
        "salary_range": (100000, 2000000),
        "balance_range": (20000, 1000000),
        "home_loan_range": (500000, 5000000),
        "personal_loan_range": (20000, 300000),
        "car_loan_range": (50000, 300000),
        "fd_range": (20000, 1000000),
        "home_loan_label": "Islamic Home Finance",
        "personal_loan_label": "Personal Finance (Takaful)",
        "car_loan_label": "Auto Finance",
        "edu_loan_label": "Personal Finance (Takaful)",
        "home_loan_rate": (3.5, 5.5),
        "personal_loan_rate": (5.0, 8.0),
        "car_loan_rate": (3.5, 6.0),
        "edu_loan_rate": (4.5, 7.0),
    },
    "GB": {
        "country_name": "United Kingdom",
        "region": "EMEA",
        "currency": "GBP",
        "phone_prefix": "+44",
        "cities": [
            "London Canary Wharf", "London City", "Manchester Deansgate",
            "Birmingham Colmore", "Edinburgh St Andrew", "Leeds City", "Bristol Clifton",
        ],
        "names": [
            "James Richardson", "Emma Thompson", "Oliver Davies", "Sophie Williams",
            "William Clark", "Charlotte Evans", "Harry Wilson", "Amelia Brown",
            "Jack Taylor", "Isla Morrison",
        ],
        "occupations": [
            "Banker", "Barrister", "GP Doctor", "Software Architect",
            "University Lecturer", "Consultant", "Fund Manager", "Civil Servant",
        ],
        "loan_types": ["Mortgage", "Personal Loan", "Car Finance", "Student Loan"],
        "wealth_types": [
            "Fixed Deposit", "Stocks & Shares ISA", "Life Insurance", "Pension (SIPP)",
        ],
        "account_types": ["Savings", "Savings", "Current"],
        "txn_debit": [
            "Direct Debit", "Standing Order", "Faster Payment",
            "Council Tax", "Mortgage Payment",
        ],
        "txn_credit": [
            "Wages Credit", "BACS Transfer", "Interest Credit",
            "Dividend Credit", "Bonus Credit",
        ],
        "kyc_docs": {
            "aadhaar_type": "National Insurance Number",
            "pan_type": "Passport",
            "address_types": ["Council Tax Bill/Utility Bill"],
        },
        "salary_range": (30000, 300000),
        "balance_range": (5000, 200000),
        "home_loan_range": (150000, 800000),
        "personal_loan_range": (5000, 50000),
        "car_loan_range": (10000, 60000),
        "fd_range": (5000, 200000),
        "home_loan_label": "Mortgage",
        "personal_loan_label": "Personal Loan",
        "car_loan_label": "Car Finance",
        "edu_loan_label": "Student Loan",
        "home_loan_rate": (3.5, 5.5),
        "personal_loan_rate": (6.0, 12.0),
        "car_loan_rate": (4.5, 8.5),
        "edu_loan_rate": (4.5, 6.5),
    },
    "DE": {
        "country_name": "Germany",
        "region": "SEPA",
        "currency": "EUR",
        "phone_prefix": "+49",
        "cities": [
            "Frankfurt Bankenviertel", "Frankfurt Sachsenhausen", "Berlin Mitte",
            "Munich Maxvorstadt", "Hamburg HafenCity", "Düsseldorf Medienhafen",
        ],
        "names": [
            "Klaus Weber", "Sabine Müller", "Hans Fischer", "Petra Schmidt",
            "Andreas Hoffmann", "Ursula Becker", "Michael Wagner", "Elisabeth Schulz",
            "Wolfgang Braun", "Brigitte Zimmermann", "Dieter Koch", "Helga Schäfer",
            "Ralf Hartmann", "Monika Richter",
        ],
        "occupations": [
            "Mechanical Engineer", "Financial Controller", "University Professor",
            "Business Analyst", "Medical Doctor", "IT Architect", "Factory Manager",
        ],
        "loan_types": [
            "Immobilienkredit", "Ratenkredit", "Autokredit", "Studienkredit",
        ],
        "wealth_types": [
            "Festgeld", "Investmentfonds", "Lebensversicherung", "Riester-Rente",
        ],
        "account_types": ["Savings", "Current", "Current"],
        "txn_debit": [
            "SEPA Überweisung", "Lastschrift", "Miete",
            "Stromrechnung", "Steuerzahlung",
        ],
        "txn_credit": [
            "Gehaltseingang", "Dividende", "Zinsgutschrift",
            "Rückerstattung", "Bonus",
        ],
        "kyc_docs": {
            "aadhaar_type": "Personalausweis",
            "pan_type": "Steuer-ID",
            "address_types": ["Meldebescheinigung"],
        },
        "salary_range": (30000, 150000),
        "balance_range": (5000, 200000),
        "home_loan_range": (150000, 600000),
        "personal_loan_range": (5000, 50000),
        "car_loan_range": (10000, 60000),
        "fd_range": (5000, 200000),
        "home_loan_label": "Immobilienkredit",
        "personal_loan_label": "Ratenkredit",
        "car_loan_label": "Autokredit",
        "edu_loan_label": "Studienkredit",
        "home_loan_rate": (2.5, 4.5),
        "personal_loan_rate": (4.0, 9.0),
        "car_loan_rate": (3.0, 6.0),
        "edu_loan_rate": (3.5, 5.5),
    },
    "JP": {
        "country_name": "Japan",
        "region": "APAC",
        "currency": "JPY",
        "phone_prefix": "+81",
        "cities": [
            "Tokyo Shinjuku", "Tokyo Marunouchi", "Osaka Umeda",
            "Osaka Namba", "Nagoya Sakae", "Fukuoka Tenjin", "Sapporo Odori",
        ],
        "names": [
            "Tanaka Hiroshi", "Suzuki Yuki", "Sato Kenji", "Watanabe Akiko",
            "Ito Masashi", "Kobayashi Reiko", "Yamamoto Takuya",
            "Nakamura Haruka", "Hayashi Daisuke", "Kimura Naomi",
            "Matsumoto Ryota", "Inoue Sachiko",
        ],
        "occupations": [
            "Corporate Manager (Salaryman)", "Engineer", "Civil Servant",
            "Doctor", "Retail Business Owner", "University Researcher", "IT Manager",
        ],
        "loan_types": ["Housing Loan", "Personal Loan", "Car Loan", "Education Loan"],
        "wealth_types": [
            "Fixed Deposit (定期預金)", "Investment Trust", "Life Insurance", "iDeCo Pension",
        ],
        "account_types": ["Savings", "Savings", "Current"],
        "txn_debit": [
            "ATM引出し", "電気代", "家賃支払い",
            "税金", "振込手数料",
        ],
        "txn_credit": [
            "給与振込", "投資信託", "振込 (Bank Transfer)",
            "利息", "ボーナス",
        ],
        "kyc_docs": {
            "aadhaar_type": "My Number Card",
            "pan_type": "Residence Card",
            "address_types": ["Jūminhy/Utility Bill"],
        },
        "salary_range": (3000000, 20000000),
        "balance_range": (1000000, 50000000),
        "home_loan_range": (20000000, 100000000),
        "personal_loan_range": (500000, 5000000),
        "car_loan_range": (1000000, 8000000),
        "fd_range": (1000000, 30000000),
        "home_loan_label": "Housing Loan",
        "personal_loan_label": "Personal Loan",
        "car_loan_label": "Car Loan",
        "edu_loan_label": "Education Loan",
        "home_loan_rate": (0.5, 2.0),
        "personal_loan_rate": (3.0, 8.0),
        "car_loan_rate": (1.5, 4.0),
        "edu_loan_rate": (1.0, 3.5),
    },
    "AU": {
        "country_name": "Australia",
        "region": "APAC",
        "currency": "AUD",
        "phone_prefix": "+61",
        "cities": [
            "Sydney CBD", "Sydney Chatswood", "Melbourne Collins St",
            "Melbourne Docklands", "Brisbane CBD", "Perth CBD", "Adelaide CBD",
        ],
        "names": [
            "Michael Johnson", "Sarah Thompson", "David Williams", "Emily Brown",
            "James Wilson", "Olivia Taylor", "Andrew Martin", "Jessica Anderson",
            "Christopher Thomas", "Emma White", "Matthew Harris", "Lauren Jackson",
        ],
        "occupations": [
            "Mining Engineer", "Financial Planner", "GP Doctor", "Property Developer",
            "Nurse", "Technology Consultant", "Construction Manager",
        ],
        "loan_types": ["Home Loan", "Personal Loan", "Car Loan", "Business Loan"],
        "wealth_types": [
            "Term Deposit", "Managed Fund", "Life Insurance", "Superannuation",
        ],
        "account_types": ["Savings", "Savings", "Current"],
        "txn_debit": [
            "BPAY", "Direct Debit", "EFTPOS",
            "BAS Payment", "Rent Payment",
        ],
        "txn_credit": [
            "Payroll Credit", "Superannuation", "Osko Transfer",
            "Interest Credit", "Dividend Credit",
        ],
        "kyc_docs": {
            "aadhaar_type": "Medicare Card",
            "pan_type": "Tax File Number",
            "address_types": ["Driver Licence/Utility Bill"],
        },
        "salary_range": (60000, 500000),
        "balance_range": (10000, 300000),
        "home_loan_range": (400000, 2000000),
        "personal_loan_range": (10000, 80000),
        "car_loan_range": (15000, 80000),
        "fd_range": (10000, 300000),
        "home_loan_label": "Home Loan",
        "personal_loan_label": "Personal Loan",
        "car_loan_label": "Car Loan",
        "edu_loan_label": "Personal Loan",
        "home_loan_rate": (5.5, 7.5),
        "personal_loan_rate": (7.0, 14.0),
        "car_loan_rate": (5.0, 9.0),
        "edu_loan_rate": (5.5, 8.0),
    },
    "MY": {
        "country_name": "Malaysia",
        "region": "APAC",
        "currency": "MYR",
        "phone_prefix": "+60",
        "cities": [
            "KLCC", "Bangsar KL", "Petaling Jaya", "Penang Georgetown",
            "Johor Bahru City", "Subang Jaya", "Cyberjaya",
        ],
        "names": [
            "Ahmad Razif bin Abdullah", "Nurul Farhana binte Ismail", "Lee Chong Wei",
            "Tan Mei Yin", "Kumar Selvam a/l Ramasamy", "Priya Devi d/o Krishnan",
            "Mohd Hafizuddin bin Aziz", "Lim Siew Ching", "Rajendran a/l Subramaniam",
            "Nor Azlina binte Mohd Yusof", "Wong Kah Meng", "Kavitha a/p Murugesan",
        ],
        "occupations": [
            "Civil Engineer", "Bank Officer", "Business Owner", "Teacher",
            "IT Consultant", "Medical Officer", "Accountant",
        ],
        "loan_types": [
            "Housing Loan", "Personal Loan (Conventional)", "ASB Financing", "Car Loan",
        ],
        "wealth_types": [
            "Fixed Deposit", "Unit Trust", "Takaful Insurance", "ASB Fund",
        ],
        "account_types": ["Savings", "Savings", "Current"],
        "txn_debit": [
            "IBG Transfer", "DuitNow", "TNB Electricity",
            "EPF Deduction", "PTPTN",
        ],
        "txn_credit": [
            "Salary Credit", "ASB Dividend", "Interest Credit",
            "Bonus Credit", "DuitNow Received",
        ],
        "kyc_docs": {
            "aadhaar_type": "MyKad (IC)",
            "pan_type": "Income Tax No.",
            "address_types": ["Utility Bill/Rental Agreement"],
        },
        "salary_range": (30000, 300000),
        "balance_range": (10000, 500000),
        "home_loan_range": (200000, 2000000),
        "personal_loan_range": (10000, 100000),
        "car_loan_range": (30000, 200000),
        "fd_range": (10000, 300000),
        "home_loan_label": "Housing Loan",
        "personal_loan_label": "Personal Loan (Conventional)",
        "car_loan_label": "Car Loan",
        "edu_loan_label": "Personal Loan (Conventional)",
        "home_loan_rate": (3.0, 5.0),
        "personal_loan_rate": (4.5, 9.0),
        "car_loan_rate": (2.5, 4.5),
        "edu_loan_rate": (3.5, 6.0),
    },
    "HK": {
        "country_name": "Hong Kong",
        "region": "APAC",
        "currency": "HKD",
        "phone_prefix": "+852",
        "cities": [
            "Central", "Admiralty", "Mong Kok", "Causeway Bay",
            "Tsim Sha Tsui", "Wan Chai", "Kwun Tong",
        ],
        "names": [
            "Chan Siu Ming", "Wong Mei Ling", "Lee Ka Wai", "Cheung Hoi Yan",
            "Lam Wing Tung", "Ng Yat Fai", "Liu Xiao Hua", "Zhang Wei",
            "Ho Chi Wai", "Tang Lai Kuen", "Chow Wai Kit", "Kwok Mei Yee",
        ],
        "occupations": [
            "Investment Banker", "Solicitor", "Property Agent", "Finance Director",
            "Doctor", "Entrepreneur", "Fund Manager",
        ],
        "loan_types": ["Mortgage Loan", "Personal Loan", "Car Loan", "Tax Loan"],
        "wealth_types": [
            "Time Deposit", "Unit Trust", "Life Insurance", "MPF Fund",
        ],
        "account_types": ["Savings", "Savings", "Current"],
        "txn_debit": [
            "ATM Withdrawal", "MPF Contribution", "CLP Electricity",
            "Management Fee", "FPS Transfer",
        ],
        "txn_credit": [
            "Salary Credit", "FPS Transfer", "Interest Credit",
            "Dividend Credit", "Bonus Credit",
        ],
        "kyc_docs": {
            "aadhaar_type": "HKID Card",
            "pan_type": "MPF Account No.",
            "address_types": ["Rate Demand Note/Utility Bill"],
        },
        "salary_range": (200000, 3000000),
        "balance_range": (50000, 2000000),
        "home_loan_range": (2000000, 10000000),
        "personal_loan_range": (50000, 500000),
        "car_loan_range": (100000, 500000),
        "fd_range": (50000, 2000000),
        "home_loan_label": "Mortgage Loan",
        "personal_loan_label": "Personal Loan",
        "car_loan_label": "Car Loan",
        "edu_loan_label": "Personal Loan",
        "home_loan_rate": (2.5, 4.0),
        "personal_loan_rate": (4.0, 9.0),
        "car_loan_rate": (2.5, 5.0),
        "edu_loan_rate": (3.5, 6.0),
    },
    "SA": {
        "country_name": "Saudi Arabia",
        "region": "EMEA",
        "currency": "SAR",
        "phone_prefix": "+966",
        "cities": [
            "Riyadh King Fahd Rd", "Riyadh Olaya", "Jeddah Corniche",
            "Jeddah Al-Rawdah", "Dammam Al-Khobar", "Makkah", "Madinah",
        ],
        "names": [
            "Abdullah Al-Ghamdi", "Khalid Al-Zahrani", "Noura bint Al-Qahtani",
            "Mohammed Al-Otaibi", "Fatimah Al-Harbi", "Sarah Al-Shamri",
            "Tariq Al-Dossari", "Reem Al-Maliki", "Omar Al-Shahrani",
        ],
        "occupations": [
            "Oil Engineer", "Government Official", "Business Owner",
            "Medical Specialist", "Finance Director",
        ],
        "loan_types": [
            "Islamic Home Finance (Murabaha)", "Auto Finance", "Personal Finance",
        ],
        "wealth_types": [
            "Murabaha Deposit", "Islamic Sukuk", "Takaful Insurance", "REIT Fund",
        ],
        "account_types": ["Savings", "Savings", "Current"],
        "txn_debit": [
            "SARIE Transfer", "SADAD Payment", "ATM Cash",
            "Zakat Deduction", "STC Bill",
        ],
        "txn_credit": [
            "Salary Credit", "Bonus Credit", "Interest Credit",
            "SARIE Received", "Dividend Credit",
        ],
        "kyc_docs": {
            "aadhaar_type": "Saudi National ID / Iqama",
            "pan_type": "GOSI Registration",
            "address_types": ["Electricity Bill (SEC)"],
        },
        "salary_range": (100000, 1000000),
        "balance_range": (20000, 1000000),
        "home_loan_range": (500000, 3000000),
        "personal_loan_range": (20000, 200000),
        "car_loan_range": (50000, 300000),
        "fd_range": (20000, 500000),
        "home_loan_label": "Islamic Home Finance (Murabaha)",
        "personal_loan_label": "Personal Finance",
        "car_loan_label": "Auto Finance",
        "edu_loan_label": "Personal Finance",
        "home_loan_rate": (3.0, 5.5),
        "personal_loan_rate": (4.5, 8.0),
        "car_loan_rate": (3.0, 6.0),
        "edu_loan_rate": (4.0, 7.0),
    },
    "ZA": {
        "country_name": "South Africa",
        "region": "EMEA",
        "currency": "ZAR",
        "phone_prefix": "+27",
        "cities": [
            "Sandton Johannesburg", "Cape Town CBD", "Cape Town Waterfront",
            "Durban CBD", "Pretoria Arcadia",
        ],
        "names": [
            "Sipho Ndlovu", "Thandi Dlamini", "Pieter van der Berg", "Anita Botha",
            "Themba Nkosi", "Lerato Mokoena", "Johan du Plessis", "Nomvula Mthembu",
        ],
        "occupations": [
            "Mining Engineer", "Barrister/Attorney", "Medical Specialist",
            "Business Owner", "Financial Advisor", "Architect",
        ],
        "loan_types": ["Home Loan", "Personal Loan", "Vehicle Finance", "Business Loan"],
        "wealth_types": [
            "Fixed Deposit", "Unit Trust", "Life Insurance", "Retirement Annuity",
        ],
        "account_types": ["Savings", "Savings", "Current"],
        "txn_debit": [
            "EFT Transfer", "DebiCheck", "Municipal Account",
            "Eskom Bill", "SARS Tax",
        ],
        "txn_credit": [
            "Salary Credit", "JSE Dividend", "EFT Received",
            "Interest Credit", "Bonus Credit",
        ],
        "kyc_docs": {
            "aadhaar_type": "SA ID Document",
            "pan_type": "SARS Tax Number",
            "address_types": ["Municipal Account/Utility Bill"],
        },
        "salary_range": (200000, 2000000),
        "balance_range": (10000, 500000),
        "home_loan_range": (500000, 5000000),
        "personal_loan_range": (20000, 200000),
        "car_loan_range": (80000, 500000),
        "fd_range": (10000, 300000),
        "home_loan_label": "Home Loan",
        "personal_loan_label": "Personal Loan",
        "car_loan_label": "Vehicle Finance",
        "edu_loan_label": "Personal Loan",
        "home_loan_rate": (8.0, 12.0),
        "personal_loan_rate": (12.0, 20.0),
        "car_loan_rate": (10.0, 15.0),
        "edu_loan_rate": (10.0, 14.0),
    },
}

# ── Customer counts per country ───────────────────────────────────────────────

COUNTRY_COUNTS = [
    ("IN", 15),
    ("SG", 10),
    ("AE", 10),
    ("GB", 10),
    ("DE", 8),
    ("JP", 8),
    ("AU", 8),
    ("MY", 6),
    ("HK", 6),
    ("SA", 5),
    ("ZA", 4),
]

# ── Generic fund / policy name pools per country ──────────────────────────────

FUND_NAMES = {
    "IN": [
        "HDFC Flexi Cap Fund", "SBI Blue Chip Fund", "Axis Long Term Equity Fund",
        "Mirae Asset Large Cap Fund", "ICICI Pru Balanced Advantage Fund",
        "Nippon India Small Cap Fund", "Parag Parikh Flexi Cap Fund",
        "Kotak Emerging Equity Fund",
    ],
    "SG": [
        "Nikko AM Shenton Horizon Fund", "Lion Global Investors Bond Fund",
        "Aberdeen Standard APAC Equity", "Eastspring Investments Asia Pacific",
        "Fullerton SGD Bond Fund",
    ],
    "AE": [
        "Emirates NBD Islamic Sukuk Fund", "Dubai Islamic Bank Wakala Fund",
        "Abu Dhabi Investment Sukuk", "Emirates REIT Fund", "Noor Takaful Fund",
    ],
    "GB": [
        "Vanguard LifeStrategy 80% Equity", "iShares FTSE 100 ETF",
        "Fundsmith Equity Fund", "Baillie Gifford Global Alpha",
        "HSBC FTSE All-World Index Fund",
    ],
    "DE": [
        "DWS Deutschland Fonds", "Allianz Interglobal Fund",
        "Union Investment UniGlobal", "Deka DAX UCITS ETF",
        "Flossbach von Storch Multiple Opportunities",
    ],
    "JP": [
        "Nomura Fund Wrap", "Daiwa Investment Trust", "SBI Japan Stock Index",
        "Nikko Asset Management iDeCo", "Mitsubishi UFJ Global Balance Fund",
    ],
    "AU": [
        "Vanguard Australian Shares Index", "BetaShares ASX 200 ETF",
        "Colonial First State Balanced Fund", "AustralianSuper Balanced",
        "Perpetual Balanced Growth Fund",
    ],
    "MY": [
        "Public Mutual Growth Fund", "ASB Unit Trust",
        "CIMB Islamic Equity Fund", "RHB Bond Fund",
        "Maybank Islamic Growth Fund",
    ],
    "HK": [
        "Hang Seng MPF Conservative Fund", "BOCHK APAC Dividend Fund",
        "Manulife MPF Growth Fund", "HSBC HK Equity Fund",
        "Fidelity HK & China Fund",
    ],
    "SA": [
        "Al-Rajhi REIT Fund", "Saudi Fransi Islamic Sukuk",
        "NCB Capital Amanah Fund", "Riyad Capital Equity Fund",
        "SAMBA Islamic Fund",
    ],
    "ZA": [
        "Coronation Balanced Plus Fund", "Allan Gray Balanced Fund",
        "Sanlam Investment Management Fund", "Old Mutual Investors Fund",
        "Investec Opportunity Fund",
    ],
}

INSURANCE_POLICIES = {
    "IN": [
        "LIC Jeevan Anand", "HDFC Life Click2Protect",
        "ICICI Pru iProtect Smart", "SBI Life eShield",
    ],
    "SG": [
        "Great Eastern Endowment Plan", "Prudential PRUshield",
        "AIA Vitality Pro", "NTUC Income Star Endowment",
    ],
    "AE": [
        "Dubai Islamic Takaful Policy", "Abu Dhabi National Takaful",
        "Noor Takaful Family Protection", "Watania Takaful Plan",
    ],
    "GB": [
        "Aviva Life Insurance", "Legal & General Term Assurance",
        "Zurich UK Life Plan", "Royal London Protection Plan",
    ],
    "DE": [
        "Allianz Lebensversicherung", "Generali Deutschland Policy",
        "Zurich Gruppe Deutschland", "Zurich Riester Plan",
    ],
    "JP": [
        "Nippon Life Insurance", "Meiji Yasuda Life Policy",
        "Dai-ichi Life Insurance", "Japan Post Life Insurance",
    ],
    "AU": [
        "TAL Life Insurance", "AIA Australia Life Cover",
        "MLC Life Insurance", "BT Insurance Protection Plan",
    ],
    "MY": [
        "Takaful Malaysia Family Plan", "Prudential BSN Takaful",
        "Great Eastern Takaful", "AIA Takaful Malaysia",
    ],
    "HK": [
        "AIA Hong Kong Life Plan", "Manulife HK Insurance",
        "Prudential HK Life Cover", "HSBC Life HK Policy",
    ],
    "SA": [
        "Bupa Arabia Takaful", "Tawuniya Family Takaful",
        "Al-Rajhi Takaful Plan", "Arabian Shield Takaful",
    ],
    "ZA": [
        "Discovery Life Policy", "Old Mutual Life Cover",
        "Sanlam Life Insurance", "Liberty Life South Africa",
    ],
}


# ── Helper functions ──────────────────────────────────────────────────────────

def _to_inr(local_amount: float, currency: str) -> float:
    """Convert local currency amount to INR equivalent."""
    rate = INR_RATES.get(currency, 1.0)
    return round(local_amount * rate, 2)


def _rand_account_id() -> str:
    return "ACC" + "".join(random.choices(string.digits, k=9))


def _rand_loan_id() -> str:
    return "LN" + "".join(random.choices(string.digits, k=8))


def _rand_holding_id() -> str:
    return "WH" + "".join(random.choices(string.digits, k=8))


def _rand_customer_id(idx: int) -> str:
    return f"CUST{idx:04d}"


def _rand_doc_number(pattern: str = "??######??") -> str:
    """Generate a random alphanumeric document number."""
    result = []
    for ch in pattern:
        if ch == "?":
            result.append(random.choice(string.ascii_uppercase))
        elif ch == "#":
            result.append(random.choice(string.digits))
        else:
            result.append(ch)
    return "".join(result)


def _future_date(min_days: int = 10, max_days: int = 3650) -> str:
    return (date.today() + timedelta(days=random.randint(min_days, max_days))).isoformat()


def _past_date(min_days: int = 30, max_days: int = 3650) -> str:
    return (date.today() - timedelta(days=random.randint(min_days, max_days))).isoformat()


def _near_expiry_date(max_days: int = 90) -> str:
    return (date.today() + timedelta(days=random.randint(1, max_days))).isoformat()


def _rand_age(segment: str) -> int:
    if segment == "Mass":
        return random.randint(22, 45)
    elif segment == "Affluent":
        return random.randint(30, 55)
    else:  # HNI
        return random.randint(35, 65)


def _rand_email(name: str, country: str) -> str:
    """Generate email from name."""
    local = name.lower().replace(" ", ".").replace("/", "").replace("'", "")
    # Keep only ASCII letters, digits and dots
    local = "".join(c for c in local if c.isalnum() or c == ".")
    local = local[:20]
    domains = {
        "IN": ["gmail.com", "yahoo.co.in", "outlook.com"],
        "SG": ["gmail.com", "singtel.com.sg", "outlook.com"],
        "AE": ["gmail.com", "hotmail.com", "emiratesmail.ae"],
        "GB": ["gmail.com", "outlook.co.uk", "hotmail.co.uk"],
        "DE": ["gmail.com", "web.de", "gmx.de"],
        "JP": ["gmail.com", "docomo.ne.jp", "softbank.ne.jp"],
        "AU": ["gmail.com", "outlook.com.au", "bigpond.com"],
        "MY": ["gmail.com", "yahoo.com.my", "hotmail.com"],
        "HK": ["gmail.com", "netvigator.com", "hotmail.com.hk"],
        "SA": ["gmail.com", "hotmail.com", "outlook.sa"],
        "ZA": ["gmail.com", "webmail.co.za", "outlook.com"],
    }
    domain = random.choice(domains.get(country, ["gmail.com"]))
    suffix = "".join(random.choices(string.digits, k=3))
    return f"{local}{suffix}@{domain}"


def _rand_phone(country: str) -> str:
    cfg = COUNTRY_CONFIG[country]
    prefix = cfg["phone_prefix"]
    phone_lengths = {
        "+91": 10, "+65": 8, "+971": 9, "+44": 10,
        "+49": 10, "+81": 10, "+61": 9, "+60": 9,
        "+852": 8, "+966": 9, "+27": 9,
    }
    n = phone_lengths.get(prefix, 9)
    digits = "".join(random.choices(string.digits, k=n))
    return f"{prefix}{digits}"


def _gen_transactions(
    balance_inr: float, country: str, n: int = 4
) -> list[dict]:
    cfg = COUNTRY_CONFIG[country]
    currency = cfg["currency"]
    rate = INR_RATES[currency]
    txns = []
    for _ in range(n):
        is_credit = random.random() < 0.4
        # Generate local currency amount then convert to INR
        max_local = min(balance_inr / rate * 0.2, 50000)
        max_local = max(max_local, 100)
        local_amount = round(random.uniform(100, max_local), 2)
        inr_amount = _to_inr(local_amount, currency)
        desc = random.choice(
            cfg["txn_credit"] if is_credit else cfg["txn_debit"]
        )
        txns.append({
            "date": _past_date(1, 90),
            "description": desc,
            "amount": inr_amount,
            "type": "credit" if is_credit else "debit",
        })
    txns.sort(key=lambda x: x["date"], reverse=True)
    return txns


def _gen_account(country: str, dormant: bool = False) -> dict:
    cfg = COUNTRY_CONFIG[country]
    currency = cfg["currency"]
    bal_min, bal_max = cfg["balance_range"]
    if dormant:
        local_balance = round(random.uniform(bal_min * 0.01, bal_min * 0.1), 2)
    else:
        local_balance = round(random.uniform(bal_min, bal_max), 2)
    balance_inr = _to_inr(local_balance, currency)

    acc_type = random.choice(cfg["account_types"])
    txns = _gen_transactions(balance_inr, country, n=random.randint(3, 5))

    if dormant:
        old_base = date.today() - timedelta(days=365)
        txns = [
            {
                "date": (old_base - timedelta(days=random.randint(0, 180))).isoformat(),
                "description": random.choice(cfg["txn_debit"]),
                "amount": _to_inr(
                    round(random.uniform(100, bal_min * 0.05), 2), currency
                ),
                "type": "debit",
            }
            for _ in range(2)
        ]

    return {
        "account_id": _rand_account_id(),
        "type": acc_type,
        "balance": balance_inr,
        "branch": random.choice(cfg["cities"]),
        "status": "Dormant" if dormant else "Active",
        "transactions": txns,
    }


def _gen_loan(country: str) -> dict:
    cfg = COUNTRY_CONFIG[country]
    currency = cfg["currency"]
    loan_type = random.choice(cfg["loan_types"])

    # Map loan type to category to pick appropriate range and rate
    label_home = cfg["home_loan_label"]
    label_personal = cfg["personal_loan_label"]
    label_car = cfg["car_loan_label"]

    if loan_type == label_home:
        lo, hi = cfg["home_loan_range"]
        rate_lo, rate_hi = cfg["home_loan_rate"]
        tenure = random.choice([120, 180, 240, 300])
    elif loan_type == label_personal or "personal" in loan_type.lower() or "raten" in loan_type.lower() or "finance" in loan_type.lower():
        lo, hi = cfg["personal_loan_range"]
        rate_lo, rate_hi = cfg["personal_loan_rate"]
        tenure = random.choice([12, 24, 36, 48, 60])
    elif loan_type == label_car or "car" in loan_type.lower() or "auto" in loan_type.lower() or "vehicle" in loan_type.lower():
        lo, hi = cfg["car_loan_range"]
        rate_lo, rate_hi = cfg["car_loan_rate"]
        tenure = random.choice([36, 48, 60, 72, 84])
    else:
        # Education / student / ASB / Tax / Business
        lo, hi = cfg["personal_loan_range"]
        rate_lo, rate_hi = cfg["personal_loan_rate"]
        tenure = random.choice([60, 84, 120])

    local_sanctioned = round(random.uniform(lo, hi), 2)
    sanctioned_inr = _to_inr(local_sanctioned, currency)
    rate = round(random.uniform(rate_lo, rate_hi), 2)

    r = rate / 12 / 100
    n = tenure
    if r > 0:
        emi = round(sanctioned_inr * r * (1 + r) ** n / ((1 + r) ** n - 1), 2)
    else:
        emi = round(sanctioned_inr / n, 2)

    months_paid = random.randint(0, tenure - 1)
    outstanding = round(sanctioned_inr * (1 - months_paid / tenure), 2)
    is_overdue = random.random() < 0.1

    return {
        "loan_id": _rand_loan_id(),
        "type": loan_type,
        "sanctioned_amount": sanctioned_inr,
        "outstanding": outstanding,
        "emi": emi,
        "rate": rate,
        "tenure_months": tenure,
        "start_date": _past_date(30, months_paid * 30 + 30),
        "status": "Overdue" if is_overdue else "Active",
    }


def _gen_wealth(country: str, wealth_type: str) -> dict:
    cfg = COUNTRY_CONFIG[country]
    currency = cfg["currency"]
    fd_lo, fd_hi = cfg["fd_range"]
    holding: dict = {"holding_id": _rand_holding_id(), "type": wealth_type}

    wt_lower = wealth_type.lower()

    # Fixed deposit variants
    if any(x in wt_lower for x in ["fixed deposit", "term deposit", "festgeld", "time deposit", "murabaha deposit", "定期預金"]):
        local_amount = round(random.uniform(fd_lo, fd_hi), 2)
        holding["amount"] = _to_inr(local_amount, currency)
        holding["rate"] = round(random.uniform(2.5, 7.5), 2)
        if random.random() < 0.2:
            holding["maturity_date"] = _near_expiry_date(90)
        else:
            holding["maturity_date"] = _future_date(91, 1825)
        holding["fund_name"] = None
        holding["policy_number"] = None

    # Fund / trust / pension / superannuation / ISA / PPF / ASB / REIT / sukuk / CPF
    elif any(x in wt_lower for x in [
        "mutual fund", "unit trust", "managed fund", "investmentfonds",
        "investment trust", "superannuation", "pension", "ppf", "asb fund",
        "mpf fund", "cpf investment", "reit fund", "iDeCo".lower(), "riester",
        "stocks & shares", "retirement annuity", "islamic sukuk", "sukuk",
    ]):
        local_amount = round(random.uniform(fd_lo * 0.5, fd_hi * 0.8), 2)
        holding["amount"] = _to_inr(local_amount, currency)
        holding["rate"] = round(random.uniform(5.0, 15.0), 2)
        holding["maturity_date"] = None
        holding["fund_name"] = random.choice(
            FUND_NAMES.get(country, FUND_NAMES["IN"])
        )
        holding["policy_number"] = None

    # Insurance / takaful
    elif any(x in wt_lower for x in [
        "insurance", "takaful", "lebensversicherung", "gold savings",
    ]):
        local_amount = round(random.uniform(fd_lo * 0.1, fd_hi * 0.3), 2)
        holding["amount"] = _to_inr(local_amount, currency)
        holding["rate"] = round(random.uniform(3.0, 6.5), 2)
        holding["maturity_date"] = _future_date(365, 7300)
        holding["fund_name"] = random.choice(
            INSURANCE_POLICIES.get(country, INSURANCE_POLICIES["IN"])
        )
        holding["policy_number"] = "POL" + "".join(random.choices(string.digits, k=8))

    else:
        # Fallback — treat like FD
        local_amount = round(random.uniform(fd_lo, fd_hi), 2)
        holding["amount"] = _to_inr(local_amount, currency)
        holding["rate"] = round(random.uniform(3.0, 7.0), 2)
        holding["maturity_date"] = _future_date(91, 1825)
        holding["fund_name"] = None
        holding["policy_number"] = None

    return holding


def _gen_kyc(country: str, near_expiry: bool = False) -> dict:
    cfg = COUNTRY_CONFIG[country]
    docs = cfg["kyc_docs"]
    addr_expiry = _near_expiry_date(90) if near_expiry else _future_date(180, 3650)

    return {
        "aadhaar": {
            "type": docs["aadhaar_type"],
            "number": _rand_doc_number("??######??"),
            "verified": True,
            "expiry": None,
        },
        "pan": {
            "type": docs["pan_type"],
            "number": _rand_doc_number("??######??"),
            "verified": True,
            "expiry": None,
        },
        "address_proof": {
            "type": random.choice(docs["address_types"]),
            "number": _rand_doc_number("??######??"),
            "verified": random.random() > 0.1,
            "expiry": addr_expiry,
        },
        "risk_category": random.choices(
            ["Low", "Medium", "High"], weights=[60, 30, 10], k=1
        )[0],
        "last_updated": _past_date(30, 730),
    }


def _get_name(country: str) -> str:
    cfg = COUNTRY_CONFIG[country]
    if country == "IN":
        return fake_in.name()
    names = cfg["names"]
    return random.choice(names)


def _get_annual_income(country: str, segment: str, currency: str) -> float:
    cfg = COUNTRY_CONFIG[country]
    sal_lo, sal_hi = cfg["salary_range"]
    if segment == "HNI":
        lo = sal_lo + (sal_hi - sal_lo) * 0.7
        hi = sal_hi
    elif segment == "Affluent":
        lo = sal_lo + (sal_hi - sal_lo) * 0.35
        hi = sal_lo + (sal_hi - sal_lo) * 0.8
    else:
        lo = sal_lo
        hi = sal_lo + (sal_hi - sal_lo) * 0.45
    local_income = round(random.uniform(lo, hi), 2)
    return _to_inr(local_income, currency)


# ── Main generator ────────────────────────────────────────────────────────────

def generate_customers() -> list[dict]:
    customers = []
    cust_idx = 1

    for country, count in COUNTRY_COUNTS:
        cfg = COUNTRY_CONFIG[country]
        currency = cfg["currency"]

        # Segment weights per country: adjust slightly for wealthier markets
        if country in ("HK", "SG", "AE", "SA"):
            segment_weights = [40, 40, 20]
        elif country in ("GB", "AU", "DE"):
            segment_weights = [50, 35, 15]
        else:
            segment_weights = [60, 30, 10]

        # Track names used to avoid exact duplicates within a country
        used_names: set[str] = set()

        for _ in range(count):
            segment = random.choices(
                ["Mass", "Affluent", "HNI"], weights=segment_weights, k=1
            )[0]

            # Get a unique name
            attempts = 0
            while True:
                name = _get_name(country)
                if name not in used_names or attempts > 20:
                    used_names.add(name)
                    break
                attempts += 1

            phone = _rand_phone(country)
            email = _rand_email(name, country)
            age = _rand_age(segment)
            occupation = random.choice(cfg["occupations"])
            annual_income = _get_annual_income(country, segment, currency)

            # Accounts: 1-2 per customer; 15% chance of dormant
            num_accounts = random.randint(1, 2)
            has_dormant = random.random() < 0.15
            accounts = []
            for j in range(num_accounts):
                is_dormant = has_dormant and j == 0
                accounts.append(_gen_account(country, dormant=is_dormant))

            # Loans: 0-2 depending on segment
            num_loans = random.randint(0, 2)
            if segment == "Mass":
                num_loans = min(num_loans, 1)
            loans = [_gen_loan(country) for _ in range(num_loans)]

            # Wealth: 0-3 depending on segment
            if segment == "HNI":
                num_wealth = random.randint(2, 3)
            elif segment == "Affluent":
                num_wealth = random.randint(1, 3)
            else:
                num_wealth = random.randint(0, 2)

            wealth_pool = random.sample(
                cfg["wealth_types"], k=min(num_wealth, len(cfg["wealth_types"]))
            )
            wealth = [_gen_wealth(country, wt) for wt in wealth_pool]

            # KYC
            near_expiry = random.random() < 0.15
            kyc = _gen_kyc(country, near_expiry=near_expiry)

            customers.append({
                "customer_id": _rand_customer_id(cust_idx),
                "name": name,
                "phone": phone,
                "email": email,
                "segment": segment,
                "relationship_since": _past_date(180, 7300),
                "country": country,
                "country_name": cfg["country_name"],
                "city": random.choice(cfg["cities"]),
                "region": cfg["region"],
                "currency": currency,
                "occupation": occupation,
                "annual_income": annual_income,
                "age": age,
                "accounts": accounts,
                "loans": loans,
                "wealth": wealth,
                "kyc": kyc,
                "photo_url": None,
            })
            cust_idx += 1

    return customers


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    total = sum(c for _, c in COUNTRY_COUNTS)
    print(f"Generating {total} customers across {len(COUNTRY_COUNTS)} countries …")

    customers = generate_customers()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2, ensure_ascii=False)

    print(f"\nWritten {len(customers)} customers to {OUTPUT_PATH}")

    # Summary breakdown by country
    country_counts = Counter(c["country"] for c in customers)
    print("\nBreakdown by country:")
    for country, cnt in country_counts.items():
        cname = COUNTRY_CONFIG[country]["country_name"]
        print(f"  {country} ({cname}): {cnt}")

    # Breakdown by segment
    segment_counts = Counter(c["segment"] for c in customers)
    print("\nBreakdown by segment:")
    for seg, cnt in segment_counts.items():
        print(f"  {seg}: {cnt}")

    # Breakdown by region
    region_counts = Counter(c["region"] for c in customers)
    print("\nBreakdown by region:")
    for region, cnt in region_counts.items():
        print(f"  {region}: {cnt}")

    dormant = sum(
        1 for c in customers for a in c["accounts"] if a["status"] == "Dormant"
    )
    print(f"\nDormant accounts: {dormant}")

    near_kyc = sum(
        1
        for c in customers
        if c["kyc"]["address_proof"]["expiry"]
        and c["kyc"]["address_proof"]["expiry"]
        <= (date.today() + timedelta(days=90)).isoformat()
    )
    print(f"KYC expiring within 90 days: {near_kyc}")


if __name__ == "__main__":
    main()
