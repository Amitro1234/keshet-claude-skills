# Keshet — Rules ארגוניים לפלטפורמת Vibe Coding
**גרסה 1.0 (טיוטה) | יולי 2026 | Amit Rosen, AI Architecture**

מסמך זה הוא המענה המעשי לפרק "Skills — סטנדרטיזציה ארגונית" במסמך האב: הוא לוקח את רשימת ה-Skills המנדטוריים (הנכפים "דרך Rules") ומגדיר בפועל *מה* ה-Rule, *איך* הוא נאכף, ו*באיזו רמת ביטחון*. מבוסס על ביקורת מלאה של `keshet-claude-skills` v2.1.1 (ראו `keshet-skills-audit-2026-07-01.md`) ועל בדיקה טכנית של מנגנוני האכיפה הקיימים ב-Claude Code (ראו `enforcement/README.md`).

**עקרון מנחה:** Rule שאין לו מנגנון אכיפה הוא בקשה, לא Rule. כל שורה בטבלאות למטה מסומנת ברמת אכיפה — 🔒 Hard (Claude Code עצמו חוסם, לא ניתן לעקיפה על ידי הבניאי), 🔐 Hard-if-managed (חסימה אמיתית, אך רק אם Admin Panel Owner/CISO פרסמו אותו ב-managed settings), ⚠️ Advisory (טקסט הנחיה בלבד — Claude עוקב אחריו, אבל שום דבר לא עוצר אותו אם הוא לא).

---

## 0. שכבות האכיפה — לפני שקוראים את הטבלאות

| שכבה | איפה חי | מי יכול לשנות | ניתן לעקוף? |
|---|---|---|---|
| Instruction-level | CLAUDE.md, קבצי Skill, system prompt | כל מי שיכול לערוך את הקבצים | כן — זו הנחיה, לא אכיפה |
| Project settings | `.claude/settings.json` + `.claude/hooks/` בכל repo של בונה | הבונה, אך שינוי נראה ב-git history | טכנית כן, אבל מבוקר (auditable) |
| Managed settings | (א) קובץ `managed-settings.json` על הדיסק, מופץ ב-IT tooling רגיל (Intune/Group Policy/Jamf) **או** (ב) Server-managed settings דרך admin console של claude.ai | (א) כל אדמין IT, **בכל תוכנית — כולל Team, לא רק Enterprise** (ב) Owner/Admin ב-claude.ai, דורש Team או Enterprise (לא Free/Pro) | **לא** — השכבה היחידה שקלוד קוד עצמו לא מאפשר לבונה לעקוף |

