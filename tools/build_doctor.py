#!/usr/bin/env python3
"""Read-only analyzer for Buildozer/python-for-android build logs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RULES_PATH = Path("tools/known_errors.json")
OUTPUT_PATH = Path("doctor-report.md")

def load_rules():
    try:
        data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        return data.get("rules", [])
    except Exception as exc:
        print(f"Could not read rules: {exc}", file=sys.stderr)
        return []

def main():
    log_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build.log")
    if not log_path.exists():
        OUTPUT_PATH.write_text(
            "# Galaxy Build Doctor\n\nلم يتم العثور على build.log، لذلك لا يمكن تشخيص هذا البناء.\n",
            encoding="utf-8",
        )
        return 0

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    rules = load_rules()
    matches = []

    # Prefer specific known failures over generic make/command failures.
    for rule in rules:
        pattern = re.compile(rule["pattern"], re.IGNORECASE)
        for index, line in enumerate(lines):
            if pattern.search(line):
                matches.append((index, rule))
                break

    matches.sort(key=lambda item: item[0])
    output = [
        "# تقرير Galaxy Build Doctor",
        "",
        "> هذه الأداة تقرأ السجل فقط. لا تغيّر ملفات المشروع ولا تطبّق إصلاحات تلقائية.",
        "",
        f"- ملف السجل: `{log_path.as_posix()}`",
        f"- عدد أسطر السجل: {len(lines)}",
        "",
    ]

    if matches:
        index, rule = matches[0]
        output += [
            "## التشخيص الأقرب",
            "",
            f"**التصنيف:** {rule['title']}",
            "",
            f"**الشرح:** {rule['explanation']}",
            "",
            f"**الخطوة المقترحة:** {rule['suggestion']}",
            "",
            f"**موضع المطابقة:** السطر {index + 1}",
            "",
            "### مقتطف من السجل",
            "",
            "```text",
        ]
        start, end = max(0, index - 5), min(len(lines), index + 6)
        output.extend(f"{i + 1}: {lines[i]}" for i in range(start, end))
        output += ["```", ""]
        if len(matches) > 1:
            output += ["### إشارات إضافية", ""]
            for extra_index, extra_rule in matches[1:6]:
                output.append(f"- السطر {extra_index + 1}: {extra_rule['title']}")
            output.append("")
    else:
        output += [
            "## لم يتم التعرف على خطأ معروف",
            "",
            "لم تطابق الأسطر أي قاعدة معروفة. افتح سجل البناء وابحث عن **أول** سطر يحتوي على "
            "`error:`, `Traceback`, `Exception` أو `FAILED`، ثم شاركه لتحليل يدوي.",
            "",
        ]

    output += [
        "## تنبيه",
        "",
        "قد تظهر رسائل مثل `make: ***` أو `Command failed` بعد الخطأ الأصلي؛ غالباً هي نتيجة للفشل وليست السبب الأول. "
        "هذا التقرير مساعدة أولية وليس ضماناً بأن التشخيص نهائي.",
        "",
    ]
    OUTPUT_PATH.write_text("\n".join(output), encoding="utf-8")
    print(f"Doctor report written to {OUTPUT_PATH}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
