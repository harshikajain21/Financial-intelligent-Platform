# security_audit.py

import os
import re

print("=" * 50)
print("SECURITY AUDIT REPORT")
print("=" * 50)

# ── Check 1: Hardcoded secrets ──────────────────────
print("\n[1] Checking for hardcoded secrets...")

suspicious = []
secret_patterns = [
    r'api_key\s*=\s*["\'][^"\']{8,}["\']',
    r'password\s*=\s*["\'][^"\']{4,}["\']',
    r'secret\s*=\s*["\'][^"\']{8,}["\']',
    r'token\s*=\s*["\'][^"\']{8,}["\']',
]

skip_dirs  = {'venv', '__pycache__', 'node_modules', '.git', 'logs'}
skip_files = {'.env', 'security.py', 'security_audit.py'}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for file in files:
        if not file.endswith('.py'):
            continue
        if file in skip_files:
            continue
        path = os.path.join(root, file)
        try:
            content = open(path, encoding='utf-8', errors='ignore').read()
            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if 'your_' not in match and 'example' not in match.lower() and 'settings.' not in match:
                        suspicious.append(f'{path}: {match[:80]}')
        except Exception:
            pass

if suspicious:
    print("  ISSUES FOUND:")
    for s in suspicious:
        print(f"  - {s}")
else:
    print("  OK: No hardcoded secrets found")

# ── Check 2: .env exists and .gitignore protects it ──
print("\n[2] Checking .env protection...")
if os.path.exists('.env'):
    print("  OK: .env file exists")
else:
    print("  WARNING: .env file missing")

if os.path.exists('.gitignore'):
    gitignore = open('.gitignore').read()
    if '.env' in gitignore:
        print("  OK: .env is in .gitignore")
    else:
        print("  WARNING: .env not in .gitignore — secrets could be committed!")
else:
    print("  WARNING: .gitignore missing")

# ── Check 3: API keys in security.py ────────────────
print("\n[3] Checking hardcoded API keys in security.py...")
if os.path.exists('api/security.py'):
    content = open('api/security.py').read()
    if 'demo-key-12345' in content or 'admin-key-99999' in content:
        print("  WARNING: Hardcoded API keys found in security.py")
        print("  ACTION: These should come from .env in production")
    else:
        print("  OK: No hardcoded keys in security.py")

# ── Check 4: Rate limiting in place ─────────────────
print("\n[4] Checking rate limiting...")
routes_dir = 'api/routes'
rate_limited = []
not_limited  = []
for f in os.listdir(routes_dir):
    if not f.endswith('.py'):
        continue
    content = open(os.path.join(routes_dir, f)).read()
    if '@limiter.limit' in content:
        rate_limited.append(f)
    else:
        not_limited.append(f)

print(f"  Rate limited: {rate_limited}")
print(f"  Not limited : {not_limited}")

# ── Check 5: Input sanitization ─────────────────────
print("\n[5] Checking input sanitization...")
if os.path.exists('api/sanitizer.py'):
    print("  OK: sanitizer.py exists")
    content = open('api/sanitizer.py').read()
    checks = ['sanitize_symbol', 'sanitize_query', 'sanitize_exchange']
    for c in checks:
        status = "OK" if c in content else "MISSING"
        print(f"  {status}: {c}")
else:
    print("  WARNING: sanitizer.py missing")

# ── Check 6: CORS configuration ─────────────────────
print("\n[6] Checking CORS...")
main_content = open('api/main.py').read()
if 'allow_origins=["*"]' in main_content or "allow_origins=['*']" in main_content:
    print("  WARNING: CORS open to all origins")
elif 'localhost:3000' in main_content:
    print("  OK: CORS restricted to known origins")
else:
    print("  CHECK: Review CORS settings manually")

# ── Check 7: Security headers ────────────────────────
print("\n[7] Checking security headers...")
headers = [
    'X-Content-Type-Options',
    'X-Frame-Options',
    'X-XSS-Protection',
    'Referrer-Policy',
    'Cache-Control'
]
for h in headers:
    status = "OK" if h in main_content else "MISSING"
    print(f"  {status}: {h}")

# ── Check 8: Error sanitization ─────────────────────
print("\n[8] Checking error handling...")
if 'global_exception_handler' in main_content:
    print("  OK: Global exception handler present")
else:
    print("  WARNING: No global exception handler")

# ── Check 9: Authentication ──────────────────────────
print("\n[9] Checking authentication...")
if os.path.exists('api/security.py'):
    sec = open('api/security.py').read()
    checks = ['SECRET_KEY', 'jwt', 'bcrypt', 'HTTPBearer']
    for c in checks:
        status = "OK" if c in sec else "MISSING"
        print(f"  {status}: {c}")

# ── Check 10: Database safety ────────────────────────
print("\n[10] Checking database safety...")
if os.path.exists('database/repository.py'):
    repo = open('database/repository.py').read()
    if 'db.query(' in repo and 'filter(' in repo:
        print("  OK: Using ORM queries (safe from SQL injection)")
    if 'execute(' in repo:
        print("  WARNING: Raw execute() found — review for SQL injection")
    else:
        print("  OK: No raw SQL execute() calls")

print("\n" + "=" * 50)
print("AUDIT COMPLETE")
print("=" * 50)