> ✅ **עודכן 2026-07-01, אחרי בדיקה מול תיעוד עדכני:** קיבלתי בטעות רושם ש-managed settings דורש Enterprise. זה **לא נכון**. מנגנון הקובץ (א) הוא convention של קלוד קוד עצמו ועובד בכל תוכנית — אתם לא צריכים לחכות להחלטה Team vs Enterprise (החלטה פתוחה #2) כדי להתחיל לאכוף. גם ה-Server-managed (ב) וגם ה-MCP connector allowlist ל-Cowork/Chat (ראו A3 למטה) עובדים היום על **Team** — לא Enterprise-only כמו שהניח הטיוטה המקורית של מסמך זה.

**מגבלה קריטית:** שכבות ה-hooks וה-settings.json קיימות רק ב-**Claude Code CLI** (מכונות Builder). **ב-Cowork וב-Claude.ai Chat אין hooks ואין settings.json** — האכיפה שם מוגבלת לרמת ה-connector allowlist (ברמת ה-workspace, לא קובץ) ולבידוד ה-VM שקיים כברירת מחדל. כל שאר ה-Rules במסלול Safe Use הם Instruction-level בלבד. זה משנה את כל תמהיל ה-Rules למסלול Safe Use לעומת מסלול Builder — ראו סעיף 4.

---

## 1. Rules ברמת Admin — FinOps וממשל (6 ה-Skills הארגוניים + ניהול פלטפורמה)

בעלי התפקידים הרלוונטיים: **FinOps Owner, Admin Panel Owner, GitHub Admin** (טבלת בעלי תפקידים, מסמך האב §8).

| # | Rule | מקור | מנגנון | רמת אכיפה |
|---|---|---|---|---|
| A1 | ניתוב מודל לפי Tier (Haiku/Sonnet/Opus) לפני כל משימה | `model-router-skill` | הצהרת Tier בטקסט + בחירת מודל ב-UI (Cowork/Chat) או `/model` (CLI) | ⚠️ Advisory — אין hook שנכנס "לפני שקלוד מתחיל לחשוב על משימה" |
| A2 | Spend Caps לפי user/group ($150 Builder, $30 Safe Use, $200 Automation — טבלת `agentic-loop-guard`) | `agentic-loop-guard` + Admin Panel | הגדרה ב-Claude Enterprise Admin Panel (server-side, לא קובץ מקומי) | 🔐 Hard-if-configured — זו לא תלויה ב-repo הזה כלל, תלויה בקונפיגורציה בפאנל עצמו — **לאמת שהמספרים בטבלה תואמים את מה שמוגדר בפועל** |
| A3 | רק connectors מה-allowlist המאושר (`docs/approved-mcp-connectors.md`) | כל 3 ה-skills שמפנים אליו + `enforcement/managed-settings.example.json` | ל-Claude Code: `allowedMcpServers`/`deniedMcpServers` ב-managed settings + hook בדיקה סמנטית. **ל-Cowork/Chat: זמין היום, ברמת Team ומעלה — Organization Settings → Connectors ב-admin console (לא צריך Enterprise ולא צריך לחכות להחלטה #2)** | 🔒 Hard — ואפשר להפעיל את חלק ה-Cowork/Chat **מיד**, עוד לפני שההחלטה הכללית על הפלטפורמה נסגרת |
| A4 | Prompt Caching כסטנדרט לתוכן חוזר מעל 1,024 טוקן (רק API/SDK — לא רלוונטי ל-Cowork/Chat) | `prompt-caching` | קוד JSON בפועל ב-SDK — לא רלוונטי ל-CLI אינטראקטיבי | ⚠️ Advisory לבוני pipelines; אוטומטי ולא רלוונטי בשאר הפלטפורמות |
| A5 | Batch API ל-jobs עם N>10 שיכולים להמתין 24 שעות | `batch-detector` | דומה ל-A4 | ⚠️ Advisory (SDK/pipeline builders בלבד) |
| A6 | תקרת 10 קריאות כלי ברצף לפני checkpoint, 50 קריאות = hard stop, 3 ניסיונות חזרה מקסימום | `agentic-loop-guard` | ⚠️ אין hook ל"ספירת קריאות כלי מצטברת" כרגע — Claude סופר את עצמו | ⚠️ Advisory — מועמד טוב לבדיקה עתידית אם Claude Code יחשוף מונה קריאות ב-hook |

**מה זה אומר בפועל ל-FinOps Owner:** רוב ה-Rules בשכבה הזו הם עדיין Advisory. השליטה האמיתית שקיימת היום היא ברמת ה-Admin Panel (Spend Caps, MCP allowlist) — לא ברמת קובץ. המשמעות: התפקיד הקריטי כאן הוא לא "לכתוב Rule חכם יותר," אלא לוודא שה-Admin Panel בפועל מוגדר לפי המספרים שה-skills מניחים שהם קיימים (A2, A3) — כרגע יש חוסר וידוא בין המספרים הכתובים ב-skill לבין הקונפיגורציה בפועל.

> ✅ **עודכן 2026-07-01, אחרי בדיקה ב-`platform.claude.com/docs/en/api/admin` ובמדריך ה-Spend Limits הרשמי:** ה-**Admin API** הכללי (ניהול users/workspaces/API keys/service accounts/invites) **זמין גם ב-Team**, לא רק Enterprise — אפשר לכתוב היום קוד שמנהל onboarding/offboarding, workspaces ו-API keys, בלי לחכות להחלטה #2. **אבל** ה-**Spend Limits API הספציפי** (הגדרת cap פר-user/פר-group בקוד, ותור אישור בקשות להעלאת cap) **בדוק ומאומת כ-Enterprise-only** — הקריאה עצמה מחזירה שגיאת 400 "this endpoint is not supported for this organization type" אם הארגון לא על Enterprise (ונדרש גם Usage Credits מופעל). ב-Team יש Spend Controls — אבל רק דרך ממשק ה-Console, לא API. זה משנה את A2: התקרות עדיין קיימות ב-Team, אבל **תחזוקה שלהן היום היא ידנית ב-UI, לא ניתנת לאוטומציה עד Enterprise**.

---

## 2. Rules ברמת User/Builder — 11 שערי ה-Builder Flow

בעלי תפקידים רלוונטיים: **Pipeline Maintainer, Security/CISO, כל Builder**.

| # | Rule | מקור | מנגנון | רמת אכיפה |
|---|---|---|---|---|
| B1 | אין קוד לפני אישור Spec Pack (Step 5→6) | `spec-pack` | ⚠️ שום hook לא יכול לבדוק "האם יש Spec Pack מאושר" | ⚠️ Advisory — תלוי משמעת + Champion sign-off אנושי |
| B2 | חסימת קריאה ל-`.env`/קבצי credentials לתוך context | `security` | `permissions.deny` על `Read(.env)` וכו' (managed tier) + hook לתפוס `cat .env`, `grep API_KEY` וכו' | 🔒 Hard |
| B3 | חסימת `git push --force`, `sudo`, `curl \| sh` וכו' | `company-agent-guardrails` (Deny stance) | `permissions.deny` (managed tier) | 🔒 Hard |
| B4 | אישור נדרש (Ask) לפני: `git push` רגיל, deploy, התקנת חבילה, migration | `company-agent-guardrails` (Ask stance) + `deployment` | `permissions.ask` (project tier `.claude/settings.json`) | 🔒 Hard — אך ניתן לעריכה על ידי הבונה עצמו (auditable, לא immutable) |
| B5 | חסימת MCP tool calls שלא ברשימה המאושרת | `security`, `architecture` | hook סמנטי (`pre_tool_use_guard.py`) + managed allowlist | 🔒 Hard |
| B6 | Coverage מינימלי (80% business logic, 100% routes) לפני Step 8 | `unit-test` | ⚠️ אין hook שמריץ `pytest --cov` ובודק סף לפני מעבר Gate — היום זו בדיקה שקלוד "מתבקש" להריץ ולדווח | ⚠️ Advisory — אפשר לשדרג ל-CI/CD gate אמיתי (GitHub Actions) שזה *לא* תלוי בקלוד בכלל |
| B7 | VERDICT: BLOCK/FAIL עוצר את ההתקדמות ל-Gate הבא | כל 11 ה-skills | ⚠️ הפלט הוא טקסט שקלוד כותב — שום דבר לא "נועל" את המעבר בפועל אם המשתמש מתעלם מהפלט | ⚠️ Advisory — ראו המלצה בסעיף 5 |
| B8 | איסור commit של secrets, PII בלוגים, שינוי schema ב-Prod בלי migration ממוספר | `db-structure`, `audit-logging` | חלקית hook (B2-style content scan), חלקית Advisory | 🔒/⚠️ מעורב |

**התובנה המרכזית לשכבה הזו:** ה-Rules שהם באמת Hard (B2, B3, B5) הם כולם Rules "מונעי אסון" — סוד שדולף, פקודה הרסנית, connector לא מאושר. ה-Rules ש"מנהלים תהליך" (B1, B6, B7) — שהם בעצם רוב הערך של ה-Builder Flow — **אין להם היום מנגנון אכיפה טכני בכלל**, הם תלויים בכך שהבונה מריץ את ה-skill ומכבד את ה-VERDICT. זה לא באג בעיצוב — זה מגבלה אמיתית של הפלטפורמה כרגע — אבל חשוב לדעת את זה לפני שמציגים את ה-Builder Flow כ"gate מלא" להנהלה.

**הערה חשובה על B2/B3 בפועל (עודכן 2026-07-01):** ה-hook (`pre_tool_use_guard.py`) במקור בדק רק קריאות דרך כלי ה-`Bash` — כלומר בסשן Windows טהור שרץ דרך כלי `PowerShell` (ולא Git Bash), החסימה בפועל לא הייתה קיימת כלל, למרות שהטבלה סימנה "🔒 Hard". זה תוקן: ה-hook כולל כעת רגקסים מקבילים ל-PowerShell (`Get-Content`, `Remove-Item -Recurse -Force`, `Format-Volume` וכו'), אבל זה תלוי בכך ש-`project-settings.example.json` בפועל כולל את `PowerShell` ב-matcher של ה-`PreToolUse` hook (לא רק `Bash`) — לוודא את זה בכל פריסה חדשה.

---

## 3. Guardrails משותפים (Deny / Ask / Monitor)

מקור: `company-agent-guardrails/SKILL.md`. חלים על **כל** סשן — Admin או Builder, Safe Use או Vibe Coding.

| עמדה | פעולות | מנגנון | רמת אכיפה |
|---|---|---|---|
| 🚫 Deny | דליפת secrets, `curl \| sh`, ביטול sandbox/permissions, פקודות הרס מערכת, גישה ל-credential store | `permissions.deny` + hook תוכן (managed tier) | 🔒 Hard (רק אם פרוס ב-managed) |
| ❓ Ask | git push/force-push, deploy, התקנת חבילה, שינוי schema, כתיבה מחוץ לתיקיית הפרויקט, MCP לא מאושר | `permissions.ask` (project tier) | 🔒 Hard, auditable |
| 👁️ Monitor | כל הרצת shell, כתיבת קבצים בפרויקט, קריאות API חיצוניות | Session transcript + `audit-logging` skill | ⚠️ Advisory — "מוניטור" פה הוא בעצם "מתועד," לא "נחסם" |

---

## 4. מסלול Safe Use — מה שונה

מסלול Safe Use (כלל העובדים, Browser/Enterprise Workspace) **לא רץ על Claude Code CLI** — כל שכבת ה-hooks/settings.json בסעיפים 1-3 לא קיימת שם. עבור האוכלוסייה הזו:

- אין אכיפה טכנית ברמת קובץ — הכל Instruction-level (system prompt ארגוני, אם קיים) או ברמת ה-workspace (אילו connectors מופעלים ל-workspace — הגדרת admin console, לא קובץ ב-repo).
- ה-Deny stance (סעיף 3) חשוב יותר, לא פחות, במסלול הזה — כי אין רשת ביטחון שנייה. שווה לבדוק אם יש דרך להזריק את ה-guardrails כ-system prompt ארגוני קבוע ל-Safe Use workspace (זה תלוי ביכולות ה-Admin Panel, לא נבדק עדיין).
- זה מתקשר ישירות לסעיף הפתוח #6 במסמך האב ("פוליסי ארגוני Safe Use — red lines") — המסמך הזה לא פותר את הפריט הזה, אבל מבהיר *למה* הוא קריטי דווקא כאן: אין שום Rule טכני שיתפוס דבר שה-policy לא מנע במפורש.

---

## 5. המלצות להמשך (לא מומש עדיין — לדיון)

1. **הפוך VERDICT: FAIL ל-Gate אמיתי:** כרגע ה-VERDICT שכל skill מפיק הוא טקסט. שדרוג טבעי: להריץ את הבדיקות הרלוונטיות (coverage, secret-scan, lint) כ-**GitHub Actions check** על ה-PR עצמו — זה נועל את ה-merge ברמת GitHub, בלי תלות בכלל בציות של קלוד להנחיה. זה בעצם מה ש-CI/CD אמור לעשות, ו-Keshet כבר יש לו CI ל-skills library עצמו (`validate-skills.yml`) — הרחבה טבעית היא CI דומה על כל repo של Builder.
2. **סנכרון allowlist:** כרגע רשימת ה-connectors המאושרים כתובה ידנית ב-3 מקומות (`docs/approved-mcp-connectors.md`, `managed-settings.example.json`, `pre_tool_use_guard.py`). לפני production — לבנות סקריפט קטן שמייצר את שתי הרשימות האחרות מה-markdown, כדי שיהיה מקור אמת אחד.
3. **לאמת מול המציאות, לא רק מול המסמך:** טבלת ה-Spend Caps (A2) מוצגת ב-`agentic-loop-guard` כאילו היא "כמו שמוגדר ב-Admin Panel" — לא אומתה מול הפאנל בפועל. שווה לבדוק בפועל לפני שמציגים אותה כ-Rule.
4. **הרצת dry-run לפני managed tier:** `enforcement/README.md` (הקובץ הטכני המצורף) ממליץ להריץ קודם רק project-tier settings.json על מכונת Builder אחת, ולעבור ל-managed רק אחרי שזה עבד בפועל.

---

*מסמך זה טיוטה לדיון — לא אושר עדיין על ידי Security/CISO. לפני הפצה: לעדכן את מסמך האב (סעיף "Skills — סטנדרטיזציה ארגונית") שיפנה לכאן, ולסמן את פריט ההחלטה הפתוח #6 (Safe Use red lines) כתלוי בסעיף 4 כאן.*
