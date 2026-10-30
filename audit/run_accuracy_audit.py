import fitz
import json
import csv
from pathlib import Path
from rapidfuzz import fuzz

def audit_document(pdf_path_str, qms_json_path_str, output_csv_path_str):
    pdf_path = Path(pdf_path_str)
    qms_json_path = Path(qms_json_path_str)
    output_csv_path = Path(output_csv_path_str)
    
    if not pdf_path.exists() or not qms_json_path.exists():
        print(f"Skipping {pdf_path}: file not found.")
        return
        
    doc = fitz.open(str(pdf_path))
    pages_text = {i + 1: doc[i].get_text() for i in range(len(doc))}
    
    with open(qms_json_path, encoding='utf-8') as f:
        qms_rows = json.load(f)
    
    audit_rows = []
    
    correct_count = 0
    incorrect_count = 0
    missed_count = 0
    hallucinated_count = 0
    unclear_count = 0
    
    for row in qms_rows:
        qms_field = row.get('qms_field')
        label = row.get('label')
        status = row.get('status')
        val = row.get('limit_amount') if row.get('limit_amount') is not None else row.get('limit_text')
        if val is None and row.get('limit_percent_of_si') is not None:
            val = f"{row.get('limit_percent_of_si')}%"
        if val is None and row.get('limit_days') is not None:
            val = f"{row.get('limit_days')} days"
            
        src_pages = row.get('source_pages') or []
        evidence = row.get('evidence') or ''
        
        # 1. Independent text verification of evidence on claimed page
        evidence_found = 'no'
        if evidence:
            ev_clean = ' '.join(evidence.split())[:120]
            # check on claimed pages
            for p in src_pages:
                if p in pages_text:
                    score = fuzz.partial_ratio(ev_clean.lower(), ' '.join(pages_text[p].split()).lower())
                    if score >= 75:
                        evidence_found = 'yes'
                        break
            if evidence_found == 'no':
                # check across all pages
                for p, ptext in pages_text.items():
                    score = fuzz.partial_ratio(ev_clean.lower(), ' '.join(ptext.split()).lower())
                    if score >= 75:
                        evidence_found = f'yes (found on page {p})'
                        break
        else:
            evidence_found = 'N/A (no evidence quote)'
            
        # 2. Evaluate validity
        value_matches = 'yes'
        notes = ''
        
        if status in ['not_mentioned', None] and not val:
            # Check if this term might actually be mentioned in the PDF
            field_name_words = label.lower().split()
            found_mentions = []
            for p, ptext in pages_text.items():
                for w in field_name_words:
                    if len(w) > 4 and w in ptext.lower():
                        found_mentions.append((p, w))
            if len(found_mentions) > 2:
                value_matches = 'unclear'
                notes = f"Possible mention on pages {set(p for p, w in found_mentions)}"
                missed_count += 1
            else:
                correct_count += 1
                notes = 'Correctly identified as not mentioned'
        elif evidence and evidence_found.startswith('yes'):
            correct_count += 1
            notes = 'Evidence verified in raw text'
        elif evidence and evidence_found == 'no':
            value_matches = 'no'
            hallucinated_count += 1
            notes = 'Evidence quote not found in document text'
        else:
            unclear_count += 1
            notes = 'Requires manual verification'
            
        audit_rows.append({
            'qms_field': qms_field,
            'label': label,
            'extracted_value': val,
            'extracted_status': status,
            'source_pages_claimed': ','.join(map(str, src_pages)),
            'evidence_quote_claimed': evidence[:120].replace('\n', ' '),
            'evidence_found_on_claimed_page': evidence_found,
            'value_matches_evidence': value_matches,
            'notes': notes
        })
        
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=audit_rows[0].keys())
        writer.writeheader()
        writer.writerows(audit_rows)
        
    total = len(qms_rows)
    acc = round((correct_count / total) * 100, 1)
    print(f"=== Summary for {pdf_path.name} ===")
    print(f"Total fields: {total} | Correct: {correct_count} | Missed/Unclear: {missed_count} | Hallucinated: {hallucinated_count} | Unclear: {unclear_count} | Accuracy: {acc}%")

if __name__ == '__main__':
    audit_document('uploads/1.Policy Copy.pdf', 'output/1.Policy Copy.qms.json', 'audit/accuracy_1.Policy Copy.csv')
    audit_document('samples/sample_gmc_policy.pdf', 'output/sample_gmc_policy.qms.json', 'audit/accuracy_sample_gmc_policy.csv')
