"""Persistencia servidor (SQLite) V0.3: entidades por cuenta, auditoría encadenada por hash, usuarios/roles/sesiones.
Aislamiento: TODA lectura/escritura de datos de negocio exige account_id y se filtra por él (no se mezclan contabilidades/titularidades).
Sin secretos: contraseñas con scrypt+sal; sesiones guardadas como hash SHA-256 del token."""
import hashlib, hmac, json, os, secrets, sqlite3, threading, time

KINDS = {"brand", "product", "dossier", "dataset", "evidence", "task", "ai_run", "query", "approval", "news", "cost_doc", "plan"}
ROLES = {"analyst": 1, "approver": 2, "admin": 3}
SESSION_TTL = 8 * 3600
SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY, name TEXT NOT NULL, legal_entity TEXT NOT NULL, seller_central_ref TEXT, marketplaces TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, pw_salt BLOB NOT NULL, pw_hash BLOB NOT NULL, role TEXT NOT NULL, accounts TEXT NOT NULL DEFAULT '[]', active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, username TEXT NOT NULL, csrf TEXT NOT NULL, expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), kind TEXT NOT NULL, key TEXT, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, created_by TEXT);
CREATE TABLE IF NOT EXISTS ai_budget(id TEXT PRIMARY KEY, month TEXT NOT NULL, real INTEGER NOT NULL, state TEXT NOT NULL, worst REAL NOT NULL, actual REAL, model TEXT, created_at TEXT NOT NULL, closed_at TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS keepa_cache(k TEXT PRIMARY KEY, domain INTEGER NOT NULL, asin TEXT NOT NULL, params TEXT NOT NULL, fetched_at REAL NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS keepa_ledger(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, op TEXT NOT NULL, domain INTEGER, n_asin INTEGER, est_tokens INTEGER, tokens_consumed INTEGER, tokens_left INTEGER, refill_rate INTEGER, status TEXT NOT NULL, cache_hits INTEGER, note TEXT);
CREATE INDEX IF NOT EXISTS ix_rec ON records(account_id, kind, updated_at);
CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, account_id TEXT, actor TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
"""


class Forbidden(Exception):
    pass


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canon(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class Store:
    def __init__(self, path=":memory:"):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        # una reserva «reserved» que sobrevive a un reinicio = proceso caído en mitad de una llamada → consumo INCIERTO (se sigue cobrando el peor caso)
        self.db.execute("UPDATE ai_budget SET state='uncertain', note='INTERRUMPIDA_POR_REINICIO', closed_at=? WHERE state='reserved'", (now(),))
        self.db.commit()

    # ---- usuarios / sesiones -------------------------------------------------------------------
    @staticmethod
    def _hash(pw, salt):
        return hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)

    def create_user(self, username, password, role, accounts):
        if role not in ROLES or len(password) < 10 or not username.isidentifier():
            raise ValueError("usuario/rol/contraseña inválidos (mínimo 10 caracteres)")
        salt = os.urandom(16)
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO users VALUES(?,?,?,?,?,1)", (username, salt, self._hash(password, salt), role, json.dumps(accounts)))
            self.db.commit()
        self.audit(None, "system", "user.create", {"username": username, "role": role, "accounts": accounts})

    def login(self, username, password):
        with self.lock:
            u = self.db.execute("SELECT * FROM users WHERE username=? AND active=1", (username,)).fetchone()
            ok = bool(u) and hmac.compare_digest(self._hash(password, u["pw_salt"]), u["pw_hash"]) if u else hmac.compare_digest(self._hash(password, b"x" * 16), b"\0" * 32)
            if not ok:
                self.audit(None, username[:40], "login.fail", {})
                return None
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
            self.db.execute("INSERT INTO sessions VALUES(?,?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), username, csrf, time.time() + SESSION_TTL))
            self.db.commit()
        self.audit(None, username, "login.ok", {})
        return {"token": token, "csrf": csrf}

    def session(self, token):
        if not token:
            return None
        h = hashlib.sha256(token.encode()).hexdigest()
        with self.lock:
            s = self.db.execute("SELECT s.csrf,s.expires,u.username,u.role,u.accounts FROM sessions s JOIN users u USING(username) WHERE token_hash=? AND u.active=1", (h,)).fetchone()
            if not s or s["expires"] < time.time():
                return None
            return {"username": s["username"], "role": s["role"], "accounts": json.loads(s["accounts"]), "csrf": s["csrf"]}

    def logout(self, token):
        with self.lock:
            self.db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256((token or "").encode()).hexdigest(),)); self.db.commit()

    # ---- cuentas ---------------------------------------------------------------------------------
    def create_account(self, id_, name, legal_entity, seller_ref=None, marketplaces=None, actor="system"):
        with self.lock:
            self.db.execute("INSERT OR IGNORE INTO accounts VALUES(?,?,?,?,?,?)", (id_, name, legal_entity, seller_ref, json.dumps(marketplaces if marketplaces is not None else ["amazon.es"]), now())); self.db.commit()
        self.audit(id_, actor, "account.create", {"name": name, "legal_entity": legal_entity, "marketplaces": marketplaces if marketplaces is not None else ["amazon.es"]})

    def accounts_for(self, sess):
        with self.lock:
            rows = self.db.execute("SELECT * FROM accounts ORDER BY id").fetchall()
        return [{"id": r["id"], "name": r["name"], "legal_entity": r["legal_entity"], "seller_central_ref": r["seller_central_ref"], "marketplaces": json.loads(r["marketplaces"])}
                for r in rows if sess["role"] == "admin" or r["id"] in sess["accounts"]]

    @staticmethod
    def can_access(sess, account_id):
        return sess["role"] == "admin" or account_id in sess["accounts"]

    # ---- registros por cuenta ------------------------------------------------------------------
    def put(self, account_id, kind, data, id_=None, key=None, actor="system"):
        if kind not in KINDS:
            raise ValueError("tipo desconocido")
        t = now()
        with self.lock:
            if not self.db.execute("SELECT 1 FROM accounts WHERE id=?", (account_id,)).fetchone():
                raise ValueError("cuenta inexistente")
            if id_:
                row = self.db.execute("SELECT account_id FROM records WHERE id=?", (id_,)).fetchone()
                if row and row["account_id"] != account_id:
                    raise Forbidden("el registro pertenece a otra cuenta")
            else:
                id_ = f"{kind}-{secrets.token_hex(6)}"
            if row_exists := self.db.execute("SELECT 1 FROM records WHERE id=?", (id_,)).fetchone():
                self.db.execute("UPDATE records SET data=?, key=COALESCE(?,key), updated_at=? WHERE id=? AND account_id=?", (canon(data), key, t, id_, account_id))
            else:
                self.db.execute("INSERT INTO records VALUES(?,?,?,?,?,?,?,?)", (id_, account_id, kind, key, canon(data), t, t, actor))
            self.db.commit()
        self.audit(account_id, actor, f"{kind}.{'update' if row_exists else 'create'}", {"id": id_, "key": key})
        return id_

    def get(self, account_id, id_):
        with self.lock:
            r = self.db.execute("SELECT * FROM records WHERE id=? AND account_id=?", (id_, account_id)).fetchone()
        return self._rec(r) if r else None

    # ---- libro de presupuesto de IA: reserva atómica ------------------------------------------------
    def reserve(self, worst, budget, real, model=None):
        """Comprueba y reserva EN UNA SOLA OPERACIÓN (hilo + transacción IMMEDIATE de SQLite, válida también entre procesos).
        committed = real facturado (settled) + peor caso de lo reservado/incierto. Devuelve id o None si superaría el presupuesto mensual."""
        month = time.strftime("%Y-%m", time.gmtime()); rid = "bud-" + secrets.token_hex(6)
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                committed = self.db.execute("SELECT COALESCE(SUM(CASE WHEN state='settled' THEN actual ELSE worst END),0) FROM ai_budget WHERE month=? AND real=? AND state IN ('reserved','uncertain','settled')", (month, int(bool(real)))).fetchone()[0]
                if committed + worst > budget + 1e-12:
                    self.db.execute("ROLLBACK"); return None
                self.db.execute("INSERT INTO ai_budget VALUES(?,?,?,?,?,?,?,?,?,?)", (rid, month, int(bool(real)), "reserved", worst, None, model, now(), None, None))
                self.db.execute("COMMIT")
            except BaseException:
                try: self.db.execute("ROLLBACK")
                except sqlite3.Error: pass
                raise
        return rid

    def _close(self, rid, state, actual=None, note=""):
        with self.lock:
            self.db.execute("UPDATE ai_budget SET state=?, actual=?, note=?, closed_at=? WHERE id=?", (state, actual, note, now(), rid)); self.db.commit()

    def settle(self, rid, actual, note=""):
        self._close(rid, "settled", float(actual or 0.0), note)

    def uncertain(self, rid, note=""):
        self._close(rid, "uncertain", None, note)

    def release(self, rid, note=""):
        self._close(rid, "released", None, note)

    def reconcile(self, rid, actual, actor="admin"):
        """El administrador fija el coste real (p. ej. leído del panel de OpenAI) de una reserva INCIERTA."""
        with self.lock:
            r = self.db.execute("SELECT state FROM ai_budget WHERE id=?", (rid,)).fetchone()
            if not r or r["state"] != "uncertain":
                raise ValueError("solo se concilian reservas inciertas")
            if not (isinstance(actual, (int, float)) and 0 <= actual < 1000):
                raise ValueError("coste real no válido")
        self._close(rid, "settled", float(actual), "CONCILIADO_POR_ADMIN")
        self.audit(None, actor, "ai_budget.reconcile", {"id": rid, "actual": float(actual)})

    def real_ai_verified(self):
        """¿Existe alguna ejecución REAL (host oficial) sin error y con tokens reportados por el proveedor? Solo entonces se declara «IA real verificada»."""
        with self.lock:
            rows = self.db.execute("SELECT data FROM records WHERE kind='ai_run'").fetchall()
        for r in rows:
            d = json.loads(r["data"])
            if d.get("mode") == "REAL" and not d.get("error") and d.get("token_source") == "reportado_por_proveedor" and d.get("origin_verified") is True:
                return True
        return False

    def ai_usage(self, month=None):
        """Registro de consumo de IA. real_cost = lo COMPROMETIDO del mes en ejecuciones REAL (facturado + peor caso de lo incierto/en vuelo)."""
        month = month or time.strftime("%Y-%m", time.gmtime())
        with self.lock:
            rows = self.db.execute("SELECT * FROM ai_budget WHERE month=?", (month,)).fetchall()
        out = {"month": month, "real_cost": 0.0, "settled_cost": 0.0, "uncertain_cost": 0.0, "uncertain_calls": 0, "in_flight": 0, "real_calls": 0, "released_calls": 0, "local_calls": 0, "by_model": {}, "uncertain": []}
        for r in rows:
            if not r["real"]:
                out["local_calls"] += 1; continue
            if r["state"] == "released":
                out["released_calls"] += 1; continue
            c = r["actual"] if r["state"] == "settled" else r["worst"]; out["real_cost"] += c; out["real_calls"] += 1
            if r["state"] == "settled": out["settled_cost"] += c
            elif r["state"] == "uncertain":
                out["uncertain_cost"] += c; out["uncertain_calls"] += 1
                out["uncertain"].append({"id": r["id"], "model": r["model"], "worst_case": r["worst"], "note": r["note"], "created_at": r["created_at"]})
            else: out["in_flight"] += 1
            m = out["by_model"].setdefault(r["model"] or "?", {"calls": 0, "cost": 0.0}); m["calls"] += 1; m["cost"] += c
        for k in ("real_cost", "settled_cost", "uncertain_cost"): out[k] = round(out[k], 8)
        return out

    def list(self, account_id, kind, limit=200, key=None):
        q, a = "SELECT * FROM records WHERE account_id=? AND kind=?", [account_id, kind]
        if key:
            q += " AND key=?"; a.append(key)
        with self.lock:
            rows = self.db.execute(q + " ORDER BY updated_at DESC, rowid DESC LIMIT ?", a + [limit]).fetchall()
        return [self._rec(r) for r in rows]

    @staticmethod
    def _rec(r):
        return {"id": r["id"], "account_id": r["account_id"], "kind": r["kind"], "key": r["key"], "data": json.loads(r["data"]), "created_at": r["created_at"], "updated_at": r["updated_at"], "created_by": r["created_by"]}

    def delete(self, account_id, id_, actor):
        with self.lock:
            n = self.db.execute("DELETE FROM records WHERE id=? AND account_id=?", (id_, account_id)).rowcount; self.db.commit()
        if n:
            self.audit(account_id, actor, "record.delete", {"id": id_})
        return bool(n)

    # ---- auditoría encadenada ------------------------------------------------------------------
    def audit(self, account_id, actor, action, detail):
        with self.lock:
            last = self.db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            prev = last["hash"] if last else "0" * 64
            ts = now()
            body = canon({"ts": ts, "account": account_id, "actor": actor, "action": action, "detail": detail})
            h = hashlib.sha256((prev + body).encode()).hexdigest()
            self.db.execute("INSERT INTO audit(ts,account_id,actor,action,detail,prev_hash,hash) VALUES(?,?,?,?,?,?,?)", (ts, account_id, actor, action, canon(detail), prev, h)); self.db.commit()

    def ai_calls(self, limit=50):
        """Registro MÍNIMO de llamadas de IA (solo estado, duración, tokens, coste estimado, modelo, id de respuesta): lo que se audita en cada llamada."""
        with self.lock:
            rows = self.db.execute("SELECT ts, detail FROM audit WHERE action='ai.call' ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
        return [dict(json.loads(r["detail"]), ts=r["ts"]) for r in rows]

    def audit_list(self, account_id=None, limit=200):
        with self.lock:
            rows = self.db.execute("SELECT * FROM audit WHERE (?1 IS NULL OR account_id=?1) ORDER BY seq DESC LIMIT ?2", (account_id, limit)).fetchall()
        return [{"seq": r["seq"], "ts": r["ts"], "account_id": r["account_id"], "actor": r["actor"], "action": r["action"], "detail": json.loads(r["detail"]), "hash": r["hash"][:16]} for r in rows]

    def verify_audit(self):
        """Recorre toda la cadena. Devuelve (ok, n, primera_seq_rota)."""
        with self.lock:
            rows = self.db.execute("SELECT * FROM audit ORDER BY seq").fetchall()
        prev = "0" * 64
        for r in rows:
            body = canon({"ts": r["ts"], "account": r["account_id"], "actor": r["actor"], "action": r["action"], "detail": json.loads(r["detail"])})
            if r["prev_hash"] != prev or hashlib.sha256((prev + body).encode()).hexdigest() != r["hash"]:
                return False, len(rows), r["seq"]
            prev = r["hash"]
        return True, len(rows), None
