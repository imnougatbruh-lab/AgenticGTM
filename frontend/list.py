import re
with open(r'c:\AgenticGTM The Autonomous AI Marketing Engine\backend\frontend\src\app\dashboard\page.tsx', 'r', encoding='utf-8') as f:
    text = f.read()
    print("Menu Items:", re.findall(r'name:\s*"([^"]+)"', text))
    print("Headers:", re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', text))
